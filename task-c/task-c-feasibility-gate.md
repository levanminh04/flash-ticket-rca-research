# Task C — Hard feasibility và thesis-feasibility gate

- Ngày: 2026-09-21. Trạng thái: **DRAFT / CANDIDATE**. Ý định: `EXECUTE`; loại tạo tác: `FORMATION`.
- Phạm vi: kiểm đủ mười câu hỏi dữ liệu của yêu cầu §15 và từng chiều luận văn §17/24 cho C1–C5 sau hàng rào sáu reviewer và chuẩn hóa. Không chọn winner, không tính tổng, không khóa RQ hoặc thuật toán.
- `FACT` là sự thật có nguồn trong đúng phạm vi; verdict là **TASK-C INFERENCE / CANDIDATE**, không phải quyết định của Minh. `OPEN` chỉ đầu vào chưa có, không thay cho phán quyết về giới hạn đã xác minh.

## 1. Nguồn và hiệu lực

| Khóa | Tạo tác và phần dùng |
|---|---|
| S | Yêu cầu Task C gốc, `C:/Users/84583/.codex/attachments/22e07417-e07b-42f3-a60f-793c63c2aec7/Pasted text.txt`, §15, §17–20, §24, §27–29 |
| U | [Normalized universe](task-c-normalized-candidate-universe.md), toàn văn; C1–C5 và ánh xạ 12 đề xuất |
| L | [Evidence ledger](task-c-evidence-ledger.md), toàn văn; lớp nguồn và giới hạn mẫu |
| TV | [Targeted verification](task-c-targeted-verification.md), toàn văn TV-01–04 |
| B | [Task B CLOSED](../dataset-audit/TASK-B-RCAEval-audit.md), §12.1–12.20 có hiệu lực; không dùng phần lịch sử để đảo kết luận CLOSED |
| A | [Task A](D:/Project/flash-ticket-platform/docs/research-rca/task-a-ban-do-bang-chung-doc-lap.md), trực tiếp đối chiếu §I–L; pipeline qua L/TV và hợp đồng reviewer |
| C/D/E/F | [Reviewer C](phase-1-independent-candidates/reviewer-c.md), [D](phase-1-independent-candidates/reviewer-d.md), [E](phase-1-independent-candidates/reviewer-e.md), [F](phase-1-independent-candidates/reviewer-f.md), các hợp đồng CC-01/02, CD-01/02, CE-01/02, CF-01/02 |
| LG / EC | [Literature gate](task-c-literature-positioning.md) và [evidence cross-review](task-c-evidence-cross-review.md), đọc để đối chiếu kết luận sau phân tích gate ban đầu; không phải nguồn sinh ứng viên mù |
| P | Hiến pháp, skill govern-capstone-work/reference authority; [DT18](D:/Project/flash-ticket-platform/docs/evidence/project-direction/2026-09-18-de-tai-va-nhiem-vu.md) và [roles](D:/Project/flash-ticket-platform/docs/project/roles.md) |

Đây là kiểm tra độc lập về diễn giải feasibility, không phải raw audit độc lập. Không nhận đã đọc lại toàn bộ Task A/11 báo cáo Task B trong lượt gate này; dùng nguồn CLOSED/ledger đã ingestion và hợp đồng cụ thể. Không download, install, baseline execution hoặc dataset audit mới. Chỉ ghi supporting file do S §29 chỉ định; canonical project vẫn là `D:/Project/flash-ticket-platform`.

**Hiệu chỉnh áp dụng:** TV-04 không chứng minh MicroRank phải chờ thêm năm phút sau alert; trace-volume sensitivity và overhead đã có prior. EC-07: root labels evaluation-only, không được train/tune mô hình bằng chúng, kể cả để bảng supervised riêng. EC-09: thuật toán/metric/LLM cụ thể theo yêu cầu Task C hiện hành, không gán là nguyên văn thư 22/08. DT18 là xác nhận của Minh, không tự là thư mới của giảng viên.

## 2. Ràng buộc chung đã xác minh

