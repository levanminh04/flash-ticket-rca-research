# Pre-Approval Task D Review Packet — TD-v1.2

Minh, 26/09/2026. Lớp `FORMATION / REVIEW_PACKET`. **REVIEW_READY WITH BLOCKERS — do not start E**. Bản này hoàn thiện đặc tả để xét duyệt; chưa có phê duyệt của Minh, kết quả thực nghiệm hoặc cấu hình cuối đã chọn và freeze.

## A. Source-of-truth snapshot

| Repository | Branch / HEAD trước và sau lượt | Trạng thái |
|---|---|---|
| P: D:/Project/flash-ticket-platform | codex/rca-research-program / fa27a9d32873d957818ac389b8d3fc8f4e98b185 | Canonical; README có thay đổi từ trước, được bảo tồn |
| W: D:/Project/flash-ticket-rca-research | main / 38a0d0362e1e51a56ba3a6334a7f7c13a036f603 | Evidence chi tiết; sạch lúc bắt đầu |

P main cũ ở d4d7f6f thiếu trạng thái D hiện tại. History, CURRENT-STATE và handoff xác định branch P trên là nguồn mới nhất; không có xung đột authority chưa phân xử được. TD-v1.2 hiện **local, chưa commit, chưa push**.

[Prechange inventory](td-v1.2-prechange-inventory.json) lưu SHA-256 của 256 tệp tracked ở P và 126 tệp ở W. README giữ nguyên SHA-256 `3646cb1b6e8da832e8b9513fd8318d749f7f5f6788b5d3223eda7f5a9a662274`. TD-v1.1 có SHA-256 `9a70e64db570916b9f02fcc81fab3f4bf7cef0313f5c2de213a9eb0a8d690f3c`, được giữ trong lịch sử Git.

Nguồn đã đọc theo ngữ cảnh: AGENTS, toàn bộ governance skill và authority/gates; DT18, roles, advisor; bootstrap, current state, decisions, Master, artifact map, C lock, D, handoff và B digest. Task A được đọc các phần cơ chế, metrics, datasets và giới hạn liên quan. W được đọc B CLOSED §12, full-trace/metrics/log/GT audits, Task C independent/cross-review, D evidence/exposure, source-first review, reconciliation, delta review, validators và program workflow. Các lựa chọn kỹ thuật còn được đối chiếu primary papers và official implementations; không dùng vài search snippets thay việc đọc nguồn liên quan, không đọc legacy để hình thành thiết kế.

Mission gốc được lưu đầy đủ ở P `docs/evidence/project-direction/2026-09-26-rca-task-d-redesign.md`; SHA-256 attachment là `9F86A703CB4F6381BAF09DA0370857A0EE8D70432524379B8F1F4C8F7E0E592C`.

## B. Five-reviewer verdict và giới hạn độc lập

**Chỉ có ba native agents độc lập, không đủ năm.** Công cụ từ chối cấp thêm agent bằng lỗi `agent thread limit reached`, kể cả khi worker đã completed. Agent B làm thêm vai trò E; agent C làm thêm vai trò A. Hai vai trò bổ sung chia sẻ context với vai trò trước, nên không được tính là reviewer độc lập mới.

Cả năm memo theo vai trò đã có trước khi gửi vòng phản biện A→B→C→D→E→A. Các cạnh phản biện được thực hiện bằng memo tóm tắt do coordinator chuyển; giới hạn context và nguồn memo được ghi trong [review memos](td-v1.2-review-memos.md). Yêu cầu năm subagents độc lập vẫn là blocker.

| Reviewer | Verdict ban đầu / Major findings | Giữ lại | Sửa và kết quả delta |
|---|---|---|---|
| A — scope/advisor; agent C kiêm | MAJOR REVISION: C5, multi-public validation và graph comparator chưa đủ thực chất | C1 primary, DT18, LLM downstream | C5 có mechanics, comparator và dataset roles cụ thể; giới hạn cùng agent còn nguyên |
| B — thuật toán/toán học | MAJOR REDESIGN: fusion tùy ý, nhầm mass/value propagation, detector prior, comparator và precision của R | Common input tensor, observed relations, GT boundaries | PPR, value-diffusion backup, forecasting, RCD; các lỗi solver, gates và time input được đóng |
| C — thống kê/selection | MAJOR REVISION: dev-label ban đã bị supersede; số cell nhỏ; calibration và inference cần làm rõ | Grouped repeats, ties, exposure, finite-study effects | Registry, CV, sensitivity, weighted CDF và conditional CI; ba finding delta cuối đã đóng |
| D — dữ liệu/GT | REVISE: thiếu RE3 compatibility; count-signal weakness chưa được chứng minh; admission và GT limits | RE2 primary, literal joins, không tạo GT/graph giả | Frozen RE3 transfer, equal-cell headline, role matrix; numeric threshold transport đã được làm rõ |
| E — falsification; agent B kiêm | Material revision: hidden selection, false freeze, broad negative claim và baseline fidelity | Không E, không hứa graph thắng | Failure tree, backups đăng ký trước, lưu cả failures; giới hạn cùng agent còn nguyên |

