# Reviewer C-B — Phản biện định vị literature độc lập

- Trạng thái thực thi: **COMPLETE**; trạng thái nội dung: `CANDIDATE` / `OPEN`, chưa được con người duyệt.
- Ngày: 2026-09-20. Ý định: `EXECUTE`; loại tạo tác: `FORMATION`.
- Phạm vi: phục hồi và hoàn tất riêng C-B theo yêu cầu recovery. Không hợp nhất, xếp hạng hoặc chọn hướng thắng; không đọc bản ứng viên của reviewer khác.
- Lăng kính: công trình gần nhất đã giải gì, câu hỏi nào còn đủ hẹp để kiểm chứng, và vì sao một kết quả có thể không đủ thành đóng góp luận văn.
- Quy tắc quản trị đã áp dụng: `govern-capstone-work`, hiến pháp dự án, DT18 và phân công hiện hành. Không thay yêu cầu hệ thống, quyết định nghiên cứu, Task A/B hay dữ liệu thô.

## 1. Nguồn, mức khẳng định và tính độc lập

Ký hiệu nguồn:

- **A**: `D:/Project/flash-ticket-platform/docs/research-rca/task-a-ban-do-bang-chung-doc-lap.md`, DRAFT, ngày chốt nguồn 2026-09-20.
- **B**: `D:/Project/flash-ticket-rca-research/dataset-audit/TASK-B-RCAEval-audit.md`, CLOSED; **§12 có hiệu lực**, §§1–11 là lịch sử.
- **L**: `D:/Project/flash-ticket-rca-research/task-c/task-c-evidence-ledger.md`.
- **R**: thư mục `D:/Project/flash-ticket-rca-research/audits/rcaeval/`.

`VERIFIED — TASK A/B` là sự kiện được báo cáo trong đúng phạm vi nguồn, không phải tự tái lập paper hay audit. `VERIFIED — MACHINE EVIDENCE` dưới đây chỉ dùng cho JSON đã trực tiếp mở. Mọi đề xuất, H0/H1 và nhận xét giá trị luận văn là `REVIEWER INFERENCE` / trạng thái `CANDIDATE`; điều chưa biết là `OPEN`. Đây là nhãn bằng chứng, không thêm trạng thái quyết định ngoài hiến pháp.

**Provenance đọc thực tế.** Trước recovery đã đọc nội dung Task A, B và các báo cáo B-A đến B-E; recovery dùng ledger trước, rồi mở đúng báo cáo I, J và JSON về coverage/parent resolution phục vụ hai câu hỏi. Các báo cáo F/G/H/resource được dẫn qua ledger và kết luận CLOSED, không tuyên bố C-B đã đọc trực tiếp toàn bộ 11 báo cáo. Đây tuân theo yêu cầu recovery không đọc lại máy móc; main chịu trách nhiệm inventory toàn bộ evidence pack. Không đọc E1, A10, phương pháp sinh viên, trao đổi cũ hay ứng viên của reviewer khác. Không tra cứu web, tải dữ liệu, cài phần mềm, chạy mô hình hoặc sinh thêm reviewer.

### Các ràng buộc quyết định khả năng sống còn

