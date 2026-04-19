from __future__ import annotations

import json
from heapq import nlargest
import sqlite3
from pathlib import Path

from repobrain.config import RepoBrainConfig
from repobrain.models import Chunk, Edge, ParsedDocument, SearchHit
from repobrain.engine.providers import EmbeddingProvider, cosine_similarity, tokenize


class MetadataStore:
    def __init__(self, config: RepoBrainConfig) -> None:
        self.config = config
        self.db_path = config.metadata_db_path
        self.vector_path = config.vectors_dir / "chunks.jsonl"
        self._vector_cache_signature: tuple[int, int] | None = None
        self._vector_cache: list[tuple[int, list[float]]] | None = None

    def initialize(self, reset: bool = False) -> None:
        self.config.state_path.mkdir(parents=True, exist_ok=True)
        self.config.vectors_dir.mkdir(parents=True, exist_ok=True)
        self.config.cache_dir.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            if reset:
                connection.executescript(
                    """
                    DROP TABLE IF EXISTS chunk_fts;
                    DROP TABLE IF EXISTS edges;
                    DROP TABLE IF EXISTS chunks;
                    DROP TABLE IF EXISTS symbols;
                    DROP TABLE IF EXISTS files;
                    """
                )
            connection.executescript(
                """
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS files (
                    path TEXT PRIMARY KEY,
                    language TEXT NOT NULL,
                    role TEXT NOT NULL,
                    sha256 TEXT DEFAULT '',
                    size INTEGER DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS symbols (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    name TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    start_line INTEGER NOT NULL,
                    end_line INTEGER NOT NULL,
                    signature TEXT NOT NULL,
                    doc_hint TEXT DEFAULT ''
                );
                CREATE TABLE IF NOT EXISTS chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    language TEXT NOT NULL,
                    role TEXT NOT NULL,
                    symbol_name TEXT,
                    symbol_kind TEXT,
                    start_line INTEGER NOT NULL,
                    end_line INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    search_text TEXT NOT NULL,
                    neighborhood_json TEXT NOT NULL,
                    hints_json TEXT NOT NULL
                );
                CREATE VIRTUAL TABLE IF NOT EXISTS chunk_fts USING fts5(content, search_text);
                CREATE TABLE IF NOT EXISTS edges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_file TEXT NOT NULL,
                    source_symbol TEXT NOT NULL,
                    target TEXT NOT NULL,
                    edge_type TEXT NOT NULL,
                    target_file TEXT
                );
                """
            )
            connection.commit()
        if reset and self.vector_path.exists():
            self.vector_path.unlink()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def replace_documents(self, documents: list[ParsedDocument], embedder: EmbeddingProvider) -> dict[str, int]:
        self.initialize(reset=True)
        chunk_texts: list[str] = []
        chunk_ids: list[int] = []
        with self.connect() as connection:
            connection.execute("PRAGMA synchronous=NORMAL")
            connection.execute("PRAGMA temp_store=MEMORY")
            for document in documents:
                connection.execute(
                    "INSERT OR REPLACE INTO files(path, language, role, size) VALUES (?, ?, ?, ?)",
                    (document.file_path, document.language, document.role, len(document.content)),
                )
                connection.executemany(
                    """
                    INSERT INTO symbols(file_path, name, kind, start_line, end_line, signature, doc_hint)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        (
                            document.file_path,
                            symbol.name,
                            symbol.kind,
                            symbol.start_line,
                            symbol.end_line,
                            symbol.signature,
                            symbol.doc_hint,
                        )
                        for symbol in document.symbols
                    ),
                )
                connection.executemany(
                    """
                    INSERT INTO edges(source_file, source_symbol, target, edge_type, target_file)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        (edge.source_file, edge.source_symbol, edge.target, edge.edge_type, edge.target_file)
                        for edge in document.edges
                    ),
                )
                for chunk in document.chunks:
                    cursor = connection.execute(
                        """
                        INSERT INTO chunks(
                            file_path, language, role, symbol_name, symbol_kind, start_line, end_line,
                            content, search_text, neighborhood_json, hints_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            chunk.file_path,
                            chunk.language,
                            chunk.role,
                            chunk.symbol_name,
                            chunk.symbol_kind,
                            chunk.start_line,
                            chunk.end_line,
                            chunk.content,
                            chunk.search_text,
                            json.dumps(chunk.neighborhood),
                            json.dumps(chunk.hints),
                        ),
                    )
                    chunk_id = int(cursor.lastrowid)
                    connection.execute(
                        "INSERT INTO chunk_fts(rowid, content, search_text) VALUES (?, ?, ?)",
                        (chunk_id, chunk.content, chunk.search_text),
                    )
                    chunk_ids.append(chunk_id)
                    chunk_texts.append(chunk.search_text)
            connection.commit()

        vectors = embedder.embed(chunk_texts)
        with self.vector_path.open("w", encoding="utf-8") as handle:
            for chunk_id, vector in zip(chunk_ids, vectors):
                handle.write(json.dumps({"chunk_id": chunk_id, "vector": vector}) + "\n")
        self._vector_cache_signature = None
        self._vector_cache = None

        return {
            "files": len(documents),
            "chunks": len(chunk_ids),
            "symbols": sum(len(item.symbols) for item in documents),
            "edges": sum(len(item.edges) for item in documents),
        }

    def search_fts(self, query: str, limit: int = 8) -> list[SearchHit]:
        terms = tokenize(query)
        if not terms:
            return []
        match_query = " OR ".join(sorted(set(terms)))
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT c.*, bm25(chunk_fts) AS rank
                FROM chunk_fts
                JOIN chunks c ON c.id = chunk_fts.rowid
                WHERE chunk_fts MATCH ?
                ORDER BY rank
                LIMIT ?
                """,
                (match_query, limit),
            ).fetchall()
        hits: list[SearchHit] = []
        for position, row in enumerate(rows, start=1):
            score = 1 / position
            hits.append(
                SearchHit(
                    chunk_id=row["id"],
                    file_path=row["file_path"],
                    language=row["language"],
                    role=row["role"],
                    symbol_name=row["symbol_name"],
                    start_line=row["start_line"],
                    end_line=row["end_line"],
                    content=row["content"],
                    score=score,
                    reasons=["bm25", "fts"],
                )
            )
        return hits

    def search_vectors(self, query: str, embedder: EmbeddingProvider, limit: int = 8) -> list[SearchHit]:
        if not self.vector_path.exists():
            return []
        query_vector = embedder.embed([query])[0]
        vectors = self._load_vectors()
        scored = (
            (chunk_id, cosine_similarity(query_vector, vector))
            for chunk_id, vector in vectors
        )
        top_scored = [item for item in nlargest(limit, scored, key=lambda item: item[1]) if item[1] > 0]
        top_ids = [chunk_id for chunk_id, _ in top_scored]
        if not top_ids:
            return []
        rows = self.get_chunks(top_ids)
        score_map = dict(top_scored)
        hits: list[SearchHit] = []
        for row in rows:
            hits.append(
                SearchHit(
                    chunk_id=row["id"],
                    file_path=row["file_path"],
                    language=row["language"],
                    role=row["role"],
                    symbol_name=row["symbol_name"],
                    start_line=row["start_line"],
                    end_line=row["end_line"],
                    content=row["content"],
                    score=score_map.get(row["id"], 0.0),
                    reasons=["vector"],
                )
            )
        return hits

    def _load_vectors(self) -> list[tuple[int, list[float]]]:
        try:
            stat = self.vector_path.stat()
        except OSError:
            return []
        signature = (stat.st_mtime_ns, stat.st_size)
        if self._vector_cache_signature == signature and self._vector_cache is not None:
            return self._vector_cache

        vectors: list[tuple[int, list[float]]] = []
        with self.vector_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                payload = json.loads(line)
                vectors.append((int(payload["chunk_id"]), [float(item) for item in payload["vector"]]))
        self._vector_cache_signature = signature
        self._vector_cache = vectors
        return vectors

    def get_chunks(self, chunk_ids: list[int]) -> list[sqlite3.Row]:
        if not chunk_ids:
            return []
        placeholders = ", ".join("?" for _ in chunk_ids)
        with self.connect() as connection:
            rows = connection.execute(
                f"SELECT * FROM chunks WHERE id IN ({placeholders})",
                tuple(chunk_ids),
            ).fetchall()
        row_map = {row["id"]: row for row in rows}
        return [row_map[chunk_id] for chunk_id in chunk_ids if chunk_id in row_map]

    def get_edges_for_files(self, file_paths: list[str], limit: int = 12) -> list[dict[str, str | None]]:
        if not file_paths:
            return []
        placeholders = ", ".join("?" for _ in file_paths)
        with self.connect() as connection:
            rows = connection.execute(
                f"""
                SELECT source_file, source_symbol, target, edge_type, target_file
                FROM edges
                WHERE source_file IN ({placeholders})
                ORDER BY id
                LIMIT ?
                """,
                (*file_paths, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_related_edges(
        self,
        file_paths: list[str],
        *,
        targets: list[str] | None = None,
        limit: int = 24,
    ) -> list[dict[str, str | None]]:
        normalized_paths = [str(item).strip() for item in file_paths if str(item).strip()]
        normalized_targets = [str(item).strip() for item in (targets or []) if str(item).strip()]
        if not normalized_paths and not normalized_targets:
            return []

        where_parts: list[str] = []
        params: list[object] = []
        if normalized_paths:
            file_placeholders = ", ".join("?" for _ in normalized_paths)
            where_parts.append(f"(source_file IN ({file_placeholders}) OR target_file IN ({file_placeholders}))")
            params.extend(normalized_paths)
            params.extend(normalized_paths)
        if normalized_targets:
            target_placeholders = ", ".join("?" for _ in normalized_targets)
            where_parts.append(f"target IN ({target_placeholders})")
            params.extend(normalized_targets)

        query = (
            "SELECT source_file, source_symbol, target, edge_type, target_file "
            f"FROM edges WHERE {' OR '.join(where_parts)} ORDER BY id LIMIT ?"
        )
        params.append(limit)
        with self.connect() as connection:
            rows = connection.execute(query, tuple(params)).fetchall()
        return [dict(row) for row in rows]

    def get_file_records(self, file_paths: list[str]) -> list[sqlite3.Row]:
        if not file_paths:
            return []
        placeholders = ", ".join("?" for _ in file_paths)
        with self.connect() as connection:
            rows = connection.execute(
                f"SELECT path, language, role FROM files WHERE path IN ({placeholders})",
                tuple(file_paths),
            ).fetchall()
        return rows

    def stats(self) -> dict[str, int]:
        with self.connect() as connection:
            files = connection.execute("SELECT COUNT(*) FROM files").fetchone()[0]
            chunks = connection.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
            symbols = connection.execute("SELECT COUNT(*) FROM symbols").fetchone()[0]
            edges = connection.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
        return {"files": files, "chunks": chunks, "symbols": symbols, "edges": edges}

    def indexed(self) -> bool:
        if not self.db_path.exists():
            return False
        required_tables = {"files", "symbols", "chunks", "chunk_fts", "edges"}
        try:
            with self.connect() as connection:
                rows = connection.execute(
                    "SELECT name FROM sqlite_master WHERE type IN ('table', 'virtual table')"
                ).fetchall()
                available = {row["name"] for row in rows}
                if not required_tables.issubset(available):
                    return False
                file_count = connection.execute("SELECT COUNT(*) FROM files").fetchone()[0]
                chunk_count = connection.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
                return file_count > 0 and chunk_count > 0
        except sqlite3.Error:
            return False