Final B/C/D đọc lại canonical D và xác nhận các finding cụ thể đã đóng; không còn must-fix họ xác định trong phạm vi được giao. Đây là kết quả review thiết kế, không chứng nhận tài liệu hết mọi lỗi hoặc AI approval.

Disagreement còn thực chất: smoothing có thể là graph AD, và thuộc tính giảm max không tự chứng minh phương pháp vô hiệu. Track mới cần grounding và kiểm chứng adequacy mạnh hơn. Forecast/ridge/pooling/prefix là adaptation, không phải reproduction GDN/CIRCA. Chọn local qua L và common λ qua joint objective là chính sách có giới hạn, không phải cách duy nhất công bằng. RE3 count-signal weakness chưa được chứng minh. Hai walk rankers không đủ để kết luận âm về mọi graph method; RE3-TT cũng không chứng minh generalization sang hệ thống độc lập.

## C. Advisor-alignment matrix

| Step của giảng viên | Phương pháp / task / dataset / metric | Trạng thái và giới hạn |
|---|---|---|
| 1. Dependency graph | Reference parent relations; giữ direction; PPR reverse/undirected; caller/callee cho C5 | CANDIDATE đã đặc tả; observed graph không đồng nghĩa causal/complete graph; coverage của dữ liệu thực dùng phải kiểm ở E/F |
| 2. Graph AD và ánh xạ telemetry | G/L/ALL prefix ridge forecasting residual; TV secondary; M/T/L count channels và masks | First-class method track; regime precision/recall/F1, coverage và event outcomes; không tạo node GT hoặc production FPR |
| 3. Public datasets | RE2 primary; RE3-TT fault-family transfer; RE3-OB cross-application; SS/LEMMA component roles | Vai trò cụ thể đã có; admission/license/campaign và kết quả thực nghiệm trên nhiều public datasets còn OPEN |
| 4. So với RCA đã có | Matched L/R; executable LocalMAX, BARO adapted, RCD adapted; MRR primary, Hit/NDCG secondary | Có source/fidelity contract; chưa reproduce baseline trong lượt này, không tuyên bố SOTA |
| 5. LLM explanation | Ranked packet bất biến; evidence IDs; observed/processing direction và uncertainty | Task I kiểm faithfulness/usefulness; không rerank, sửa answer hoặc tạo GT |

Hướng dẫn cũ coi hệ thống chủ yếu để demo được giữ như bằng chứng lịch sử. DT18 và RCA-018–021 giữ nghĩa vụ xây dựng, đánh giá hệ thống bán vé phân tán, tích hợp và chạy cơ chế trong FlashTicket. Ngày/kênh gửi bản hướng dẫn gốc chưa xác minh; không tự điền.

## D. Formula/parameter provenance summary

[Ma trận đầy đủ](td-v1.2-provenance-and-data.md) có **38 dòng thành phần, 11 cột**.

| Phân loại | Thành phần tiêu biểu |
|---|---|
| DIRECTLY_ADOPTED | Physical parent identifiers; các constants từ pinned RCD artifact |
| ADAPTED_FROM_PRIOR_WORK | Robust reference deviation; reverse PPR; graph forecasting/residual; graph total variation |
| STANDARD_STATISTICAL_METHOD | Ridge estimator, numerical solve, quantiles, tie expectations, bootstrap và Bonferroni |
| STUDY_SPECIFIC_DESIGN | Exact windows/bins/floors/pooling/fusion; trace/log count features; control budget/mobility; fit gates; grids; threshold, streak, refractory, δ; adapter và selection policy |