| Mã | Khẳng định và nguồn | Lớp bằng chứng | Giới hạn |
|---|---|---|---|
| CB-E1 | Multimodal graph AD/RCA đã có ở Eadro, TORAI, ARMOR; graph ablation đã có ở Eadro/DéjàVu. A §C.7–C.9, C.12, G, L; L A-003/A-005 | VERIFIED — TASK A | “Thêm đồ thị/ba modality” không tự là đóng góp |
| CB-E2 | MicroRCA cấp cùng detector output cho baseline; MicroRank thu thêm trace sau trigger; RCD/CIRCA/TORAI nhận cửa sổ lỗi; các protocol không đồng nhất. A §C.2–C.8, J.2 | VERIFIED — TASK A | Không suy chênh lệch số liệu giữa paper thành lợi thế phương pháp |
| CB-E3 | A không xác nhận gap nào là STRONG CANDIDATE. A §L/Q; L A-006 | VERIFIED — TASK A | Khoảng chưa mô tả trong survey giới hạn không phải khoảng trống literature-wide |
| CB-E4 | RE2-TT có 90 case = 5 service × 6 fault × 3 repeats, có thời điểm tiêm hợp lệ; root service là target định lượng. B §12.4/12.9/12.12; R I, L M-001 | VERIFIED — TASK B | Không có nhãn onset bất thường độc lập, affected nodes, operation hay causal path |
| CB-E5 | JSON `re2tt-target-candidate-coverage.json`: `case_count=90`, `root_target_present_count=90`, candidate count 20–27 | VERIFIED — MACHINE EVIDENCE | **Full-case coverage**; chưa chứng minh coverage ở prefix hoặc lịch sử trước lỗi |
| CB-E6 | JSON `re2tt-trace-full-subset-audit.json:summary.parent_resolution`: 65,748,095/66,781,374 parent resolve; tỷ lệ 0.9845274372. B §12.6/12.11: 7 case dưới 90% | VERIFIED — MACHINE EVIDENCE cho tổng; VERIFIED — TASK B cho phân tầng | Không là topology recall; giữ low-coverage cases, không phục dựng cạnh |
| CB-E7 | B §12.7/12.15: cạnh chỉ là resolved parent→child trace relation; resource/CALLS/causal semantics không được hỗ trợ | VERIFIED — TASK B | Thí nghiệm kiểm giá trị quan hệ quan sát, không xác nhận causality |
| CB-E8 | B §12.10: path/case/fault/root labels không là model input; inject_time chỉ làm boundary ngoài cho known-window RCA | VERIFIED — TASK B | Không gọi kết quả này là phát hiện end-to-end |
| CB-E9 | JSON full-trace `summary.transfer.retained_telemetry_bytes=0`, 89 remote objects range-read và 1 local reused | VERIFIED — MACHINE EVIDENCE | JSON audit không phải corpus đã sẵn sàng để thực nghiệm 90 case; retrieval thuộc giai đoạn sau |
| CB-E10 | B §12.5/12.13: L–M direct tại exact entity-second bin; L–T/M–T chỉ service+time; 89/90 có logs theo metadata | VERIFIED — TASK B | Không direct request join; join schema chưa audit toàn bộ 89 log cases |

## 2. CB-01 — Giá trị thông tin quan hệ khi kiểm thử tách khỏi kịch bản lặp

**Trạng thái:** `CANDIDATE`. Định vị sơ bộ: **NEEDS TARGETED VERIFICATION**, có thể chỉ là **DEFENSIBLE BUT INCREMENTAL**. Không phải tuyên bố mới.

