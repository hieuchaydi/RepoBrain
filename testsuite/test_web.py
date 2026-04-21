from __future__ import annotations

import io

import pytest

from repobrain.web import (
    RequestTooLargeError,
    _MAX_REQUEST_BODY_BYTES,
    _files_field,
    _read_request_fields,
    _text_field,
)


def test_read_request_fields_rejects_oversized_body() -> None:
    oversized = _MAX_REQUEST_BODY_BYTES + 1
    environ = {
        "CONTENT_LENGTH": str(oversized),
        "CONTENT_TYPE": "application/json",
        "wsgi.input": io.BytesIO(b"x" * oversized),
    }
    with pytest.raises(RequestTooLargeError):
        _read_request_fields(environ)


def test_read_request_fields_accepts_small_json_body() -> None:
    body = b'{"query":"hello"}'
    environ = {
        "CONTENT_LENGTH": str(len(body)),
        "CONTENT_TYPE": "application/json",
        "wsgi.input": io.BytesIO(body),
    }
    assert _read_request_fields(environ) == {"query": "hello"}


def test_text_field_treats_json_null_as_empty_default() -> None:
    body = b'{"base":null,"files":["src/api/auth.py"]}'
    environ = {
        "CONTENT_LENGTH": str(len(body)),
        "CONTENT_TYPE": "application/json",
        "wsgi.input": io.BytesIO(body),
    }
    fields = _read_request_fields(environ)
    base = _text_field(fields, "base") or None
    files = _files_field(fields, "files")

    assert base is None
    assert files == ["src/api/auth.py"]