1. **FACT — B §12.4/9, L M-001:** 90 ca = năm root service × sáu fault × ba repetition, một collection. Span/window/cutoff/seed không tăng số incident độc lập. Ba repeats không bảo đảm thống kê subgroup mạnh; 30 nhóm service×fault cũng chưa được chứng minh độc lập giữa campaign/workload.
2. **FACT — B §12.6/7/9:** 67.345.051 span, 27 service, 161 cặp service-operation là union audit. Full-case candidate sets có 20–27 literal services, chứa nhãn root ở 90/90 ca. Đây không là quyền dùng union test vocabulary/topology và không chứng minh prefix coverage.
3. **FACT — B §12.6/7/11:** chỉ resolved same-trace parents thành cạnh. Resolution tổng 98,45274372%, bảy ca dưới 90%, thấp nhất 38,54287289%. Giữ ca khó; không điền cạnh từ kiến trúc/đáp án. Resolution không là topology recall hay cơ chế missingness.
4. **FACT — B §12.9/12/17:** root-service GT có; operation/resource/affected-node/path GT không có. Không dùng nhãn root chấm operation accuracy, node/service anomaly F1 hoặc causal-path correctness.
5. **FACT — B §12.4–6/13:** metrics/traces hiện diện ở 90 ca, logs ở 89. Schema trace được kiểm full-90; metric/log profile và joins chỉ được kiểm ở mẫu. B2B 271.919 log rows khớp metric bins là riêng một ca; không full-89 verification. “Normal log-bearing case” không có nghĩa healthy-only control. L–M trực tiếp chỉ exact entity-second bin; M–T/L–T chỉ service+time, không request/event correlation.
6. **FACT — B §12.10:** root/fault chỉ evaluation; cấm path/case ID/root text và metadata/file-level normal–fault timestep counts, full-case end/duration/counts làm feature. Không dùng aggregate từ tương lai/toàn ca cho một prefix hoặc detector. **Số đếm telemetry tính chỉ trong cửa sổ/history được phép vẫn có thể là local feature hợp lệ**, cấp như nhau cho các comparator; không đồng nhất chúng với oracle metadata. `inject_time` chỉ boundary ngoài cho known-window RCA; cấm detector dùng trực tiếp hoặc qua midpoint/warm-up chọn từ lịch injection.
7. **FACT — B §12.2, L M-009:** full-trace audit dùng range reads, không giữ corpus 90 trace mới tại máy. JSON audit không thay model-ready telemetry. Authorized pinned retrieval và loader validation còn là công việc thực nghiệm tương lai.
8. **FACT — P:** Minh phụ trách chính RCA đồng thời lead/nền tảng; không giả định bốn người RCA toàn thời gian. Public experiment đi trước FlashTicket application/evaluation. Ranking không thay detector evaluation hoặc kiểm tải/thông lượng/nhất quán giao dịch của DT18.

**Phạm vi thí nghiệm chính đề xuất: toàn bộ 90 ca RE2-TT ở revision đã pin.** Thiếu logs không loại ca khỏi trace/metric experiment chính. Giữ low-coverage cases, missing-target prefixes, lỗi chạy/timeout trong mẫu số và báo cáo thất bại. Logs là evidence phụ có availability rule. Loader không đọc được dữ liệu phải báo đúng phạm vi; không dùng tập con “sạch” rồi gọi all-90. Chưa có kết quả mô hình hoặc loader toàn quần thể metric/log.

## 3. Mười câu hỏi hard gate cho từng ứng viên

“Có” dưới đây nghĩa dữ liệu đủ cho task hẹp đã nêu, không có nghĩa phương pháp đã chạy hay có hiệu quả.

### C1 — Thông tin quan hệ service ngoài bằng chứng cục bộ

| # | Câu hỏi §15 | Phán quyết có căn cứ |
|---:|---|---|
| 1 | Input có không? | **Có cho trace + metric contract phù hợp**: hiện diện ở 90 ca, cùng local evidence giữa nhánh. Trace schema full-90; không suy metric/log compatibility vượt mẫu (B §12.4–6/12). Logs không là điều kiện sống. |
| 2 | Graph có không? | **Có observed graph**: literal services và resolved parent relationships đủ graph/no-graph/structure controls; không cần complete topology (B §12.7/15). |
| 3 | GT có không? | **Có root service/ca**, evaluation-only; không structural/affected-region truth (B §12.9). |
| 4 | Output chấm được không? | **Có** service rank, paired MRR/Hit@k; không dùng rank để chấm graph correctness. |
| 5 | Universe quan sát không leakage? | **Có toàn ca**, 20–27 services từ permitted telemetry; cấm năm injected targets. Nếu giới hạn horizon, dựng từ phần hợp lệ và chấm target vắng là miss. |
| 6 | Có oracle không? | **Boundary oracle có khai báo của known-window task**. `inject_time` không là feature; labels không vào score, graph, control selection hoặc tuning. Không gọi end-to-end detection. |
| 7 | Metric diễn giải đúng không? | **Có cho injected-root rank**; không chứng minh detector, causal mechanism, explanation correctness; single-root NDCG không đo severity (A §J). |
| 8 | Graph semantic có căn cứ không? | **Có** trace-derived service relationships; không CALLS/USES/causal propagation (B §12.7). Perturbed graph là control thông tin, không can thiệp hệ thật. |
| 9 | Thiếu telemetry làm test vô hiệu không? | **Không** cho observed-graph task: cùng missingness giữa paired controls, giữ bảy ca khó. Low/high resolution strata không là can thiệp nhân quả về missingness. |
| 10 | Dataset hai bắt buộc hay hữu ích? | **Hữu ích, không bắt buộc** cho RE2-TT claim. Muốn suy rộng cần dữ liệu hệ khác; FlashTicket validation bắt buộc cấp DT18, không vì thiếu nhãn ranking hiện tại. |