Bỏ primary cap 20, denominator giữ cố định khi thiếu modality và rolling-mixture q99. Floor/pool/fusion, graph orientation/damping và λ/q chuyển sang bounded development selection. Sensitivity bắt buộc trước final freeze cho windows/bins/floors/tails, damping/direction, R budget, prefix/lag/residual floor, threshold/event policies và RCD bins.

Các con số không có external basis được ghi study-specific, không gán citation để hợp thức hóa. Ridge và TV không được gọi là thuật toán mới hoặc causal guarantee. Empirical selection và sensitivity **chưa chạy** trong lượt này; không chọn tham số bằng final outcomes.

## E. Revised research architecture

```text
C1 — phép đo controlled, known-window, primary
  Common M+T evidence / cùng candidate universe
    → L / observed O / perturbed R → PPR service ranking
    → immutable ranking + evidence packet

C5 — track phát hiện theo thời gian
  Telemetry theo thứ tự → prefix graph/scaler/model fit trong 120s
    → 60s held-out residual scale
    → G / L / ALL forecasting residual scores
    → threshold fit trên RE2 development
    → persistence + refractory → trigger
    → past 300s reference / 60s query MTL diagnosis
    → structured evidence → LLM explanation ở I
    → read-only integration / controlled truth ở H
```

Detector không chọn các ca C1. PPR mass khác row-value diffusion; TV là spatial detector secondary, không phải cách cứu C1 ranking sau kết quả xấu. Prefix fitting là runtime policy quan sát được, không nhận injection time τ.

C3 triển khai supporting operation evidence, hoãn scored-operation ablation vì thay feature count/multiplicity. C4 triển khai late graph ranking, hoãn cross-placement comparison vì thay scorer/capacity không cô lập relation effect. D §1.1 ghi rationale và điều kiện mở lại bằng protocol riêng. C5 không được gọi là kết quả C4; window/bin sensitivity không tự mở optional C2.

Prefix nằm trước declared fault theo metadata RE2/RE3; điều này không chứng nhận independent healthy truth hoặc arrival timing. Scale từ 9–12 held-out errors có thể nhiễu; không gọi nó q99 hoặc FPR. Shared thresholds có conditional weights rõ ràng. G/L/ALL dùng cùng nominal slots/budget nhưng active capacity vẫn khác, phải báo.

## F. Dataset plan

| Dataset | Vai trò | Evidence và điều kiện còn phải kiểm |
|---|---|---|
| RE2-TT | Primary C1, first-class C5 regime proxy, baselines | Full trace audit và metadata/samples; E/F kiểm mọi window, prefix, mapping và log join thực dùng |
| RE3-TT | 30 ca frozen RE2-selected fault-family transfer; headline equal-cell | 90 HTTP206 footers; một raw sample có 54 reference relation types và 100% reference parent resolution; joins của 29 ca còn lại chưa kiểm raw. Khóa cả numeric RE2 thresholds, không chỉ q |
| RE3-OB | Frozen cross-application/code-fault candidate | Tri-modal, 30 ca/10 cells; literal mapping và admission còn phải kiểm; không pool với TT |
| RE2-OB | Optional resource/network cross-application control | Hai faulty horizons 210/284s; không áp âm thầm query 300s rồi bỏ ca khó |
| Sock Shop RE2/RE3 | Local M/L, BARO/RCD component portability | Không traces; không lặp observed-trace C1/G bằng graph giả; answer files bị chặn khỏi input |
| LEMMA ProductReview 20211203 | Entity-ranking/long-time component candidate | Release đã pin; PPTX GT, granularity, mapping, units và quyền sử dụng OPEN. Fault times JST phải đổi sang UTC bằng cách trừ 9 giờ; chưa có declared span traces |
| LEMMA Cloud | Supporting component candidate | Có ca CloudTrail-only; không giả định mọi ca có EKS logs. Graph/GT/license admission OPEN |
| FlashTicket | Target transfer, integration và system evaluation | Theo H/DT18; không thay bằng chứng public thứ hai hoặc lấy dataset score thay kiểm chứng hệ thống |

Audit footer chuyển 6,026,998 bytes, kiểm 90/90 tệp, không lỗi: M 54,030 rows, L 1,627,863 rows, T 4,152,676 rows; số schema variants M/L/T là 21/1/1. Row counts khớp metadata. Không tải telemetry rows từ remote. Official LFS identities không phải full-file hash do ta tính độc lập.

