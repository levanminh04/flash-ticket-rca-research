# Final continuation status — 28/09/2026

Phases1–7 COMPLETE trong gói scopeddevelopment U27R. Verdict PASS WITH LIMITATIONS, xem development-preflight-report.md và development-preflight-adjudication.json. Full30/C1/C5/mandatorysensitivities/integrated/RCD270 và ba review đã đóng. Không human-approve method/freeze hoặc mở F–I. Các TODO bên dưới giữ checkpoint lịch sử; không dùng để chạy lại work đã hoàn tất.

# D/E continuation — impact map, TODO và cổng thực thi

Ngày 27/09/2026, owner Minh. EXECUTE / FORMATION. U27R mission SHA256 `0109696102a7945375433833b3c6051d593714139b9e9627c8ce2cb3950c8adb` trực tiếp phê duyệt impact map hợp lý trong D/E, kể cả hơn3file, amendment và tự động resume sau review/fixtures đạt. Không xin lại cùng phạm vi. Exact policy do agent chọn vẫn CANDIDATE dùng trong development được ủy quyền, không USER_CONFIRMED hoặc formal final freeze.

## 1. TODO/phase plan

1. DONE — xác minh P/W heads/dirty state và73entries của inventory trước; giữ unrelated README; tạo byte snapshot TD-v1.2 và prechange inventory, không chạy lại34fixtures chưa bị ảnh hưởng.
2. DONE — ba reviewer độc lập semantics/statistics/adversarial, ít nhất hai lựa chọn mỗi finding, không xem outcome để chọn; coordinator phân xử theo evidence, không bỏ phiếu.
3. DONE — rationale lựa chọn + sửa canonical TD thành TD-v1.3, changelog/provenance; bổ sung exact membership/conflict fixtures; fresh targeted review; chỉ resume khi không còn critical/major ambiguity.
4. IN PROGRESS — complete C5 forecasting/calibration/events/TV/composition; worker/cache/firewall; real pinned RCD isolated runtime; source/license checks. Mỗi executable run có contract trước và run ID mới.
5. IN PROGRESS — đúng89allowlisted development telemetry objects (reuse5verified, acquire84missing), full actual-use audit30 và reference-graph/R topology diagnostics trước outcome. Giữ failures trong denominator.
6. PENDING — predetermined smokeIDs nguyên registry TD12; nếu đạt thì đủ development30 C1/C5 registry và mandatory OFAT sensitivity, comparator results, resource/failure attribution. Không chọn primary vì graph phải thắng.
7. PENDING — ba hướng final scientific review độc lập nếu capacity cho phép; reconcile; canonical handoff/state/map, exact changed-file/hash inventory, governance audit, final16questions và verdict có evidence.

## 2. Impact map được U27R cho phép

| Root | Files/families | Thay đổi và lý do |
|---|---|---|
| P | `docs/evidence/project-direction/2026-09-27-rca-c5-amendment-and-e-resume.md` | Tạo nguồn verbatim quyền mới |
| P | `docs/research-rca/RESEARCH-DECISIONS.md`; `docs/project/decision-register.md` | Append quyền nguyên tử và đăng ký, không rewrite history |
| P | `docs/research-rca/task-d-method-and-experiment-specification.md` | Canonical amendment trước code/derived; chỉ C5 và clause phụ thuộc trực tiếp |
| P | `docs/research-rca/{task-d-handoff,task-e-handoff,CURRENT-STATE,ARTIFACT-MAP}.md` | Current routing/results sau source/evidence; bảo tồn checkpoint cũ |
| W | `task-d/td-v1.2-before-c5-amendment.md`; `td-v1.3-prechange-inventory.json`; `td-v1.3-c5-clarification-rationale.md`; `td-v1.3-c5-reviews.json` | Snapshot byte gốc, alternatives, reviewer identities/disagreements, amendment rationale và validation |
| W | `scripts/task_e/{contract,acquire,loader,ranking,evaluator,comparators}.py`; new `detection.py`, `run_preflight.py` và bounded worker/cache/calibration/qualification helpers trong cùng folder | Hoàn tất E code trong amended spec, không mở Task F product pipeline |
| W | `tests/task_e/` | Membership/conflict/C5/event/aggregation/cache/firewall/fidelity fixtures; expected from spec trước run |
| W | `configs/task-e-td13-development.json`; `environments/task-e/`; exact new locks under `environments/` | Registry version mới giữ split/smoke/C1choices; isolated comparator env không nâng .venv cũ |
| W | `baselines/upstream/`; source manifests/new patches khi cần fidelity-qualified engineering correction | Pinned necessary source/license only; không sửa original snapshots |
| W | `datasets/rcaeval/task-e-development/<authorized-case>/` | Chỉ telemetry còn thiếu trong allowlist; original samples read-only |
| W | `results/task-e/e27-007-*` và các unique IDs tiếp theo; `results/task-e/continuation-*` | Pre-run contracts/source/data/config/env snapshots, all outputs/failures/resources/reviews/sensitivity/final evidence |
| W | `.gitignore` khi cần | Raw mới/env/cache/large intermediates không đưa Git; không untrack lịch sử |

Không sửa B CLOSED/raw history, Primary RQ, split/smoke rule, final60, FlashTicket app/API/schema/Saga, legacy repo hoặc F/G/H/I. Không commit/push. Giữ toàn bộ e27-001…006 byte-for-byte; new run không ghi đè old failure. C1 numerical method/registry không mở lại nếu không có evidence bắt buộc.

## 3. Gate và checkpoint

U27R §12 cho phép resume tự động khi targeted review không còn CRITICAL/MAJOR ambiguity, fixtures đạt, D deterministic và không cần quyết định vượt scope. Kết quả xấu tự thân không chặn; áp failure-attribution/gates của D. Genuine invalid/essential-assumption/control/coverage issue được bảo tồn và phân xử, không sáng tạo feature để cứu score. Final PASS chỉ khi các remaining stages/sensitivity/review thật sự hoàn tất.

Trước mỗi run: immutable ID, current TD/source hashes, source snapshots, exact actual inputs/allowlist, env/command/seeds/config/output schema/exposure. Dataset schema/identity audit khác model admission theo cutoff. Model receives sanitized numeric arrays only; controller/evaluator sở hữu names/paths/root/τ. API/process isolation không phải OS hostile-code sandbox.

## Resume checkpoint

Fresh review found2major/1minor implementation defects, fixed and independently rechecked. Current C5 fixtures24+34+16PASS. AUTO RESUME scoped E recorded in continuation-resume-receipt.json. Worker/runtime/data/empirical gates still pending. Usage-limit-interrupted agents resumed; their failed turns were never counted as completed review.