**Gate: SURVIVES WITH RESTRICTED CLAIM.** Chấp nhận known-window service-root ranking với matched-local-evidence relations contrast. Không detector/causality claim. Có thể qua red team như empirical RQ tiềm năng, chưa bảo đảm đóng góp đủ cho luận văn.

### C2 — Giá trị graph theo ngân sách event-time

| # | Câu hỏi §15 | Phán quyết có căn cứ |
|---:|---|---|
| 1 | Input có không? | **Có cho event-time replay**: timestamps/duration và metric time; không collector-arrival evidence. Completed-span availability phải công khai, không dùng duration tương lai (B §12.6; CD-02/CF-02). |
| 2 | Graph có không? | **Có trong prefix hợp lệ** từ resolved parents. Không full-case/cross-case union cho cutoff sớm; graph prefix thiếu/rỗng vẫn là outcome hợp lệ. |
| 3 | GT có không? | **Có root service và injection boundary**; không nhãn earliest diagnosable time, true onset hoặc safe stopping (B §12.9/12). |
| 4 | Output chấm được không? | **Có** quality trajectory/coverage/runtime. Root vắng nhận miss/RR=0; audit chưa có prefix-coverage distribution nhưng điều này không ngăn chấm hợp lệ. |
| 5 | Universe quan sát không leakage? | **Có** từ telemetry/reference hợp lệ tại cutoff, cùng policy giữa comparator. Full-case target presence không dùng thêm root sớm. Conditional-on-visible chỉ metric phụ có denominator. |
| 6 | Có oracle không? | **Known-window boundary oracle công khai**; cấm future graph/scaler/features và label tuning. Time-to-correct-rank hồi cứu dùng GT để mô tả, không thành online stopping policy. |
| 7 | Metric diễn giải đúng không? | **Có** quality theo event-time budget, runtime riêng. Không MTTD/MTTR/production latency. Curve summary/cutoffs tiền đăng ký; cutoff là repeated measures, không independent N. |
| 8 | Graph semantic có căn cứ không? | **Có** observed parent relations tại cutoff; graph tăng theo thời gian không chứng minh đã phục hồi propagation. |
| 9 | Thiếu telemetry làm test vô hiệu không? | **Không** khi coverage failures được giữ. Ít evidence do cutoff khác missing trace không rõ cơ chế. Prefix root luôn vắng có thể làm câu trả lời quá mỏng, không là lý do xóa ca. |
| 10 | Dataset hai bắt buộc hay hữu ích? | **Hữu ích cho external validity**, không cần cho event-time RQ. Claim operational latency **REQUIRES FLASHTICKET CONTROLLED VALIDATION** có arrival/alert/fault timing độc lập; không tạo yêu cầu hệ thống ở Task C. |

**Gate: SURVIVES WITH RESTRICTED CLAIM.** Chấp nhận graph-value × evidence-budget sau known incident, không autonomous detection/safe stopping. TV-03/04 đã loại novelty của window/trace-volume/runtime sweep đơn thuần; controls phải gồm matched cutoffs, candidates và coverage-inclusive effect.

**C2 estimand/falsification:** chênh lệch graph–control phải được kiểm xem có thay đổi có ý nghĩa theo budget hay không, trên miền tiền đăng ký và với uncertainty/cost/coverage controls. Gain dương nhưng gần như hằng qua budget chỉ hỗ trợ main effect của C1, không tự hỗ trợ H1 interaction của C2. Chênh lệch bằng không, không biến thiên thực dụng hoặc biến thiên chỉ do leakage/coverage-selection không hỗ trợ H1 C2; uncertainty rộng vẫn là chưa kết luận.

### C3 — Operation identity làm biểu diễn trung gian

