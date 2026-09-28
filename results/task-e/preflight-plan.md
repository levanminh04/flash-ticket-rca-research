# Task E development preflight — phạm vi và impact map

Ngày: 2026-09-27. Owner: Minh. Trạng thái: **impact map §4–5 đã được Minh duyệt; execution checkpoint RETURN TO TASK D**. Kế hoạch dưới đây giữ phạm vi đã duyệt; kết quả thực hiện ở [adjudication](e27-001-synthetic/adjudication.md). Bounded checks đã chạy, chưa actual30 campaign hoặc method approval.

## 1. Quyền đã có và giới hạn

Minh đã cho phép chuẩn bị/chạy development giới hạn theo TD-v1.2, được thực hiện trước khi đủ năm agent độc lập; yêu cầu phản biện vẫn giữ cho đánh giá chính thức. Không chạy tập đánh giá cuối hoặc đổi phạm vi đồ án. Mission đính kèm yêu cầu falsification-first: nếu fixtures, loader và smoke đạt thì chạy toàn bộ development đã đăng ký; dừng và quay D nếu gặp vấn đề protocol thực chất. Không tự mở F/G/H/I hoặc commit/push.

Nguồn mission: `C:/Users/84583/.codex/attachments/5a3353fc-c539-416a-99dd-733528b8b97c/Pasted text.txt`; SHA256 `7d2fbf1660d8edc81d0145b918c9c84352ee0a88fccb0ce6f2b7d7c529b9e627`.

P = `D:/Project/flash-ticket-platform`, branch `codex/rca-research-program`, HEAD `3d7ec9d824d12c98dc233705ef50908b62adf235`.
W = `D:/Project/flash-ticket-rca-research`, branch `main`, HEAD `f49859df7664758f1143a1033535da7f6f29d7d6`.
TD-v1.2 bytes SHA256 `985f1c5fc983422272dfbde8b69ed5ff98ee4fdd1631af075d03788c3770ad54`.
P/README.md có thay đổi trước task; SHA256 `3646cb1b6e8da832e8b9513fd8318d749f7f5f6788b5d3223eda7f5a9a662274`; giữ nguyên.

Quyền chạy development không đổi mọi công thức CANDIDATE thành DECIDED/APPROVED và không chứng nhận đủ reviewer. Ghi nguồn/quyết định/state trước first run. Các câu NOT AUTHORIZED trong snapshot D ngày26/09 được supersede đúng phạm vi bằng quyết định mới, không sửa lịch sử receipt.

## 2. Dữ liệu được phép

RE2-TT revision `afeacb11bcc94dadfd1c8f483ee4377b2b8b614e`, đúng30 development cases: mỗi cell dưới có repeats1/2/3.

| Root service | Faults |
|---|---|
| ts-auth-service | cpu, delay |
| ts-order-service | disk, loss |
| ts-route-service | mem, socket |
| ts-train-service | cpu, delay |
| ts-travel-service | disk, loss |

Case ID = `re2tt_<root>_<fault>_<repeat>`, kiểm tồn tại bằng metadata đã pin. Không quét raw ngoài allowlist. Trusted controller giữ metadata/labels/paths/time; numeric workers nhận arrays/masks/case-local indices/adjacency/config. C1 slicing giữ oracle boundary đúng task; C5 runtime không nhận injection time. Prior E1 exposure được khai, không gọi test là untouched.

Smoke rule dự kiến: một case có opaque handle nhỏ nhất lexical trong mỗi development cell, trước mọi outcome; mười cases. Rule vận hành này không đổi split hoặc chọn theo score. Chỉ nếu smoke và các gate đạt mới chạy đủ30; failure giữ trong denominator. Không tải RE3/OB/SS/LEMMA hay60 final cases.

## 3. Trình tự và điều kiện dừng

