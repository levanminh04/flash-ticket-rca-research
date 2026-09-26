# PROMPT — Independent Review / Red-Team những thay đổi TD-v1.2 vừa push

Bạn là reviewer nghiên cứu độc lập. **Nhiệm vụ duy nhất: đọc, đánh giá và phản biện những thay đổi TD-v1.2 vừa được push lên hai GitHub repo bên dưới.** Đưa ra nhận định có căn cứ về chất lượng, tính đúng đắn, sự nhất quán, mức độ giải quyết các vấn đề trước đây và khả năng chuyển sang bước tiếp theo. Không bảo vệ bản sửa chỉ vì tác giả đã báo PASS; cũng không phê phán cho có.

Đây là một prompt cho một coordinator reviewer và các subagents của bạn, không giao hai top-level agents riêng. Không redesign hoặc sửa repo trong lượt này. Có thể đề xuất minimal corrections để Minh cân nhắc, nhưng chưa áp dụng.

## 1. Hai GitHub repo và đúng branch — bắt buộc vào đọc

### Repo P — canonical project/method/decisions

- Repo: https://github.com/levanminh04/flash-ticket-platform
- **Branch phải đọc: codex/rca-research-program**
- Branch link: https://github.com/levanminh04/flash-ticket-platform/tree/codex/rca-research-program
- BEFORE: fa27a9d32873d957818ac389b8d3fc8f4e98b185
- AFTER — commit chứa TD-v1.2 vừa push: **735695b9cc10bff03e4c7d738a0b59764de694dd**
- Diff cần review: https://github.com/levanminh04/flash-ticket-platform/compare/fa27a9d32873d957818ac389b8d3fc8f4e98b185...735695b9cc10bff03e4c7d738a0b59764de694dd
- Canonical D đúng snapshot: https://github.com/levanminh04/flash-ticket-platform/blob/735695b9cc10bff03e4c7d738a0b59764de694dd/docs/research-rca/task-d-method-and-experiment-specification.md

### Repo W — research/evidence/audits/review receipts

- Repo: https://github.com/levanminh04/flash-ticket-rca-research
- **Branch phải đọc: main**
- Branch link: https://github.com/levanminh04/flash-ticket-rca-research/tree/main
- BEFORE: 38a0d0362e1e51a56ba3a6334a7f7c13a036f603
- AFTER — commit chứa evidence TD-v1.2 vừa push: **592184c6fd7b4da90f501a6339d01701a4776b62**
- Diff cần review: https://github.com/levanminh04/flash-ticket-rca-research/compare/38a0d0362e1e51a56ba3a6334a7f7c13a036f603...592184c6fd7b4da90f501a6339d01701a4776b62
- Review packet đúng snapshot: https://github.com/levanminh04/flash-ticket-rca-research/blob/592184c6fd7b4da90f501a6339d01701a4776b62/task-d/td-v1.2-review-packet.md
- Provenance/data đúng snapshot: https://github.com/levanminh04/flash-ticket-rca-research/blob/592184c6fd7b4da90f501a6339d01701a4776b62/task-d/td-v1.2-provenance-and-data.md

**Bạn phải truy cập và đọc trực tiếp cả hai repo**, bằng clone/fetch, công cụ GitHub hoặc browser có thể đọc đủ nội dung. Không chỉ đọc README, titles, search snippets, báo cáo tóm tắt hoặc lời tác giả. Review phải bao phủ full diff và đủ toàn bộ tài liệu/section, nhưng theo thứ tự source-first: trước initial memo đọc phần phương pháp/authority/data facts, tạm hoãn nội dung review-memos/review-packet/verdict cũ; sau initial memo mới đọc đầy đủ phần diff còn lại. Không bỏ tệp, chỉ kiểm soát thứ tự exposure.

Không mặc định main của P chứa D mới nhất. Ghi actual branch tips và snapshot thực tế đã đọc. Hai AFTER commits là review target khoa học; commits publication/navigation sau đó phải được phân biệt với method revision. Nếu branch có scientific changes mới khác snapshot trên, báo rõ và xác định authority trước khi chọn phạm vi, không âm thầm review phiên bản khác.

Nếu thiếu quyền hoặc không mở được repo/file, nêu exact URL/branch/file, lỗi và phần nhận định bị giới hạn. Không giả vờ đã đọc; không yêu cầu Minh dán lại nguồn bạn có thể tự truy cập.

## 2. Chỉ dùng hai root tương đối