| # | Câu hỏi §15 | Phán quyết có căn cứ |
|---:|---|---|
| 1 | Input có không? | **Có** literal `(serviceName, operationName)` ở full-90 traces, cùng observations/metric inputs cho coarse/fine. 161 cặp là union audit, không test-derived vocabulary (B §12.6/7). |
| 2 | Graph có không? | **Có** coarse service graph và finer representation/membership từ cùng resolved spans; không suy semantic endpoint từ GET/POST. |
| 3 | GT có không? | **Có cho service output, không cho operation output.** Thiếu operation GT không giết representation experiment; giết operation-localization accuracy (B §12.7/9). |
| 4 | Output chấm được không? | **Có nếu mỗi service chỉ một rank**; không lặp service theo số operations và không gán mọi operation của root là positive. |
| 5 | Universe quan sát không leakage? | **Có** cùng service universe cho coarse/fine; operation nodes từ allowed telemetry, không chọn theo root/fault. |
| 6 | Có oracle không? | **Known-window boundary khai báo**; không pseudo-GT/LLM labels, label-based aggregation/tuning, hoặc operation selection bằng đáp án. |
| 7 | Metric diễn giải đúng không? | **Có service-rank/cost**, không operation accuracy, multilevel localization accuracy hoặc đúng semantic operation. |
| 8 | Graph semantic có căn cứ không? | **Có literal identities/parent relations**, không semantic identity ổn định giữa hệ/version (B §12.7). |
| 9 | Thiếu telemetry làm test vô hiệu không? | **Không**: paired representations cùng records; giữ low coverage. Sparsity/operation count là confounders, không cớ repair. |
| 10 | Dataset hai bắt buộc hay hữu ích? | **Không cần** cho coarse-output contrast; hữu ích để kiểm phụ thuộc naming. Đổi thành operation-root task thì RE2-TT **REJECT — NOT EVALUABLE**; cần supplemental dataset có operation GT hoặc controlled validation tương ứng được duyệt, không chế nhãn. |

**Data gate: SURVIVES WITH RESTRICTED CLAIM. Thesis gate: hạ thành thí nghiệm phụ, không giữ primary direction.** Lý do không phải thiếu operation GT cho service output. A §I/L và LG đã có operation representations; C3 hiện chưa nêu điều kiện unresolved vượt aggregation/capacity ablation. Không cứu bằng thêm nodes/semantic types hoặc hứa thu operation GT — đó là đổi task.

### C4 — Contextual scoring so với graph chỉ ở ranking

| # | Câu hỏi §15 | Phán quyết có căn cứ |
|---:|---|---|
| 1 | Input có không? | **Có** cùng traces/metrics/history; graph được phép thay scorer, khác C1 giữ local score cố định (U; CE-02). |
| 2 | Graph có không? | **Có observed service graph**. Baseline cần causal metric DAG/resource topology thì graph đó **không có**: khai adaptation hoặc bỏ exact reproduction, không dựng giả (B §12.7/8). |
| 3 | GT có không? | **Có root service**, không symptom/affected labels để đo trực tiếp “phân biệt root và triệu chứng” (B §12.9). |
| 4 | Output chấm được không? | **Có** paired service rank theo case/scenario; internal node scores không là endpoint detector đã chấm. |
| 5 | Universe quan sát không leakage? | **Có** cùng telemetry-derived service universe; không prior năm targets. Scenario split là evaluator grouping, không input feature. |
| 6 | Có oracle không? | **Known-window boundary công khai**; cấm root/fault fitting/tuning, future topology, GT context selection. Không đổi supervision giữa nhánh rồi quy gain cho stage. |
| 7 | Metric diễn giải đúng không? | **Có root rank**, không symptom P/R, causal discrimination/AD quality. Held-out fault khác held-out root; không gộp thành “unseen” mơ hồ. |
| 8 | Graph semantic có căn cứ không? | **Có predictive context**, không causal-parent assumptions hay sufficiency của CIRCA nguyên bản. |
| 9 | Thiếu telemetry làm test vô hiệu không? | **Không** cho observed-graph test; missing parents giới hạn context. Giữ coverage/failures và local/late-graph controls. |
| 10 | Dataset hai bắt buộc hay hữu ích? | **Hữu ích, không bắt buộc** cho held-out-scenario service rank. Split một deployment không là cross-system validation; FlashTicket vẫn theo DT18. |

**Data gate: SURVIVES WITH RESTRICTED CLAIM. Thesis gate: hạ thành thí nghiệm phụ, không giữ primary direction.** Stage contrast có thể giải thích RQ khác nhưng contextual scoring/late ranking/graph ablation/unseen evaluation đã có prior. Gắn held-out split không tự tạo gap. Không đổi MRR thành chứng cứ triệu chứng hoặc graph detector.

### C5 — Giá trị graph ở detector và ranker, hai endpoint