| Trường contract | Nội dung |
|---|---|
| **CANDIDATE ID** | **CB-01** |
| **Working title** | Giá trị thông tin quan hệ đối với xếp hạng dịch vụ khi kiểm thử tách khỏi kịch bản lặp |
| **Research Question** | Với cùng telemetry, bằng chứng độ lệch cục bộ, tập dịch vụ ứng viên và ngân sách hiệu chỉnh, quan hệ dịch vụ suy từ trace có cải thiện xếp hạng root service trên các nhóm kịch bản tiêm lỗi chưa dùng để lựa chọn/hiệu chỉnh phương pháp, hay lợi ích chủ yếu chỉ xuất hiện khi các lần lặp của cùng kịch bản nằm ở hai phía đánh giá? |
| **Why scientifically interesting** | `REVIEWER INFERENCE`: tách thông tin có ích của quan hệ khỏi lợi thế do đầu vào, label budget và sự giống nhau giữa các lần lặp. Một kết quả âm có thể chỉ ra giới hạn của kết luận “graph giúp”, thay vì buộc phải tạo mô hình mới. Không coi phép chia dữ liệu tự nó là đóng góp; cần một hiệu ứng ổn định hoặc failure condition có giá trị sử dụng. |
| **Closest prior work** | `VERIFIED — TASK A`: MicroRCA (§C.2) đã kiểm localizer với detector output chung; Eadro (§C.7) có w/o GAT; DéjàVu (§C.9) kiểm graph aggregation và recurring failures; BARO (§C.4) là đối chứng deviation không graph; TORAI (§C.8) là RCA đa nguồn không cần service call graph. Không gán causal semantics của TORAI cho trace edges. |
| **Unresolved according to Task A** | A §L để mở controlled test giữ local score/input/candidate cố định; A §F/J.2 nhấn mạnh công bằng label budget và split. A **chưa xác nhận** nghiên cứu gần nhất đã hoặc chưa làm đúng phép đối chiếu grouped scenario này. Hạn chế recurring ở A §C.9 tạo lý do kiểm, không chứng minh gap. |
| **Exact Task-B support** | CB-E4: full factorial cho phép gom ba lần lặp của một service–fault scenario cùng phía đánh giá; fault family có thể dùng cho phân tầng/holdout bên evaluator. CB-E5/CB-E7: graph quan sát và service target có thể đánh giá. B §12.12 cho phép graph ablation. CB-E8 cấm labels đi vào feature/ranker. |
| **Primary experimental unit** | Một incident case tạo một service ranking; so sánh ghép cặp trên cùng case. Cụm phụ thuộc là service–fault scenario và các repeats, không phải span/window. Không coi 90 case là 90 môi trường độc lập. |
| **Input telemetry** | Metric series gắn exact service token và trace fields trong cùng observation budget. Bằng chứng độ lệch cục bộ được giữ nguyên giữa nhánh có/không quan hệ. Logs chỉ là phân tích bổ sung nếu cùng join/availability contract; không để thêm logs trở thành lý do nhánh graph thắng. |
| **Graph role** | Cung cấp quan hệ giữa dịch vụ trong bước reasoning/ranking sau incident window đã biết. Kiểm tác dụng của quan hệ tách khỏi local evidence; không mặc định graph-conditioned detector. Dựng từ resolved same-trace parent links trong phần telemetry được phép, không union toàn bộ test corpus. |
| **Primary output** | Ranked list trên tập literal service quan sát được; cùng universe cho các nhánh trong mỗi case. |
| **Ground truth** | `root_cause_service` dùng bởi evaluator. `fault`/`repetition` chỉ thiết kế split và báo cáo; không huấn luyện root-label model hay chọn candidate theo năm nhãn inject. Không có target anomaly-node/operation. |
| **Expected baseline family** | Đối chứng độ lệch cục bộ không dùng quan hệ, cùng scorer và candidate set; các họ graph ranker/root-blind statistical RCA để kiểm ngoài một implementation. Benchmark method bên ngoài có input/supervision khác chỉ được báo riêng, không dùng để quy phần thắng cho graph. Không chọn thuật toán cụ thể. |
| **Evaluation family** | MRR và Hit@k theo case; uncertainty theo cụm scenario, kết quả theo fault family/root service và coverage. So sánh lợi ích ghép cặp giữa graph/no-relation ở protocol tách nhóm; không báo node F1. Dữ liệu cùng kịch bản nằm hai phía chỉ có thể là đối chứng độ nhạy được khai rõ, không là kết quả tổng quát hóa chính. |
| **Null hypothesis H0** | Sau khi giữ input/local evidence/universe/budget và tách kịch bản hiệu chỉnh khỏi kiểm thử, quan hệ trace không tạo mức cải thiện service-ranking có ý nghĩa thực tiễn đã định trước so với nhánh không quan hệ; lợi ích quan sát được không vượt baseline đơn giản một cách ổn định. |
| **Alternative hypothesis H1** | Lợi ích của quan hệ vẫn dương và đạt mức ý nghĩa thực tiễn định trước trên các nhóm kiểm thử tách biệt, không chỉ do một root service, fault family hoặc repeat. Đây là giả thuyết về utility dưới protocol cụ thể, không là causal discovery hay transfer sang mọi hệ. |
| **Falsification condition** | H1 không được hỗ trợ nếu gain biến mất/đảo dấu sau khi giữ nguyên local evidence và grouped evaluation; nếu chỉ một stratum tạo gain; hoặc nếu graph-free comparator đạt tương đương trong uncertainty hợp lý. Không dùng “p không nhỏ” làm bằng chứng H0 đúng; power hạn chế phải ghi inconclusive. Margin/phép kiểm cụ thể thuộc Task D, không chọn ở đây. |
| **Main confounders** | Chỉ năm injected roots, sáu kiểu lỗi; root dịch vụ có thể có fingerprint topology/traffic; scenario repeats có thể cùng workload/collection condition; số candidate, số metric, trace volume và parent resolution khác nhau; calibration/reference histories không đồng chất. Không gọi unseen fault holdout là unseen service/system generalization. |
| **Main leakage risks** | Paths/labels, full-case graph trước cutoff, chọn hyperparameter bằng toàn bộ test labels, split windows cùng incident, chọn graph/universe từ năm roots. Fault labels dùng để group bên evaluator phải bị cách ly hoàn toàn khỏi ranker. Không cho nhánh graph tập ứng viên thuận lợi hơn. |
| **Expected implementation complexity** | Trung bình: phần khó là contract ghép cặp, grouped protocol và tái lập baseline tương thích, không nhất thiết mô hình lớn. Không giả định có bốn người làm toàn thời gian cho RCA; Minh còn chịu nền tảng chung. |
| **Expected dataset risk** | Trung bình–cao: 30 scenario × 3 repeats ít cho kết luận ổn định; test restricted to RE2-TT. Full metrics/log schema không được audit toàn corpus. CB-E9 yêu cầu retrieval có phép sau này; hiện chưa có 90-case runnable dataset. Dataset thứ hai hữu ích cho external validity, **không bắt buộc để kiểm giả thuyết trong RE2-TT**; bắt buộc bổ sung nếu muốn claim cross-system. |
| **FlashTicket transfer relevance** | Kiểm xem trace dependency có đem lợi ích chẩn đoán vượt local telemetry trước khi tăng độ phức tạp tích hợp. FlashTicket là kiểm chứng áp dụng sau public pilot theo DT18; không được suy kết quả TT thành hiệu quả trên FlashTicket, không tạo thêm service/fault chỉ để làm nghiên cứu. |
| **OUT OF SCOPE** | Trace reconstruction; resource graphs; physical causal proof; operation accuracy; end-to-end detector quality; final ranker/model; chọn threshold; mở rộng nghiệp vụ FlashTicket; dùng LLM làm ranker. |
| **Why may NOT be thesis-worthy** | Graph ablation đã phổ biến. Nếu chỉ lặp lại w/o graph trên thêm một snapshot, hoặc chỉ phát hiện split leakage vốn là hygiene, đây có thể là tái lập hữu ích nhưng chưa đủ luận văn. Gain nhỏ/không ổn định hay một pattern phụ thuộc năm root services sẽ làm contribution yếu. Phải được đánh giá như empirical contribution, không gắn nhãn methodological novelty. |