Đổi dataset không bảo đảm xử lý metric ceiling hoặc làm graph tốt hơn. Không tạo affected-node, operation, path hoặc actual-onset GT.

## G. Files changed và impact map

**P: 11 tệp của task, gồm 1 mới và 10 sửa.** README là thay đổi không thuộc task, được giữ nguyên.

| Tệp tương đối từ root P | Thao tác / lý do |
|---|---|
| docs/evidence/project-direction/2026-09-26-rca-task-d-redesign.md | NEW: toàn bộ mission, provenance và hash để giữ current authority |
| docs/research-rca/RESEARCH-DECISIONS.md | APPEND: RCA-022–042, quyết định nguyên tử và scoped supersession; giữ nguyên các dòng cũ |
| docs/project/decision-register.md | APPEND: route đến phân sổ RCA; không tạo bản quyết định cạnh tranh |
| docs/research-rca/task-d-method-and-experiment-specification.md | REVISE: TD-v1.2 method, selection, sensitivity, controls, baselines, C5, data và claims |
| docs/research-rca/task-c-research-decision-lock.md | UPDATE: quyền development, vai trò C5 và navigation; giữ Phase 2 history |
| docs/research-rca/MASTER-RESEARCH-PROGRAM.md | UPDATE: MRP-v1.2 selection/freeze gates và public roles |
| docs/research-rca/SESSION-BOOTSTRAP.md | UPDATE: resume đúng phiên bản, quyền và blocker hiện tại |
| docs/research-rca/task-b-dataset-capability-summary.md | APPEND: current policy notice; giữ facts và snapshot Task B |
| docs/research-rca/ARTIFACT-MAP.md | UPDATE: route, mục đích và consumer của evidence mới |
| docs/research-rca/CURRENT-STATE.md | UPDATE: trạng thái TD-v1.2, blocker, E và local publication |
| docs/research-rca/task-d-handoff.md | UPDATE: next action, OPEN owners, contracts, evidence và nội dung formal report |

**W: 9 tệp mới; không sửa tệp có từ trước.**

| Tệp tương đối từ root W | Mục đích |
|---|---|
| task-d/td-v1.2-prechange-inventory.json | Trạng thái và tracked hashes trước sửa |
| task-d/td-v1.2-review-memos.md | Initial memos, ring, reconciliation, delta closure và giới hạn độc lập |
| task-d/td-v1.2-provenance-and-data.md | Formula/parameter provenance và task-compatibility matrices |
| task-d/td-v1.2-review-packet.md | Packet A–J này và danh sách chính xác các tệp |
| task-d/audit_td_v1_2_public_metadata.py | Bounded audit official footers, trees và README |
| task-d/td-v1.2-public-metadata.json | Receipt 90 tệp, pins và cohorts |
| task-d/validate_td_v1_2.py | Validator mới cho tài liệu, scope và synthetic mathematics |
| task-d/td-v1.2-validation.json | Kết quả kiểm thực tế, hashes và final file scope |
| task-d/td-v1.2-governance-validation.txt | Output governance audit thực tế |

Impact map đã công bố trước mutation hơn ba tệp; U26 §15 và RCA-042 cho phép chỉnh tài liệu RCA trong đúng phạm vi mà không hỏi lại. Chuỗi cập nhật: **mission → quyết định nguyên tử → canonical D → C/Master/bootstrap/B notice/map/current/handoff → W review, provenance, audit và validation receipts**. Tác động thuộc nghiên cứu/phương pháp và điều phối; không đổi API, schema, application, architecture gates hoặc phạm vi hệ thống.

Không reset/clean/stash/checkout đè, không xóa lịch sử hoặc sửa raw data. Old review/validation/exposure receipts được bảo tồn; temporary content staging đã dọn. Không commit/push trong mission này.

## H. Validation — kết quả và giới hạn

[Receipt TD-v1.2](td-v1.2-validation.json) ghi từng check và hash; [governance output](td-v1.2-governance-validation.txt) giữ output gốc.