| # | Câu hỏi §15 | Phán quyết có căn cứ |
|---:|---|---|
| 1 | Input có không? | **Có system-time telemetry/service rank input**, không independent arrival/onset/healthy-workload corpus. Detector dùng observable history; không chọn normal reference bằng injection timing (B §12.10/12). |
| 2 | Graph có không? | **Có observed graph tại thời điểm hợp lệ**. Muốn gọi graph-conditioned detector phải làm graph tác động score; graph chỉ đổi rank không kiểm H1 detection (A §D; CF-01). |
| 3 | GT có không? | **Có injection-regime và root-service GT; không independently labelled onset, affected-service GT hay independent normal operating regimes đại diện.** Prefix trước injection không thay healthy-only controls. |
| 4 | Output chấm được không? | **Có task hẹp**: system-time injection agreement, root rank, pipeline misses. **Không** true-onset accuracy, node/service anomaly F1 hoặc production false-alarm rate. |
| 5 | Universe quan sát không leakage? | **Có** telemetry candidates cho rank; detector unit là system-time bin, không năm root nodes. Detector miss/target absence phải giữ trong whole-case result. |
| 6 | Có oracle không? | **Detector block cấm oracle**: inject_time, midpoint 720 giây, metadata full-case duration/counts hoặc calibration boundary suy từ injection metadata. Counts/duration telemetry chỉ hợp lệ khi đã quan sát trong history được phép. Known-window block riêng được dùng boundary để cô lập ranker, không nhập vào detector-triggered performance. |
| 7 | Metric diễn giải đúng không? | **Có P/R/F1 injection-regime agreement**, không true-anomaly P/R/F1. MRR/Hit@k riêng; báo conditional-on-detection và whole-case failures. Rank gain không chứng minh detector gain. |
| 8 | Graph semantic có căn cứ không? | **Có trace-derived context**, không causal graph/complete topology/affected region truth. |
| 9 | Thiếu telemetry làm test vô hiệu không? | **Missing links/logs không giết task hẹp** khi giữ ca. **Thiếu onset/normal regimes làm operational detection claim không hợp lệ**; LLM/mô hình thêm không bù GT. |
| 10 | Dataset hai bắt buộc hay hữu ích? | **Không cần** cho injection-regime task. Claim vận hành **REQUIRES FLASHTICKET CONTROLLED VALIDATION** có healthy-load controls và nhãn độc lập; supplemental public dataset phù hợp có thể bổ sung nhưng không thay DT18 FlashTicket. Không dataset mới nào được chọn/audit tại đây. |

**Data gate: SURVIVES WITH RESTRICTED CLAIM** cho injection-regime experiment. **REQUIRES FLASHTICKET CONTROLLED VALIDATION** cho operational detection claim. **Thesis gate: hoãn khỏi primary shortlist hiện tại**, vì task hẹp chấm được không tự thành gap, còn claim rộng thiếu evidence và tăng scope. LG cũng thấy graph AD/joint AD-RCL đã có prior và C5 chưa nêu điều kiện khoa học đủ riêng. Không dùng “sẽ có FlashTicket” để bảo đảm survivor; giữ đánh giá injection-regime như phần phụ nếu RQ được chọn thật sự cần. Hoãn C5 như RQ không bỏ chức năng detection đã duyệt trong DT18.

## 4. Mười ba chiều thesis feasibility — lý giải định tính

Không chấm điểm hoặc tổng trọng số; thứ tự ID trung tính. Complexity/cost là suy luận theo hợp đồng, không benchmark đã đo. Các chiều §24 về question clarity, unresolved evidence, evaluation validity và baseline fairness được nêu thêm tại §3/5–6.