**Trace missingness:** `SECONDARY ROBUSTNESS ANALYSIS`; báo coverage và phân tầng đã quan sát, không nâng thành RQ chính và không repair.

**Operation role:** `NOT USED` như đơn vị biểu diễn bắt buộc; operation không là output hoặc nhãn. **LLM role:** chỉ diễn giải structured ranked evidence ở bước sau; không cung cấp nhãn hoặc thay ranker. **Phù hợp supervisor:** kiểm graph reasoning/RCA trực tiếp, nhưng **không tự hoàn tất** yêu cầu detector đồ thị nếu giảng viên dùng nghĩa nghiêm ngặt; phần đó cần thí nghiệm riêng có label phù hợp.

**OPEN literature cần kiểm đích danh trước survival gate:** A §C.2/C.7/C.9 chưa mô tả đủ tất cả split/ablations của MicroRCA, Eadro, DéjàVu. Cần kiểm đúng phần experimental protocol và supplementary tương ứng: đã giữ local scorer/candidate set đồng nhất và group repeats/scenarios chưa? Nếu đã có cùng câu hỏi, cùng controls và coverage đủ, CB-01 mất định vị; đổi dataset không cứu novelty. C-B chưa thực hiện targeted search trong recovery và không suy “không thấy trong A” thành “chưa có”.

## 3. CB-02 — Lợi ích RCA theo lượng bằng chứng tích lũy sau thời điểm sự cố đã biết

**Trạng thái:** `CANDIDATE`. Định vị sơ bộ: **NEEDS TARGETED VERIFICATION**. Câu hỏi thực nghiệm về thời gian chờ bằng chứng, chưa là đề xuất cơ chế online.

