# Project Plan - Bien ban ra soat va plan moi

Ngay cap nhat: 2026-04-19

Ghi chu:
- Pham vi tai lieu nay chi nam trong project hien tai.
- Codebase duoc danh gia trong workspace hien tai la `RepoBrain` (`pyproject.toml` dang de version `0.5.0`).
- Tai lieu nay duoc viet theo kieu hop ky thuat: ket luan trang thai, phan no viec chua xong, quyet dinh, va ke hoach thuc thi moi.

## 1. Muc tieu buoi hop

- Ra soat lai `docs/implementation-plan.md` va `docs/backlog.md`.
- Xac dinh phan nao da lam xong, phan nao chi moi co khung, phan nao van la no ky thuat.
- Chot mot plan moi de tiep tuc lam, tap trung vao nhung viec thuc su chua xong.

## 2. Snapshot hien tai

- Nen tang chinh da co: CLI, browser UI, local report, MCP adapter, workspace memory, baseline, ship gate, provider smoke.
- Hang retrieval va harness da co query, trace, impact, targets, warning, confidence, contradiction check, benchmark fixture.
- Parser layer da co optional `tree_sitter` adapter va heuristic fallback.
- CI da build frontend, cai `.[dev,tree-sitter]`, compile package, va chay `python -m pytest -q`.
- Kiem tra nhanh trong workspace ngay 2026-04-19:
  `python -m pytest -q tests/test_engine.py tests/test_cli.py tests/test_web.py tests/test_workspace.py`
  -> `40 passed in 4.14s`

## 3. Danh gia plan cu theo kieu cuoc hop

| Hang muc cu | Trang thai | Bang chung hien co | Ket luan |
| --- | --- | --- | --- |
| Epic 1 - Indexing Quality | Lam duoc mot phan | `src/repobrain/engine/scanner.py` da co `TreeSitterParserAdapter`, role detection, hint extraction, parser capability reporting | Khong con la blocker kien truc, nhung do sau parser va role detection van chua du manh |
| Epic 2 - Retrieval Quality | Lam duoc mot phan | `src/repobrain/engine/core.py` da co rewrite query, weighted fusion kieu RRF, rerank bonus, multi-source warning, test penalty | Da tot hon MVP, nhung van la heuristic; chua phai retrieval fusion co benchmark-backed tuning |
| Epic 3 - Harness Reliability | Lam duoc nhieu nhung chua chot | Da co `build_change_context`, low-confidence warning, contradiction warning, benchmark, ship gate, confidence tests | Huong di dung, nhung confidence band van rong va `build_change_context` chua du "agent-facing" |
| Epic 4 - Provider Layer | Gan nhu xong cho muc alpha | Da co `doctor`, `provider-smoke`, docs cai dat, release workflow, missing-SDK reporting | Viec con lai la live-key validation that outside CI, khong phai thieu feature trong code |
| Epic 5 - OSS Polish | Gan nhu xong cho muc alpha | README, docs, launchers, release-check, report, webapp, CI/release workflows da co | Van can khoa lai bang bang chung release va doc alignment cuoi cung |

## 4. Ket luan cuoc hop

- Plan cu khong bi that bai. Thuc te, repo da di xa hon muc "MVP" o nhieu mat.
- Phan chua xong hien nay khong nam o cho thieu command hay thieu giao dien, ma nam o chat luong tin cay cua retrieval va muc do chac chan cua ket qua.
- Nghia la trong sprint tiep theo, khong nen mo rong them surface lon. Uu tien phai chuyen tu "them feature" sang "lam cho ket qua dang tin hon va de release hon".

## 5. Viec cu chua xong va ly do

1. Confidence calibration moi dung o muc heuristic.
   Trong `tests/test_engine.py` da co `test_confidence_calibration_bands`, nhung band van rong va chua neo vao muc nghia ro rang cho downstream agent.

2. Retrieval fusion van la weighted merging + RRF heuristic.
   `_merge_hit()` trong `src/repobrain/engine/core.py` da tot hon merge don gian, nhung backlog cu ghi ro "beyond simple weighted merging", va muc nay hien chua dat.

3. Tree-sitter da co adapter va CI da cai extra, nhung chua co integration test that voi parser that.
   `tests/test_scanner.py` moi xac nhan contract parser adapter bang stub, chua xac nhan chat luong symbol va range khi dung grammar that.

4. `build_change_context` da compact nhung chua du chat cho coding agent.
   Payload hien co top files, edit targets, warning, confidence, plan steps; van thieu tom tat evidence ngan, ly do loai tru, va cach noi ro muc rui ro khi confidence yeu.