1. Wave1 read-only: actual data/source inventory; mathematics/evaluator; leakage; comparator fidelity. Coordinator kiểm bằng chứng và phân loại finding. Scientific adversary đọc findings sau đó; khai số agent thật, không giả năm identities.
2. Source-first authorization/state; snapshot TD/P/W/data/code/environment, registry và exact run contract trước chạy.
3. Synthetic fixtures/adversarial tests: local, PPR/value diffusion/R, evaluator, C5/threshold/events. Component fail thì không chạy downstream component đó.
4. Actual-use audit toàn bộ30 development cases trước model run; missing/conflicting inputs giữ nguyên và báo rõ. Chỉ lấy các file development còn thiếu, kiểm hash/size; không sửa raw.
5. Smoke theo rule ở§2: finite scores, shapes, immutable inputs, graph participation, firewall canaries, runtime/memory.
6. Full authorized development: registry C1 local8/PPR6/diffusion3, L/O/R256; C5 G/L/ALL, MT/MTL, lambda/q; mandatory OFAT sensitivities, baseline adapters, per-case intermediates/failures. Không dùng smoke để chọn winner; không chạy Cartesian search hoặc đổi primary để cứu score.
7. Review outputs/code/failures/sensitivity; adjudication với evidence; canonical handoff sau khi có artifacts. PASS không nghĩa graph thắng và không mở stage tiếp theo.

D-spec ambiguity, fidelity không đạt, leakage, controls không informative, coverage/calibration gates fail hoặc cần feature ngoài registry: dừng nhánh bị ảnh hưởng/theo stop rule mission; báo RETURN TO TASK D. Implementation bug được sửa với receipts giữ nguyên; không sửa expected output trái contract. Không gọi phần chưa chạy là PASS hoặc valid-negative.

## 4. Impact map — file nguồn cụ thể dự kiến

### P — quyền nguồn và bàn giao; không sửa công thức TD

| File tương đối P | Thao tác | Mục đích |
|---|---|---|
| docs/evidence/project-direction/2026-09-27-rca-development-preflight.md | Tạo | Lưu nguyên văn mission và xác nhận phạm vi mới, kèm hash |
| docs/research-rca/RESEARCH-DECISIONS.md | Append | Ghi xác nhận nguyên tử của Minh, defer assurance đúng phạm vi, không approve algorithm |
| docs/project/decision-register.md | Append link | Đăng ký nguồn quyết định RCA mới, không nhân bản quyết định |
| docs/research-rca/CURRENT-STATE.md | Sửa | Phản ánh scoped authorization và checkpoint thực tế |
| docs/research-rca/ARTIFACT-MAP.md | Bổ sung | Dẫn đúng evidence/code/run/handoff E |
| docs/research-rca/task-e-handoff.md | Tạo khi có evidence | Kết luận preflight, limitations, exact next authorized step |

### W — mã preflight và kiểm chứng riêng cho E

| File tương đối W | Thao tác | Mục đích |
|---|---|---|
| results/task-e/preflight-plan.md | Tạo/cập nhật | Kế hoạch và impact map đang trình |
| scripts/task_e/contract.py | Tạo | Config schemas, source hashes, IDs, immutable registry, run preconditions |
| scripts/task_e/acquire.py | Tạo | Exact allowlist downloader/source pinning, không full-corpus |
| scripts/task_e/loader.py | Tạo | Trusted loader, windows/prefix/maps/masks và audit |
| scripts/task_e/ranking.py | Tạo | Pure numeric local/PPR/diffusion/structural controls |
| scripts/task_e/detection.py | Tạo | Pure numeric C5 G/L/ALL/TV/residual/event logic |
| scripts/task_e/evaluator.py | Tạo | Label-side ties/misses/failures/denominators/selection/statistics |
| scripts/task_e/comparators.py | Tạo | BARO/RCD declared adapters, explicit fidelity/failures |
| scripts/task_e/run_preflight.py | Tạo | Stage orchestrator, independent model/evaluator processes, manifests và diagnostics |
| tests/task_e/test_math.py | Tạo | Independent expected values + adversarial fixtures |
| tests/task_e/test_firewall.py | Tạo | Path/label/time/future/index/cache invariance và input isolation |
| configs/task-e-td12-development.json | Tạo | Registry/folds/selection/sensitivity/exact development allowlist/smoke rule |
| environments/task-e-requirements.lock.txt | Tạo | Exact runtime/dependency versions thực sự kiểm |
| baselines/task-e-source-manifest.json | Tạo | Upstream commit/license/file hashes và adapter deltas |
| baselines/rcd-td12.patch | Tạo | Exact time-drop-after-split patch và provenance |
| .gitignore | Tạo | Loại raw mới/virtualenv/cache/large intermediates khỏi Git; không untrack dữ liệu lịch sử |