| Trường contract | Nội dung |
|---|---|
| **CANDIDATE ID** | **CB-02** |
| **Working title** | Lợi ích RCA theo lượng bằng chứng tích lũy sau thời điểm sự cố đã biết |
| **Research Question** | Khi các phương pháp được cấp cùng lượng telemetry tính tới cùng mốc sau sự cố đã biết, reasoning từ quan hệ trace có giúp root service xuất hiện sớm trong danh sách xếp hạng hơn đối chứng cục bộ, hay ưu thế ở cuối case chỉ đến từ việc chờ thêm bằng chứng? |
| **Why scientifically interesting** | `REVIEWER INFERENCE`: ranking cuối case tốt chưa trả lời thời điểm nào đủ hữu ích để bắt đầu điều tra. Tách thời gian chờ dữ liệu khỏi thời gian chạy máy; khảo sát đường đánh đổi accuracy–evidence delay có thể thay đổi kết luận về utility mà bảng accuracy/runtime cuối case che khuất. Không mặc định sớm hơn luôn tốt hơn hoặc graph luôn giúp. |
| **Closest prior work** | `VERIFIED — TASK A`: MicroRank (§C.3) thu thêm khoảng năm phút trace sau trigger; CIRCA (§C.6) có reference/delay/test interval; RCD (§C.5) nhận normal/failure samples; TORAI (§C.8) lấy severity sau thời điểm anomaly; BARO (§C.4) có detector latency và ranker runtime rất khác nhau. Eadro/ARMOR (§C.7/C.12) có window/streaming setups. Đây đều là prior gần, không được nói literature bỏ qua thời gian. |
| **Unresolved according to Task A** | A §J.2 yêu cầu cùng unit/protocol; §C mô tả các window khác nhau nhưng không cung cấp một controlled comparison về chất lượng rank theo **cùng cutoff bằng chứng**. Đây là thiếu thông tin của evidence map, **chưa phải kết luận thiếu nghiên cứu**. Câu hỏi sống còn chỉ khi kiểm đích danh literature xác nhận chưa được cô lập đủ. |
| **Exact Task-B support** | B §12.4/12.9/12.12: known-window RCA và service GT được hỗ trợ; metrics có thời gian, traces có timestamps/parent keys theo §12.6/12.15. CB-E5 chỉ xác nhận candidate coverage ở full case; early-prefix coverage là outcome phải đo, không giả định. B §12.10 cho phép boundary ngoài trong đúng tác vụ này. |
| **Primary experimental unit** | Incident case; một đường service-ranking theo các cutoff đã định trước trên cùng case. Các điểm trên đường không phải mẫu độc lập. So sánh ghép cặp theo case và uncertainty theo scenario. |
| **Input telemetry** | Reference telemetry trước boundary và phần metrics/traces đã được quan sát tới cutoff; cùng budget giữa comparator. Logs chỉ thêm nếu contract CB-E10 được đáp ứng, không direct log–span join. Không đưa timestamp injection làm feature; harness chỉ cung cấp ranh giới known incident. |
| **Graph role** | Graph quan sát bằng resolved relations trong lịch sử/prefix được phép dùng cung cấp ngữ cảnh cho service ranking. Có thể phân biệt utility của quan hệ với utility của thêm samples bằng ablation cùng input. Không lấy graph union từ các mốc tương lai hoặc toàn bộ case rồi gọi kết quả early diagnosis. |
| **Primary output** | Service ranking tại mỗi cutoff và đường chất lượng rank theo thời gian bằng chứng. Output khoa học không phải detector alarm, nguyên nhân vật lý hoặc policy tự động dừng điều tra. |
| **Ground truth** | Root service cấp case dùng cho mọi cutoff; inject_time là boundary thí nghiệm bên ngoài. Không có first-symptom/first-observable-root label, vì vậy không đo “độ trễ từ lúc bất thường thật sự xuất hiện”. Không có arrival/ingestion time đầy đủ để chứng minh latency triển khai online. |
| **Expected baseline family** | Statistical/deviation RCA không quan hệ, graph-based service-ranking và các họ known-window RCA có thể nhận cùng budget. Một reference dùng toàn case chỉ là upper-information reference, **không** đối thủ công bằng ở cutoff sớm. Baseline không chạy được ở prefix phải ghi unavailable/failure, không lén cấp future data. |
| **Evaluation family** | MRR/Hit@k theo cutoff với uncertainty theo case/scenario; báo candidate coverage và misses riêng. Đường chất lượng theo thời gian là primary evidence; runtime tính toán báo riêng. Có thể tóm tắt bằng chất lượng tích lũy trên budget chung khi Task D định nghĩa, không chọn công thức ở đây. Không dùng node F1 hoặc detector delay. |
| **Null hypothesis H0** | Ở cùng cutoff và input budget, quan hệ trace không cải thiện service-ranking đạt mức ý nghĩa thực tiễn so với local evidence; không có lợi thế hữu ích về lượng bằng chứng phải chờ để đạt chất lượng rank so sánh được. |
| **Alternative hypothesis H1** | Có một miền observation budget đã định trước mà graph reasoning giúp service-ranking tốt hơn hoặc đạt chất lượng so sánh được với ít thời gian bằng chứng hơn, ổn định qua incident groups thay vì chỉ tại cutoff chọn sau khi xem kết quả. |
| **Falsification condition** | H1 không được hỗ trợ nếu local comparator bằng/tốt hơn trên miền budget đã khóa; ưu thế chỉ xuất hiện khi cấp future graph/candidate; hoặc coverage thấp khiến chất lượng prefix không có ý nghĩa. Nếu uncertainty quá lớn thì kết quả inconclusive, không chốt H0. Không chọn cutoff tốt nhất hậu nghiệm để cứu giả thuyết. |
| **Main confounders** | Workload/trace frequency, symptom build-up theo fault type, boundary injection khác first symptom, warm-up/reference length, parent resolve thay đổi theo prefix, service chưa xuất hiện sớm, số điểm quan sát và autocorrelation. Cùng giây timestamp không chứng minh cùng thời điểm telemetry thực sự tới collector. |
| **Main leakage risks** | Dùng duration của span chưa hoàn tất tại cutoff, join parent chỉ xuất hiện sau cutoff, dùng full-case candidate coverage, future log templates/normalization, full-case max severity, chọn cutoff bằng root label. Prefix phải có quy tắc quan sát được cho span hoàn tất; thiếu arrival timestamp phải hạn chế claim thành retrospective timestamp-censored evaluation. |
| **Expected implementation complexity** | Trung bình: kiểm soát cutoff/joins và tái sử dụng processing theo prefix có thể phức tạp hơn chạy một rank cuối case. Không cần chọn hoặc phát minh graph neural model. Chuẩn hóa comparator mới là phần tốn công; không ước lượng runtime/GPU khi chưa chọn baseline. |
| **Expected dataset risk** | Trung bình–cao: root coverage sớm chưa xác minh, short pre-fault window, mọi injection có offset cùng cấu trúc, không có ingestion timestamp độc lập. Có thể kiểm rank-vs-evidence-time trong RE2-TT; muốn claim vận hành online phải có controlled FlashTicket hoặc dataset có timing instrumentation thích hợp. Không cần dataset thứ hai chỉ để dựng đường offline có giới hạn. |
| **FlashTicket transfer relevance** | Hữu ích cho xác định bao nhiêu dữ liệu cần thu trước khi hiển thị danh sách nguyên nhân để người vận hành kiểm. FlashTicket sau này cần kiểm end-to-end telemetry delay/collector time riêng; hiện không yêu cầu đổi backend/UI hay xây stopping policy. DT18 yêu cầu áp dụng thực tế nên phần validation này không được thay bằng đường cong TT. |
| **OUT OF SCOPE** | Detector trigger/onset accuracy; automated stopping threshold; bất kỳ window size cố định hay công thức rank; trace repair; causal propagation; operation RCA; production MTTR claim; automatic remediation; dùng LLM suy root cho prefix thiếu dữ liệu. |
| **Why may NOT be thesis-worthy** | Latency/accuracy trade-off có thể đã là sensitivity analysis trong prior work. Nếu kết quả chỉ là “chờ lâu có thêm samples”, không phát hiện điều kiện khác biệt có thể lặp lại hoặc không thay đổi quyết định sử dụng, contribution quá nhỏ. Nếu thiếu arrival times mà vẫn muốn claim real-time advantage, câu hỏi bị sai construct; phải giữ claim offline hẹp hoặc bỏ hướng. |