| Chiều §17 | C1 | C2 | C3 | C4 | C5 |
|---|---|---|---|---|---|
| Scientific validity | Estimand thông tin quan hệ rõ nếu local evidence cố định; cần controls capacity/degree/smoothing | Estimand graph-value × budget rõ; availability/coverage là phần bắt buộc, không tuning cửa sổ đẹp | Service endpoint hợp lệ; operation count/capacity/aggregation bias có thể giải thích gain | Stage contrast chấm được nhưng đổi scorer tạo capacity confound; không đo triệu chứng | Hai endpoint hợp lệ khi tách block; detector construct chỉ injection agreement |
| Dataset fit | Observed relation + root GT đúng task; logs phụ | Timestamps/root GT đúng event-time task; early coverage là output chưa đo | Literal pairs/membership đủ; không semantic operation truth | Graph context đủ, causal/resource graph nguyên bản có thể thiếu | Ranking fit; detection fit một phần, thiếu normal diversity/onset |
| Ground-truth quality | Published injected service đủ chấm, không causal validation độc lập | Cùng root GT; boundary oracle công khai; không earliest-correct GT | Đủ coarse target; fine target hoàn toàn thiếu nhưng không cần cho task này | Root GT đủ; affected/symptom GT thiếu | Root GT có nghĩa rõ hơn detector-regime labels; regime không observed onset |
| Baseline availability | Local/statistical + graph controls có đường triển khai; exact adapters/runtime OPEN | Known-window/local/graph families có, phải replay cùng cutoff | Coarse/fine variants có đường thực hiện; service adapter và fairness tốn công | Local/late/context họ đã có; exact CIRCA/Eadro không mặc nhiên tương thích | Local unsupervised families khả dĩ; root-supervised implementations không được train theo B policy |
| Experimental complexity | Vừa: paired structure controls, scenario grouping, coverage strata | Vừa–cao: dependent curves, time censoring, multiplicity và cost separation | Vừa: paired representation, operation-count/cost controls | Vừa–cao: stage/feature/capacity controls và scenario separation | Cao: detector/ranker blocks, misses nối tiếp; thêm controls nếu claim vận hành |
| Implementation complexity | Vừa: common evidence pipeline/evaluator và graph controls | Vừa–cao: temporal loader/replay, completion semantics, cache provenance | Vừa: finer representation và service aggregation; không operation labeler | Vừa–cao: thay scorer/ranker mà giữ evidence, adapter fidelity | Vừa–cao tới cao: hai evaluators và integration; không buộc deep model |
| Compute cost | Trace I/O/aggregation có thể lớn hơn rank trên vài chục nodes; controls nhân chi phí | Nhiều cutoff dễ nhân preprocessing; cần reuse hợp lệ theo thời gian | Nhiều intermediate nodes/features; 161 union không là size mỗi case | Tuning/repeated controls có thể chi phối; small graph không đồng nghĩa rẻ | Detector bins + ranking + conditions; controlled runs tốn công ngoài public corpus |
| Reproducibility | Pin retrieval/hash/split/features/controls/seeds/per-case outputs; audit JSON không corpus | Thêm cutoff/availability/censored failures và cost accounting | Thêm literal mapping, mỗi service một rank, aggregation provenance | Thêm stage/matched-budget/adaptation manifests | Thêm calibration provenance, actual-trigger vs oracle block và independent control protocol |
| Risk of dead end | Vừa–cao: chỉ là graph ablation thường hoặc capacity/degree artifact | Vừa–cao: chỉ “nhiều dữ liệu tốt hơn”, early root vắng, fake-online claim | Cao làm primary: prior representation mạnh; gain có thể do extra features | Cao làm primary: gần prior, không symptom labels, fairness khó | Cao làm primary detector: schedule shortcut, thiếu independent validation, nhiều việc cho Minh |
| Supervisor alignment | Graph reasoning/baseline RCA phù hợp; chưa đánh giá detector | Graph reasoning và evidence budget phù hợp; chưa detection | Hỗ trợ representation, chưa có output đóng góp riêng | Context score phù hợp graph use nhưng MRR không chứng minh AD | Gần chuỗi detection/ranking; mức phù hợp không vượt qua literature/GT gate |
| FlashTicket transfer value | Kiểm quan hệ còn hữu ích trên hệ đích; không đổi kiến trúc để có effect | Kiểm evidence timing/overhead; arrival claim cần timing độc lập | Kiểm có đáng giữ operation detail qua service outcome, không bắt operation GT | Kiểm context utility dưới tải khác, không causal interpretation | Controlled normal/fault runs cần cho operational claim; không thay system load/transaction evaluation |
| LLM integration compatibility | Ranked evidence + coverage, giải thích sau | Thêm cutoff/availability; không chọn thời điểm “đúng” | Operation evidence chỉ hypothesis phụ | Giải thích context/local evidence, không xác nhận causal root | Giải thích flag và rank riêng; không sửa nhãn/rank hộ |
| Scope controllability | Một RQ, ít controls có lý do; không tái lập mọi method | Một miền budget tiền đăng ký; không online stopping/streaming platform | Dễ giữ như ablation phụ; primary dễ mở quá phạm vi để đủ đóng góp | Stage ablation phụ có ích; primary dễ thành nhiều scorers/frameworks | Chỉ giữ task hẹp hoặc chấp nhận controlled study qua quyết định riêng; không ghép mọi module làm contribution |

**Compute reality:** chưa có measurement CPU/GPU/RAM/wall-clock hoặc budget công được xác nhận. Không cam kết chạy nhanh trên laptop, không cần GPU với mọi baseline hoặc thời hạn hoàn thành. RQ không bắt GPU; baseline tương lai có thể có yêu cầu riêng. Phải tính pinned retrieval, preprocessing/caches, controls/repeats và evaluator; 67 triệu span không nằm sẵn thành corpus đầy đủ local, cũng không là 67 triệu mẫu thống kê. Không lấy graph service nhỏ để bỏ qua I/O.

**Nhân sự:** một RQ chính do Minh chịu trách nhiệm, phối hợp observability/FlashTicket theo phân công hiện hành; không lập kế hoạch bốn người RCA toàn thời gian. Budget máy, số tuần công và mức controlled validation là `OPEN` do Minh quyết. Những đầu vào này không làm các giới hạn dữ liệu đã biết trở thành chưa rõ.

## 5. Question clarity, đóng góp và vai trò sau gate