Modules là nghiên cứu preflight dùng trong E, không tuyên bố hoàn tất pipeline F. Có thể dừng sớm và không tạo các file chưa cần nếu phát hiện blocker. Nếu cần thay đổi logic ngoài TD, trình amendment trước, không coi impact map là quyền sửa method.

## 5. File sinh tự động, snapshot và dung lượng

Đây là output families được tạo khi có bằng chứng; không tạo file rỗng để đủ checklist.

- `W/baselines/upstream/<source>/<commit>/`: immutable source/license snapshots cần cho comparator; exact file manifest trước sử dụng. Không chạy script cài đặt upstream chưa kiểm.
- `W/environments/task-e/`: isolated environment nếu dependency cần; không nâng cấp môi trường audit cũ để ép tương thích.
- `W/datasets/rcaeval/task-e-development/<case>/`: chỉ telemetry development còn thiếu; exact remote revision/object hashes, dữ liệu mới không commit. Existing samples chỉ đọc.
- `W/results/task-e/<run-id>/run-contract.json`, `source-manifest.json`, `environment.json`, `development-inputs.json`: tạo trước corresponding run; có authorization/source/config/code/data/seeds/hardware/output schemas/exposure.
- Cùng run directory: `loader-audit.json`, `fixture-report.json`, `leakage-audit.json`, `baseline-fidelity.json`, `selection.json`, `sensitivity.csv`, `diagnostics.json`, `failures.jsonl`, `resources.json`, `review.json`, `adjudication.md` khi phase thực sự đã làm.
- `intermediates/`, `predictions/`, `logs/`: per-case/per-config arrays, masks, raw summaries, graphs/perturbation hashes, numeric output/ties/residuals/events, process logs; giữ mọi attempts, không ghi đè run cũ.
- `governance-validation.txt`: kết quả audit sau sửa canonical docs; không thay thực nghiệm.

RAM máy khoảng15.7GiB, CPU i5-1240P12cores/16threads, D còn khoảng74GiB ở thời điểm kiểm. Dùng từng case/giới hạn concurrency; resource limits cụ thể đăng ký trước run sau inventory, không đoán thời gian hoàn tất. Không cài cloud/GPU, không trả phí hoặc upload dữ liệu.

## 6. Lịch sử xác nhận impact map — đã được duyệt

Global Working Agreement yêu cầu trình impact map và explicit approval trước khi sửa hơn3file. Minh đã cấp quyền mục tiêu E; xác nhận còn lại chỉ dành cho **gói file/phạm vi cụ thể§4–5**, không xin lại quyền chạy hoặc yêu cầu bạn duyệt công thức.

Trong lúc chờ có thể tiếp tục read-only source/data/implementation review. Trước xác nhận không thực hiện đợt sửa nhiều file, cài môi trường, tải corpus development hoặc model run. Việc tạo bản kế hoạch này là preparation được yêu cầu, không đánh dấu state E đã chạy.


**Approval receipt:** Minh trả lời “Duyệt gói file và tiếp tục theo các gate đã nêu”. Chỉ áp gói§4–5, scope development; không duyệt outcome hoặc method amendments. Xác nhận ở canonical U27/RCA-048.