**Trace missingness:** `KNOWN LIMITATION`, thêm `SECONDARY ROBUSTNESS ANALYSIS` nếu báo theo observed parent coverage. Prefix thiếu parent là vấn đề lượng bằng chứng/observability, không tự biến thành reconstruction problem.

**Operation role:** `NOT USED` như mục tiêu hoặc biểu diễn bắt buộc; span keys chỉ phục vụ graph/cutoff. **LLM role:** giải thích ranked evidence tại cutoff, không peek future và không tạo missing labels; đánh giá LLM không là primary RQ. **Phù hợp supervisor:** đóng góp cho graph reasoning và evaluation thực dụng; không tự đáp ứng graph anomaly detector theo nghĩa nghiêm ngặt.

**OPEN literature cần kiểm đích danh trước survival gate:** phụ lục/experiment sections MicroRank, BARO, TORAI, CIRCA và Eadro/ARMOR có đã đo rank theo same evidence cutoff, tách observation delay và compute time, kiểm candidate coverage chưa? Nếu đã có cùng phép kiểm đủ mạnh, CB-02 chỉ còn reproduction/application contribution. A không ghi đủ để kết luận hai phía; không mở survey rộng hoặc mặc nhiên bảo vệ hướng.

## 4. Các ý tưởng không được nâng thành raw candidate ở C-B