| Check / cách chạy | Kết quả và cách hiểu |
|---|---|
| Legacy TD-v1.1 validator, dry-run trước sửa, bảo tồn receipt | **95/97 PASS**; hai FAIL là assertions về HEAD lịch sử sau lần push trước. Không ghi đè old receipt |
| W: `./.venv/Scripts/python.exe task-d/validate_td_v1_2.py` | **126/126 PASS**: provenance/history/scope/links/UTF-8, preservation, receipt identity và synthetic math |
| P: `.agents/skills/govern-capstone-work/scripts/audit-governance.ps1` | **PASS, 1 warning**: diff có 12 tệp nên cần approved impact map. Số này gồm 11 tệp task và README dirty từ trước; impact map và U26 authorization đã có. Script không tự đọc approval trong hội thoại |
| `git diff --check` ở cả hai roots | **PASS** về whitespace; complete diff và final file set được kiểm riêng |
| W: `./.venv/Scripts/python.exe task-d/audit_td_v1_2_public_metadata.py` | **90/90, zero errors**; chỉ footer/tree/README, không model run hoặc remote telemetry rows |
| B/C/D delta reread và synthetic math | Các finding được nêu đã đóng; solver checks khoảng 1e−16, ba damping values và input 1e308 được kiểm. B xác nhận C3/C4 disposition đã khôi phục; C kiểm lại planning arithmetic khớp interval: .119/.188/.257, chỉ cho từng contrast, không joint power |

Lần đầu validator mới đạt 124/126: hai mục là EOF whitespace và governance output chưa có. Sau khi sửa định dạng và audit kết thúc, đạt 126/126. Không sửa method chỉ để khớp assumptions của old validator.

Validator changelog: TD-v1.1 no-dev-label, fixed operator/split equality và rolling calibration không còn là current contract. Validator mới kiểm scoped supersession/history, registry/rights, PPR mass và value invariants, normalization trước solve, directed degree/partition controls, residual scale, weighted CDF, triggers, ties, MC planning và preservation. Old validator/receipt không sửa.

**Không có check nào ở đây chứng nhận runtime GT firewall, actual-used loaders/joins, empirical sensitivity, source fidelity/environment, model benefit, production availability hoặc LLM quality.** Những việc đó cần E/F/H/I được giao đúng scope; không gọi synthetic/document PASS là kết quả RCA.

## I. Remaining OPEN — owner và thời điểm

| OPEN | Owner / đầu vào cần thiết / thời điểm |
|---|---|
| Năm distinct independent source-first reviewers | Coordinator trong session có đủ tool capacity; cần reviewers độc lập thật trước E. Năm vai trò từ ba agents không đáp ứng |
| Human acceptance và explicit E scope | Minh đọc packet/protocol, chấp nhận hoặc yêu cầu sửa; REVIEW_READY không tự cấp quyền E |
| Empirical selection/sensitivity, actual-use compatibility, baseline fidelity, resources, R mobility và threshold reachability | E/F khi được giao; cần config/run/input receipts trước final freeze G. Đây là nghĩa vụ thực nghiệm, không chứng nhận đã hoàn thành ở D |
| Exact public-extension campaign; LEMMA license, GT/time/schema admission | Minh + D/E trước campaign; scientific roles đã đề xuất, measured multi-public evidence chưa có |
| Effects, valid negative hoặc inconclusive | G sau seal/freeze; không hứa effect dương |
| FlashTicket controlled truth, arrivals, integration và system measurements | H và system team tại gates của mình |
| Explanation provider/rubric/faithfulness/usefulness | I; sai ranking không được LLM sửa thành đúng |
| Advisor original send date/channel | Minh nếu còn nguồn; relative historical context đã xác nhận, không phải method blocker |

Những scientific choices có thể nghiên cứu trước E đã có CANDIDATE cụ thể. Future execution receipts không tự là lý do bác bỏ D design; yêu cầu năm reviewer độc lập là điều kiện assurance hiện chưa đạt.

## J. Final recommendation

**REVIEW_READY WITH BLOCKERS — do not start E**

TD-v1.2 đã có method, selection, sensitivity, failure và dataset contracts cụ thể; các finding delta B/C/D đã đóng trong scope review. Chưa đạt yêu cầu năm independent agents; human acceptance và E scope vẫn OPEN. Không ghi APPROVED hoặc empirical freeze/performance claim.

Nội dung cần đưa vào báo cáo đồ án sau này: lineage/adaptation/custom rationale; local/control capacity limits; historical exposure; conditional finite-study effects; C5 proxy GT/calibration; bounded negative và failure attribution; fault-family so với cross-application transfer; immutable LLM explanation; integration và system evaluation theo DT18.