5. Release validation van con mot doan manual.
   Live-key provider smoke, README example lock, demo artifact, va mot vong release evidence van la cac cong viec can dong lai truoc khi goi la "production-credible".

## 6. Quyet dinh sau hop

1. Khong them feature moi co be mat lon trong sprint tiep theo.
2. Uu tien P0 la trust layer: confidence, warning, change-context.
3. Parser quality va retrieval fusion la P1 ngay sau trust layer.
4. Provider live-smoke va release evidence la gate truoc release, khong can chen len truoc trust tightening.

## 7. Plan moi de lam

### Phase 1 - Trust Tightening

Muc tieu:
- Bien confidence thanh tin hieu de tin duoc, khong chi la mot con so heuristic.
- Lam `build_change_context` gon hon, ro hon, an toan hon cho downstream coding agent.

Cong viec:
- Chuan hoa confidence bands thanh cac muc co nghia ro rang, vi du: `exploratory`, `weak`, `moderate`, `strong`.
- Sua `_confidence()` va `_warnings()` de warning an khop voi tung band thay vi chi dua vao nguong roi rac.
- Nang `build_change_context()` de tra ve:
  - top files co bang chung ro nhat
  - edit targets da duoc support boi evidence
  - summary ngan cho ly do de xuat
  - risk note khi confidence thap hoac evidence lech
- Bo sung test cho:
  - grounded query
  - contradictory query
  - low-evidence query
  - test-only evidence query
  - change-context payload shape

Tieu chi xong:
- Confidence khong con nhay "dep" nhung mo ho.
- Warning va confidence thong nhat voi nhau.
- `build_change_context` khong dua ra goi y sua file ma khong co evidence ro.

### Phase 2 - Parser + Retrieval Quality

Muc tieu:
- Giam tinh heuristic trong indexing va ranking.

Cong viec:
- Bo sung integration test cho tree-sitter that khi grammar co san trong CI.
- Mo rong role detection cho route, callback, config, worker theo mau thuc te hon.
- Refactor retrieval fusion thanh scoring co cau truc ro hon:
  - lexical score
  - vector score
  - rerank score
  - role va path bonus
  - concentration penalty
- Them benchmark case de bat cac tinh huong:
  - route -> service -> config
  - callback -> oauth service
  - job -> queue -> handler

Tieu chi xong:
- Top file accuracy tren fixture on dinh hon.
- Trace query co role diversity tot hon.
- Parser path optional tao ra symbol range va chunk boundary tot hon heuristic mot cach do duoc.

### Phase 3 - Release Hardening

Muc tieu:
- Dong lai nhung viec can co de release nay de tin hon va de demo hon.

Cong viec:
- Khoa README examples theo output thuc te cua fixture.
- Chay full test suite + build + `release-check`.
- Chot mot tai lieu release evidence ngan cho:
  - local smoke
  - CI green
  - artifact inspection
  - provider live-key smoke it nhat 1 nha cung cap
- Them mot demo asset ngan de README va demo script khop nhau.

Tieu chi xong:
- Release checklist co the tick lai bang bang chung that.
- Khong con khoang trong lon giua docs, workflow, va hanh vi thuc te.

## 8. Thu tu uu tien thuc thi

1. Phase 1 - Trust Tightening
2. Phase 2 - Parser + Retrieval Quality
3. Phase 3 - Release Hardening

## 9. Nhung viec tam thoi khong dua vao sprint nay

- Cross-repo federation that su
- Hosted dashboard
- Browser research MCP
- Visual token unification giua moi surface UI
- Autonomous repo mutation

## 10. Action items de bat dau ngay

1. Sua `src/repobrain/engine/core.py` cho confidence band va change-context.
2. Mo rong `tests/test_engine.py` de khoa hanh vi trust layer.
3. Bo sung test parser that trong `tests/test_scanner.py`.
4. Cap nhat `docs/backlog.md` va hoac `docs/implementation-plan.md` sau khi sprint moi bat dau de tai lieu goc khong lech voi trang thai moi.

## 11. Bottom line

Huong di cu van dung, nhung trong ngay 2026-04-19 diem nghen khong con la "thieu tinh nang". Diem nghen la "do tin cay cua ket qua va bang chung release". Vi vay, plan moi se uu tien lam chat trust layer truoc, roi moi nang parser va retrieval, va cuoi cung khoa release evidence.