| ID | Evidence of unresolved problem và đóng góp tối đa hiện có | Phán quyết vai trò |
|---|---|---|
| C1 | TV-01/02/04 chứng minh graph ablation, unseen testing và structural sensitivity đã có. Contrast hẹp giữ local evidence/universe và kiểm topology/capacity nuisance vẫn là empirical question cụ thể; không thấy câu trả lời đầy đủ trong pack không chứng minh literature-wide absence | **Giữ có giới hạn để red team xét**, `DEFENSIBLE BUT INCREMENTAL` theo LG. Bỏ primary nếu chỉ graph-on/off replication hoặc không làm được controls hợp lệ. Chưa đủ căn cứ gọi NOVEL |
| C2 | TV-03/04 đã có boundary/volume/runtime tests. Câu hỏi riêng là graph-value thay đổi theo shared cutoff ra sao, tính cả coverage/processing, khác “thêm dữ liệu tốt hơn” | **Giữ có giới hạn để red team xét**, incremental event-time study. Hạ thành sensitivity nếu chỉ tune window/profile runtime; không hứa real-time hoặc early detection |
| C3 | A §I/L đã có operation/finer representations; formulation hiện tại chưa chỉ ra unresolved condition ngoài coarse/fine aggregation/capacity ablation | **Không primary; chỉ optional secondary experiment.** Data-feasible không đồng nghĩa thesis-worthy. Không cần operation GT để cứu coarse-output RQ; thu GT mới sẽ đổi task |
| C4 | Context scoring và late graph đã có; scenario split là validity requirement. Stage comparison chưa tự là research gap và có scorer/capacity nuisance khó tách | **Không primary; chỉ optional secondary experiment.** Không gộp lén C1 vì C4 thay local scoring. Không claim tách root/symptom từ MRR |
| C5 | Graph AD/joint AD-RCL đã có; hai endpoint và error-propagation evaluation là đúng phương pháp nhưng chưa đủ gap riêng. RE2-TT chỉ chấm regime, thiếu evidence phát hiện vận hành | **Hoãn primary direction hiện tại.** Có thể là evaluation phụ injection-regime; muốn mở lại cần câu hỏi đủ riêng, nguồn GT và scope được quyết lại. FlashTicket dự kiến không bảo đảm contribution |

Đây là phán quyết nghiên cứu ở trạng thái CANDIDATE, không tự duyệt/khóa quyết định. Không giữ số lượng hướng bằng quota. C1/C2 là các lựa chọn thay thế với estimand khác; không giao Minh làm cả hai và không tính cùng một kết quả thành hai đóng góp. C3/C4 giữ trong universe, hạ vai trò có lý do, không bị merge ngầm. Secondary experiment cũng tốn công và chỉ thêm nếu giải thích threat/ablation cần cho RQ được chọn.

## 6. Fairness, falsification và điều kiện dừng

**Chính sách nhãn có hiệu lực cho cả năm ứng viên:** root/fault ở evaluator để thiết kế/phân tầng split và chấm sau freeze. **Không root/fault-label fitting, supervised training, label-based model tuning hoặc calibration bằng đáp án**, kể cả đặt một bảng supervised riêng. Eadro/DéjàVu có thể là closest prior; không mặc nhiên là comparator được phép train với các nhãn này. Muốn đổi policy cần quyết định con người riêng và experimental design mới. CE-02 câu “supervised nếu đủ label budget/bảng riêng” không được áp vào synthesis vì trái B §12.10 và EC-07.

Fair internal ablation khác whole-method comparison. Baseline nguyên bản cần host/resource/causal-metric mapping hay operation output không thể mặc định chạy nguyên bản trên RE2-TT. Khai rõ service-output/resource-free adaptation; không tạo kiến trúc/GT để giữ tên paper. Không lấy số ở collection khác làm benchmark trực tiếp. Exact runnable implementations/runtime còn OPEN; sự không tương thích của một baseline không tự giết problem-level RQ nếu còn controls phù hợp.

| ID | Control và điều kiện H1 không được hỗ trợ |
|---|---|
| C1 | Cùng local evidence/universe/budget; graph controls phải có nuisance assumptions công khai, không chọn theo nhãn. Gain biến mất dưới controls hoặc không khác lợi ích capacity/degree thì không hỗ trợ relational-information H1 |
| C2 | Cùng cutoff/reference/universe, không duration/graph/normalizer từ tương lai; target vắng vẫn miss. Không có biến thiên graph-value thực dụng theo budget, biến thiên mất sau controls hoặc phải chọn cutoff đẹp từ test thì không hỗ trợ H1 interaction. Một endpoint tốt tự nó không đủ; lợi ích chỉ xuất hiện muộn vẫn có thể là kết quả về điều kiện hoạt động nếu thuộc miền tiền đăng ký. Time-to-correct chỉ hồi cứu, không policy dừng |
| C3 | Cùng records, mỗi service một rank, kiểm operation count/capacity/aggregation/cost. Gain chỉ nhiều features hoặc bias service nhiều operations không hỗ trợ granularity-information H1; không chuyển sang operation accuracy |
| C4 | Local-only, local+late-graph và context conditions phải tách input/capacity/supervision. Thắng do baseline thiếu required graph hoặc model lớn hơn không chứng minh stage utility. Không giữ primary khi không làm được fair contrast |
| C5 | Không injection-based normal/reference selection hoặc midpoint shortcut; tách known-window oracle block và actual-trigger block. Chỉ rank tăng, graph không đổi detector score, hoặc gains nhờ timing shortcut không hỗ trợ detector H1. Detector misses phải nằm whole-case outcomes |