Đây là giới hạn riêng của reviewer, không phải rejection của tập ứng viên khác:

| Ý tưởng rộng | Lý do không tạo một candidate riêng |
|---|---|
| “GNN + metrics/logs/traces” | CB-E1, A §G/L: đã có prior trực tiếp; tên công nghệ không phát biểu câu hỏi khoa học |
| “Operation localization trên RE2-TT” | B §12.7/12.9/12.17: không có operation GT. Dùng operation nội bộ có thể hợp lệ nhưng chưa đủ một đóng góp độc lập |
| “Hoàn thiện graph thiếu” | A §H/L và B §12.11: cần target/semantics và proof mới; không được suy từ bảy graph coverage thấp thành nghĩa vụ tái dựng |
| “LLM chứng minh nguyên nhân” | A §B/J/N và B §12.9: lời giải thích không bổ sung causal/operation labels |

## 5. Điểm chưa khóa và bàn giao

- **Không thêm/đổi quyết định:** chỉ hai raw candidates CB-01 và CB-02; không chọn winner, algorithm, threshold, model architecture, split numeric hoặc window numeric.
- **Giả định có điều kiện:** thí nghiệm sau này có thể lấy telemetry pinned bằng retrieval được phép; loader thực thi đúng B §12.10; Task D định nghĩa practical-effect criterion và phân tích uncertainty trước khi xem test outcomes. Chưa coi điều kiện đó đã hoàn tất.
- **Kiểm đã làm:** đối chiếu giới hạn trong B §12 với A §C/J/L; trực tiếp đọc JSON full-case coverage và parent-resolution/transfer; kiểm lại khác biệt full-case/prefix; tách xếp hạng khỏi detection, labels khỏi input và trace relation khỏi causal edge.
- **Kiểm tệp và governance:** đủ 24 trường contract, mỗi trường xuất hiện đúng hai lần cho hai candidate; có marker kết thúc hoàn chỉnh. Governance audit kết thúc PASS, kèm một warning về bốn tệp thay đổi đã có sẵn trong canonical repository; trạng thái Git đó không đổi so với trước lượt C-B. Audit không xác nhận chất lượng khoa học của ứng viên.
- **OPEN quan trọng:** targeted literature verification cho cả hai câu hỏi; power của 30 scenarios; prefix coverage; baseline adaptability và compute; mức chấp nhận đóng góp empirical/incremental của Minh/giảng viên. Đây chưa là yêu cầu người dùng chọn trong bước recovery.
- **Nội dung có thể đưa vào báo cáo sau này:** lý do metric gắn đúng service GT, contract chống leakage, giới hạn causal semantics, lợi ích hoặc kết quả âm của controlled evaluation. Chưa được đưa novelty/effectiveness claim trước thực nghiệm.
- **Tệp duy nhất do C-B ghi:** `D:/Project/flash-ticket-rca-research/task-c/phase-1-independent-candidates/reviewer-b.md`.
- **Barrier:** C-B hoàn tất riêng; không cross-review/hợp nhất. Main chỉ kiểm completeness và checkpoint trong bước recovery.

**END OF INDEPENDENT REVIEWER C-B — COMPLETE**