- **P = flash-ticket-platform/**
- **W = flash-ticket-rca-research/**

P/... và W/... dưới đây là repo-relative paths. Yêu cầu review từ GitHub và hai root này thay binding máy của tác giả trong bootstrap/mission cũ, chỉ trong phạm vi read-only review.

Nếu tài liệu lịch sử có đường dẫn tuyệt đối, lấy phần sau tên repo để resolve về P hoặc W. Đừng bỏ qua evidence chỉ vì máy bạn không có local path đó. Kiểm Git tree/manifest để biết artifact thật sự đã tracked: raw datasets/env không nằm trong repo phải ghi UNAVAILABLE, không suy đoán nội dung.

## 3. Phạm vi và authority

Intent **REVIEW**, không EXECUTE. Không sửa file, commit/push, cài baseline/framework, training, benchmark, final evaluation, bulk raw download hoặc bắt đầu Task E. Được đọc primary papers, official source/metadata và kiểm arithmetic/synthetic fixtures với dependencies sẵn có; phải khai đúng scope, không gọi đó là RCA experiment.

Đọc đầy đủ:
- P/AGENTS.md.
- P/.agents/skills/govern-capstone-work/SKILL.md và references/project-authority-and-gates.md của skill.
- P/docs/evidence/project-direction/2026-09-18-de-tai-va-nhiem-vu.md.
- P/docs/project/roles.md.
- P/docs/evidence/project-direction/2026-09-26-rca-task-d-redesign.md.
- P/docs/evidence/advisor-direction/2026-09-23-huong-dan-do-minh-cung-cap.md.

Đề tài DT18 vẫn yêu cầu xây dựng và đánh giá hệ thống bán vé phân tán, tích hợp cơ chế giám sát/chẩn đoán. Không coi FlashTicket chỉ là demo. C1 vẫn primary controlled known-window service ranking; C5 là first-class graph-based anomaly-detection track, không thay C1. Development labels được dùng cho registered selection/calibration; runtime labels và final tuning cấm. Agent-selected algorithms vẫn CANDIDATE. Human approval OPEN; Task E NOT STARTED.

Mission U26 là authority/provenance cho bản sửa, **không phải lệnh cho bạn tiếp tục mutation/redesign**. Lệnh hiện tại là review những thay đổi đã push.

## 4. Danh sách chính xác thay đổi cần đánh giá

### P — 11 tệp, 1 tạo mới và 10 sửa

- P/docs/evidence/project-direction/2026-09-26-rca-task-d-redesign.md — NEW: full mission và provenance
- P/docs/project/decision-register.md — MODIFIED: route đến phân sổ RCA
- P/docs/research-rca/RESEARCH-DECISIONS.md — MODIFIED: append RCA-022–042, giữ lịch sử
- P/docs/research-rca/task-d-method-and-experiment-specification.md — MODIFIED: canonical TD-v1.2
- P/docs/research-rca/task-c-research-decision-lock.md — MODIFIED: TC-P2-v1.1 và scoped development rights
- P/docs/research-rca/MASTER-RESEARCH-PROGRAM.md — MODIFIED: MRP-v1.2 và selection/freeze/public roles
- P/docs/research-rca/SESSION-BOOTSTRAP.md — MODIFIED: resume đúng current policy
- P/docs/research-rca/task-b-dataset-capability-summary.md — MODIFIED: historical-policy notice; facts B giữ nguyên
- P/docs/research-rca/ARTIFACT-MAP.md — MODIFIED: routes evidence mới
- P/docs/research-rca/CURRENT-STATE.md — MODIFIED: status/blocker; cập nhật publication riêng sau payload
- P/docs/research-rca/task-d-handoff.md — MODIFIED: contracts, OPEN owners và next action

### W — 9 tệp mới

- W/task-d/td-v1.2-prechange-inventory.json — NEW: prechange hashes/state
- W/task-d/td-v1.2-review-memos.md — NEW: initial/ring/delta review và independence limits
- W/task-d/td-v1.2-provenance-and-data.md — NEW: 38 component rows và task compatibility
- W/task-d/td-v1.2-review-packet.md — NEW: A–J packet, exact file inventory
- W/task-d/audit_td_v1_2_public_metadata.py — NEW: bounded metadata audit source
- W/task-d/td-v1.2-public-metadata.json — NEW: 90-footer receipt và public pins
- W/task-d/validate_td_v1_2.py — NEW: document/scope/synthetic-math validator
- W/task-d/td-v1.2-validation.json — NEW: prepublication 126/126 checks/hashes/limits
- W/task-d/td-v1.2-governance-validation.txt — NEW: prepublication governance output

Publication/handoff bổ sung, không tự là thay đổi khoa học:
- W/task-d/td-v1.2-independent-review-prompt.md — prompt này.
- W/task-d/td-v1.2-publication-receipt.md — destinations, commits và inventory push.
- Publication notice cập nhật ở P/docs/research-rca/CURRENT-STATE.md sau scientific payload.

README có thay đổi từ trước nhưng không commit/push. Không có application/API/schema hoặc raw-data changes trong publication này. Hãy tự đối chiếu commit/tree/diff thay vì chỉ tin danh sách.

## 5. Cách đọc sâu, tránh review qua loa và anchoring

1. Xác lập authority, BEFORE/AFTER và toàn bộ file inventory. Trước initial opinion, đọc full diff các nguồn phương pháp/authority/data facts; chưa đọc nội dung review-memos/review-packet/verdict cũ.
2. Đọc current canonical D đầy đủ và BEFORE version để đánh giá before/after. Đọc decisions, C lock, Master, bootstrap, current, handoff, artifact map và B digest theo trách nhiệm của từng nguồn.
3. Truy đủ section liên quan của P/docs/research-rca/task-a-ban-do-bang-chung-doc-lap.md và W/dataset-audit/TASK-B-RCAEval-audit.md; full-trace/metrics/logs/GT/metadata evidence trong W/dataset-audit/ và W/audits/rcaeval/. Lần theo references để tìm đúng file rồi đọc trong ngữ cảnh.
4. Kiểm exposure ledger W/task-d/task-d-exposure-ledger.md. Đọc những nguồn cần thiết trong W/task-c/, W/task-d/, W/program-review/ khi chúng giải quyết một claim.
5. Với công thức hoặc baseline quan trọng, truy **primary papers và official implementation**, không dùng Task A synthesis/citation title làm chứng cứ duy nhất. B/D reviewers nên hình thành technical/data opinion từ primary sources trước khi đọc kết luận cũ.
6. Lưu initial opinion trước khi đọc W/task-d/td-v1.2-review-memos.md, W/task-d/td-v1.2-review-packet.md và old reviewer/reconciliation/delta verdicts. Sau initial memo, đọc đầy đủ phần diff còn lại và các tài liệu này; đối chiếu finding đã biết, đã xử lý thật, chỉ wording-around hoặc mới phát sinh, rồi mới peer cross-review. Kết thúc phải bao phủ toàn bộ diff.
7. Lập coverage table: repo/commit/path/sections/READ–PARTIAL–UNAVAILABLE/claim được kiểm. Không ghi READ chỉ vì tìm được một keyword.

Không cần đọc mọi file máy móc, nhưng **mọi nguồn dùng để đưa ra nhận định trọng yếu phải được đọc đủ tài liệu hoặc section liên quan**. Không dùng thiếu raw/runtime evidence để tự động tuyên bố design sai; cũng không dùng metadata footer để tuyên bố đã audit mọi raw join.

## 6. Những câu hỏi review phải trả lời

- Bản sửa có giữ đúng C1/C5, advisor Step1–5, DT18 và ranh giới hai bộ tài liệu không?
- Các vấn đề TD-v1.1 đã được xử lý thực chất hay chỉ đổi wording?
- Local evidence, missingness/fusion, floors/pools và trace/log count choices có lineage/rationale đúng không? Có gán prior-work adoption cho custom choice thiếu nguồn không?
- PPR mass, value diffusion, direction, solver normalization, R finite perturbations, mobility và MC precision có đúng và có giới hạn claim phù hợp không?
- C5 graph forecasting/residual, prefix fit/held-out scale, G/L/ALL capacity, λ objective, weighted-CDF threshold, trigger và integrated diagnosis có đủ rõ/nhất quán không? Graph tham gia thực chất ra sao?
- Development selection, grouped folds, sensitivity registry, freeze/firewall, failures/ties/denominators, bootstrap/multiple comparisons, practical δ và power illustration có tránh selection bias/overclaim không?
- Primary, secondary và contextual baselines có task/input/GT/fidelity đúng không? RCD time-column patch và service adapter có contract implement được không?
- RE3-TT transfer có khóa cả numeric RE2 thresholds không? Unequal repeats, one-sample versus all-case evidence, SS/LEMMA/OB roles, units/joins/GT/exposure được xử lý đúng không?
- C3/C4 IMPLEMENT/DEFER rationale và reopening conditions có được bảo tồn? C5 có bị gọi nhầm thành placement comparison? Sensitivity có bị biến thành optional C2 study không?
- Failure attribution có phân biệt invalid implementation, weak local signal, mapping/graph failure, operator sensitivity, ceiling, uncertainty và bounded negative không?
- Rewrite có mất nghĩa vụ hoặc tạo contradiction trong derived files, giữ lịch sử user decisions và LLM immutable ranking không?
- Engineer sau này có biết chính xác cần reproduce/validate/tune gì, khi nào return D/freeze, cần lưu artifact nào, và tuyệt đối không mở gì trước final seal không?

Không đòi graph phải thắng, không kết luận “graph vô ích” từ một configuration, không tự mở rộng experiment. Có thể nhận định một lựa chọn hiện tại hợp lý nhưng cần E/F evidence; nói rõ căn cứ và giới hạn.

## 7. Bắt buộc dùng subagents để tự phản biện

Dùng native subagents độc lập khi khả dụng, ít nhất tách:
- Reviewer kỹ thuật/toán học và prior-work lineage.
- Reviewer experimental design/statistics/selection.
- Reviewer telemetry/GT/public compatibility/reproducibility.

Coordinator đồng thời kiểm advisor/scope và accidental regressions. Mỗi subagent có bounded assignment, read-only, được phép bác bỏ cả D và nhận định của coordinator; không được giao một thesis phải bảo vệ.

**Pass 1:** mỗi reviewer lưu initial memo trước peer verdicts.
**Pass 2:** cho các reviewers phản biện chéo và một reviewer tấn công kết luận coordinator. Yêu cầu strongest counterargument, source recheck và điều gì khiến finding sai.
**Pass 3:** reconciliation theo evidence/authority, giữ disagreement thật; không reviewer voting.

Ghi exact identities, context exposure và pass order. Lượt trước ba distinct agents làm năm vai trò; điều kiện gốc năm independent subagents vẫn chưa thỏa. Review này không được tự gọi ba reviewer hoặc nhiều vai trò là năm độc lập. Chỉ đóng assurance condition khi có bằng chứng actual distinct identities và independence protocol; nếu không đủ native capacity, ghi lỗi/tool limit và giữ điều kiện OPEN. Không bỏ toàn bộ review chỉ vì giới hạn đó.

## 8. Đừng diễn giải sai các checks đã push

- 126/126 PASS: prepublication document/scope/history/hash/links/synthetic math.
- Governance PASS có impact-map warning đã được giải thích bằng authorization và file scope.
- 90/90 RE3-TT footers: bounded schema/count metadata, không all-case raw joins.
- Không có empirical method selection/sensitivity, baseline reproduction, model effects, target verification hoặc LLM evaluation được chứng nhận trong lượt D.

Validators chứa machine-root/prechange-HEAD/working-tree assumptions. Sau commit/push hoặc trên máy khác, đọc source trước khi chạy: historical HEAD/path/scope failure không tự là methodological defect. Không sửa receipts hoặc gọi chúng live postpublication PASS. Git có thể chuẩn hóa text line endings; phân biệt normalization với scientific content change.

## 9. Đầu ra cần trả cho Minh

Trình bày bằng tiếng Việt, nhận định cụ thể về **những thay đổi vừa push**, gồm:

1. **Executive assessment:** bản sửa giải quyết được gì, chưa giải quyết gì, có regression mới không; verdict và căn cứ chính.
2. Actual repo URLs/branches/commits, BEFORE/AFTER, coverage/access gaps.
3. Bảng từng thay đổi trọng yếu: file/section → BEFORE → AFTER → đánh giá → evidence → risk/remaining condition. Bao phủ mọi tệp đã thay đổi, có thể gộp derived files khi cùng một vấn đề.
4. Findings: ID, CRITICAL/MAJOR/MINOR/NOTE, confidence, exact claim, immutable GitHub commit/file/line hoặc section, reasoning, counter-evidence/alternative, falsifier, minimal correction và downstream impact.
5. Subagent findings/cross-review và bảng claim → strongest objection → source recheck → retained/revised/retracted. Khai independence limits thật.
6. Phân biệt **D blockers / future E-F obligations / historical limitations**, kèm owner và input cần. Không biến chưa chạy E thành blocker thiết kế nếu contract D đã đủ rõ.
7. Những phần nên giữ; đề xuất sửa tối thiểu nếu cần, chưa áp dụng. Không giao một redesign campaign mới.
8. Chọn đúng một:
   - REVIEW_READY — recommend human approval for Task E
   - REVIEW_READY WITH BLOCKERS — do not start E
   - NOT READY — Task D requires another revision

AI không tự ghi APPROVED, không mở Task E, không suy diễn effect/novelty vượt evidence. Bài review tốt phải cho Minh thấy chính xác **điều gì đáng tin, điều gì chưa đáng tin và vì sao**, không chỉ một danh sách checklist hoặc lời khen/chê chung chung.