Mức practical effect, metric chính, k, curve summary, exact cutoff/threshold/formula/architecture và policy ties/failure để Task D sau C Phase 2; không chọn số tại đây. Estimate quá bất định là chưa kết luận, không chứng minh H0; không-significant difference không đủ claim equivalence. Split theo incident và kiểm scenario/repeat dependence; không rải windows/prefix cùng incident qua train/test. Intervals cần nêu estimand/sampling assumptions, không lấy hàng triệu spans hay random seeds để che chỉ ba repeats và một deployment.

## 7. Trace, operation, LLM và supplemental data

| ID | Trace missingness role | Operation role | Dữ liệu bổ sung thực sự cần |
|---|---|---|---|
| C1 | SECONDARY ROBUSTNESS ANALYSIS; không repair | NOT USED trong RQ chính | Không dataset hai cho RE2-TT claim; FlashTicket theo DT18 |
| C2 | KNOWN LIMITATION + SECONDARY ROBUSTNESS ANALYSIS; thiếu evidence do cutoff không tự là trace corruption | NOT USED làm biến RQ chính | Arrival/alert timing độc lập nếu claim vận hành; không cần để chấm event-time curve |
| C3 | SECONDARY ROBUSTNESS ANALYSIS | INTERMEDIATE REPRESENTATION; quantitative target luôn service | Không cần operation GT cho task hiện tại; không mở operation localization |
| C4 | SECONDARY ROBUSTNESS ANALYSIS | NOT USED làm biến chính; nếu cần chỉ SECONDARY EVIDENCE và matched giữa nhánh | Không dataset hai cho held-out-scenario rank; thiếu symptom/causal GT không được bù bằng suy diễn |
| C5 | SECONDARY ROBUSTNESS ANALYSIS | NOT USED làm target; chỉ SECONDARY EVIDENCE nếu input contract cần | Independent normal-load/failure/onset evidence để claim operational detection; thiết kế/nguồn phải được phê duyệt sau, không buộc ngay ở Task C |

LLM nhận structured evidence **sau** detector/ranker, nêu coverage/cutoff/limits, không sinh/chỉnh GT, không thay ranker, không tự kết luận root cuối hoặc tự sửa hệ thống. C3 operation evidence chỉ giả thuyết giải thích, không quantitative operation diagnosis. LLM compatibility không là contribution hoặc điểm cộng khoa học tự động.

Không sửa trace/topology theo nhãn; không đổi số service/Saga/kiến trúc FlashTicket để phù hợp RQ. Không lấy public data thay kiểm chứng FlashTicket, cũng không buộc FlashTicket giải cứu operation/causal claims ngoài task được chọn.

## 8. Handoff và tự kiểm

- **Decision states:** không có DECIDED/USER_CONFIRMED mới. Tất cả verdict là CANDIDATE review; primary research decision vẫn thuộc Minh. C1/C2 chỉ qua restricted gate; C3/C4 secondary; C5 deferred primary.
- **Giả định:** authorized pinned retrieval, telemetry-only fitting và fair adapters tương lai theo Task D/E. Không giả định corpus local sẵn, baseline đã chạy, prefix coverage, scenario independence hay independent onset/normal GT.
- **Tệp duy nhất ghi:** `D:/Project/flash-ticket-rca-research/task-c/task-c-feasibility-gate.md`. A/B, sáu reviewer gốc, raw/manifests, code, indexes và decision register không sửa.
- **Kiểm tra nội dung:** đủ 10 câu hỏi × 5 hướng, đủ 13 chiều §17, và question/gap/fairness/validity §24; đối chiếu B CLOSED, TV corrections và EC-07/09; rà full-case/prefix, 90-case/mẫu join, oracle/task/metric và label-use policy. Tự đọc toàn file sau ghi. Không baseline/data audit; main chạy integrated governance audit một lần sau cùng.
- **OPEN thật sự:** mức contribution incremental Minh/giảng viên chấp nhận; budget compute/công; mức validation muốn cam kết. Không hỏi lại dataset facts đã đóng băng. Không còn material evidence conflict chưa giải trong phán quyết gate này.
- **Nội dung cho báo cáo chính thức sau duyệt/thực nghiệm:** task/GT alignment, observed graph semantics, matched controls, incident-level inference, coverage/failures, injection-regime/event-time limits, representation khác localization GT, provenance và kết quả âm. Chưa trình bày proposal/gain giả định như kết quả đạt được.

**Kết thúc bounded feasibility review. Không winner, không quota retention, không chuyển Task D hoặc chạy thí nghiệm.**
