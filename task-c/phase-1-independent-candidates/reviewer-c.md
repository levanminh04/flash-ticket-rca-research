# Task C — Reviewer C-C: khả năng đánh giá từ dữ liệu và ground truth

- Trạng thái thực thi: **COMPLETE**. Trạng thái nghiên cứu: **DRAFT / CANDIDATE**, chưa duyệt hướng nào.
- Ngày: 2026-09-20. Intent: `EXECUTE`; loại tạo tác: `FORMATION`.
- Vai trò: reviewer độc lập về dữ liệu, nhãn, khả năng quan sát và leakage.
- Phạm vi khôi phục: hoàn tất riêng C-C; không tổng hợp A/B/C, không khởi chạy reviewer khác.
- Độc lập: chưa đọc output ứng viên của reviewer khác; không đọc E1/A10, phương pháp sinh viên hoặc đề xuất hội thoại trước. Không nhận danh sách ứng viên từ main. Hai ứng viên dưới đây hình thành từ khả năng đánh giá sau Task B, không phải lựa chọn thuật toán.
- Quy ước: `VERIFIED — TASK A/B/MACHINE EVIDENCE` là `FACT` trong phạm vi nguồn; `TASK-C INFERENCE` là lập luận/đề xuất `CANDIDATE`; `OPEN` chưa được xác lập. Toàn bộ hợp đồng thí nghiệm dưới đây là `TASK-C INFERENCE / CANDIDATE`, trừ câu có lớp nguồn khác ghi rõ.

## 1. Nguồn đã dùng và ranh giới chứng cứ

Nguồn chính:

- **A:** [Task A](D:/Project/flash-ticket-platform/docs/research-rca/task-a-ban-do-bang-chung-doc-lap.md), đọc toàn bộ ở lượt ban đầu, đặc biệt C.2–C.12, D, I, J, L, M, Q.
- **B:** [Task B CLOSED](D:/Project/flash-ticket-rca-research/dataset-audit/TASK-B-RCAEval-audit.md), đọc toàn bộ ở lượt ban đầu; §12 là kết luận hiệu lực, §1–11 là lịch sử bảo tồn.
- **L:** [Task-C evidence ledger](D:/Project/flash-ticket-rca-research/task-c/task-c-evidence-ledger.md), đọc lại đầu lượt khôi phục. ID dưới đây tham chiếu đúng bảng của ledger.
- Báo cáo độc lập Task B đã trực tiếp dùng: [I — ground truth](D:/Project/flash-ticket-rca-research/audits/rcaeval/subagent-i-re2tt-groundtruth.md), [H — red team](D:/Project/flash-ticket-rca-research/audits/rcaeval/subagent-h-methodology-red-team.md), [J — full trace](D:/Project/flash-ticket-rca-research/audits/rcaeval/subagent-re2tt-full-trace-audit.md), [F — ground truth lịch sử](D:/Project/flash-ticket-rca-research/audits/rcaeval/subagent-f-ground-truth-leakage.md). Dùng E về multimodal qua B §12.5/12.13 và ledger R-002; không tuyên bố C-C đọc độc lập trọn vẹn cả 11 reviewer. Main đã ingestion cả 11 theo ledger.
- Machine evidence đã xem: [metadata/GT I JSON](D:/Project/flash-ticket-rca-research/audits/rcaeval/subagent-i-re2tt-groundtruth.json), các phần summary/schema/parent/transfer của [full trace JSON](D:/Project/flash-ticket-rca-research/audits/rcaeval/re2tt-trace-full-subset-audit.json), summary của [candidate coverage JSON](D:/Project/flash-ticket-rca-research/audits/rcaeval/re2tt-target-candidate-coverage.json). Không quét lại telemetry.
- Định hướng hiện hành: [DT18](D:/Project/flash-ticket-platform/docs/evidence/project-direction/2026-09-18-de-tai-va-nhiem-vu.md), [roles](D:/Project/flash-ticket-platform/docs/project/roles.md), hiến pháp và skill govern-capstone-work. Đề tài phải có hệ thống bán vé được đánh giá, cơ chế đồ thị dùng log/trace/metrics và thử trên FlashTicket; public benchmark không thay thế phần kiểm chứng FlashTicket. Minh phụ trách chính RCA, không giả định cả bốn người làm RCA toàn thời gian.

| Điểm xuất phát | Lớp chứng cứ và nguồn | Hệ quả hợp lệ cho discovery |
|---|---|---|
| 90 case RE2-TT = 5 dịch vụ gốc × 6 fault × 3 lần lặp; mọi inject_time ở trong cửa sổ, cùng offset 720 giây; 720/721 timestep trước/sau | VERIFIED — MACHINE EVIDENCE; I JSON `re2tt_metadata_facts`; L M-001 | Có đơn vị case và nhãn service để chấm ranking. Offset cố định tạo shortcut; không có nhãn onset độc lập. |
| Mỗi case có metrics và traces; 89/90 có logs; cây phát hành không có operation/resource/affected-node/path target | VERIFIED — MACHINE EVIDENCE; I JSON `official_repository_tree`, `ground_truth_availability`; B §12.9 | Chỉ nhắm service-ranking làm output định lượng chính. Thiếu nhãn không được giải quyết bằng suy luận từ tên operation hoặc LLM. |
| 90 full-case trace candidate sets chứa đúng nhãn root; kích thước 20–27 | VERIFIED — MACHINE EVIDENCE; coverage JSON; L M-005 | Có endpoint coverage. **Chưa chứng minh** coverage ở prefix ngắn hoặc trước sự cố. Không lấy năm injected labels làm candidate universe. |
| 27 literal services và 161 literal service-operation pairs là union trên toàn 90 case; 55 loại quan hệ cross-service quan sát | VERIFIED — MACHINE EVIDENCE; full trace JSON `summary`; L M-003/M-006 | Hai mức biểu diễn có thể dựng; union audit không được dùng làm test graph hoặc danh mục feature học từ tương lai. |
| Chỉ parent cùng trace resolve được mới thành cạnh; tổng 98.45274372%, bảy case dưới 90%, thấp nhất 38.54287289% | VERIFIED — MACHINE EVIDENCE; full trace JSON `summary.parent_resolution` và `parent_resolution_case_profile`; L M-004 | Giữ case khó; báo độ phủ theo case. Parent resolution không phải topology recall, không xác định nguyên nhân missingness. |
| Trace không có protocol/kind/resource/causal fields; operation pair là literal representation | VERIFIED — TASK B và MACHINE EVIDENCE; B §12.6–12.8 | Chỉ gọi cạnh là quan hệ cha–con suy từ trace. Không có CALLS/USES/causal path hay resource graph được xác minh. |
| L–M khớp exact service/container-second bin trong mẫu; hai join có trace chỉ service+time | VERIFIED — TASK B; B §12.5/12.13; L R-002/M-007 | Logs có thể là bằng chứng theo bin, không gắn vào request/span. Kết quả 271,919 dòng là riêng một case B2B, không phải schema/join prevalence của 89 case. |
| B2 dùng range reads cho 89 object và không giữ corpus trace mới | VERIFIED — MACHINE EVIDENCE; full trace JSON `summary.transfer`; L M-009 | File audit không phải dữ liệu sẵn để chạy mô hình. Thực nghiệm sau cần retrieval được phép, lưu provenance và kiểm loader. |
| Graph ablation, operation evidence và multimodal đều có prior; không gap nào đã mạnh | VERIFIED — TASK A; A C.3/C.7/C.8/C.9/I/L/Q; L A-005/A-006 | Khả năng đánh giá không đồng nghĩa đóng góp đủ cho luận văn. Cả hai hướng cần gate literature, có thể bị loại. |

**TASK-C INFERENCE:** từ các ranh giới này, hai trục còn chấm được mà không chế nhãn là (i) lượng bằng chứng quan sát tới thời điểm chẩn đoán và (ii) cách tổ chức cùng bằng chứng trước khi trả kết quả ở cấp service. Tôi giữ hai hướng dưới đây; không thêm hướng chỉ để đủ số lượng. Thứ tự ID trung tính.

## 2. CC-01 — Giá trị của đồ thị khi thời gian tích lũy bằng chứng chẩn đoán còn ngắn

### Câu hỏi và vị trí khoa học

**CANDIDATE ID:** CC-01.

**Working title:** Giá trị của ngữ cảnh đồ thị đối với xếp hạng nguyên nhân dịch vụ theo ngân sách quan sát sau sự cố đã biết.

**Research Question:** Khi cùng nhận một mốc sự cố từ bên ngoài, cùng telemetry tới một cutoff và cùng tập service quan sát được, ngữ cảnh quan hệ suy từ trace có giúp đặt đúng service gốc lên đầu danh sách với ít thời gian tích lũy bằng chứng hơn so với xếp hạng từ bằng chứng cục bộ hay không; lợi ích ấy còn tồn tại khi tính cả thất bại do root chưa xuất hiện trong prefix?

**Why scientifically interesting:** so sánh ranking trên cả cửa sổ có thể che việc một phương pháp chỉ hữu ích sau khi đã nhìn phần lớn sự cố. Câu hỏi đo trao đổi giữa chất lượng chẩn đoán và thời gian phải chờ có thêm telemetry, đồng thời tách giới hạn quan sát ứng viên khỏi giới hạn xếp hạng. Kết quả âm có ý nghĩa: đồ thị có thể không giúp ở giai đoạn ít evidence, hoặc thêm thời gian tính toán lớn hơn phần chờ tiết kiệm. Đây chưa phải claim về detection nhanh hoặc lợi ích vận hành thực tế.

**Closest prior work:** MicroRank dùng normal history, trigger và thu thêm khoảng năm phút trace (A C.3); MicroRCA cô lập localizer bằng cấp cùng detector output cho baseline (A C.2); BARO tách thời gian detection/ranking nhưng trên một protocol khác (A C.4); CIRCA/TORAI nhận mốc sự cố ngoài (A C.6/C.8); Eadro có graph ablation (A C.7). Các chi tiết này là **VERIFIED — TASK A**, không được chuyển trực tiếp số hiệu năng sang RE2-TT.

**What remains unresolved according to Task A:** A J.2/L yêu cầu so cùng case, candidate và input; graph benefit ngoài local score mới là `NEEDS MORE EVIDENCE`. Task A chưa xác lập một so sánh chung giữa các ngân sách quan sát, có kiểm cutoff của graph và mất coverage. **OPEN:** chưa đủ để nói literature chưa làm bài toán này; targeted verification sau barrier cần kiểm chính xác chỗ trùng với evaluation của closest work. Không nhận “time budget” làm novelty mặc định.

**Task-B evidence making it testable:** B §12.9/12.10/12.12 cho known-window RCA và service GT; timestamp/parent relation có trong full trace schema; I JSON chứng minh 90 cửa sổ hợp lệ; coverage JSON chứng minh endpoint full-case. Khả năng chấm ở prefix là **TASK-C INFERENCE**: evaluator giữ nhãn nhưng model chỉ thấy prefix; root chưa thấy là coverage failure, không thêm node bằng nhãn. Chưa biết phân bố prefix coverage từ audit hiện hành.

### Hợp đồng đánh giá ở mức cao

**Primary experimental unit:** một injected incident/case. Các cutoff là repeated measurements trong cùng case, không phải mẫu độc lập. Có 30 tổ hợp service–fault và ba repetitions mỗi tổ hợp; uncertainty phải tôn trọng cụm incident/scenario.

**Input telemetry:** traces và metrics tới cutoff quan sát, với một đoạn tham chiếu hợp lệ thuộc protocol known-window. Mốc inject_time chỉ thay cho mốc sự cố ngoài trong protocol đã công khai; không làm feature. Logs là secondary evidence theo service-second nếu hợp lệ, không là điều kiện tồn tại của phép thử chính. Không dùng case length, full counts, fault name hoặc end-of-case để dự đoán.

**Graph role:** ngữ cảnh phục vụ xếp hạng service, dựng từ những parent reference resolve trong phần dữ liệu được phép xem. Cùng local evidence được đối chiếu khi bật/tắt ngữ cảnh đồ thị. Không thay local detector rồi quy toàn bộ hiệu ứng cho graph. Graph không được dùng cạnh từ sau cutoff hoặc từ test case khác; không được gọi đầy đủ topology.

**Primary output:** một ranked list service tại từng ngân sách quan sát. Báo cả thời gian tích lũy evidence và chi phí xử lý riêng; nếu nối thành elapsed diagnosis time phải ghi rõ đây là mô phỏng offline, chưa đo collector/alert/ingestion latency thật.

**Ground truth:** đúng một `root_cause_service` mỗi case. `inject_time` chỉ là boundary của injection regime dùng cho known-window RCA, không phải observed anomaly onset. Không có ground truth “thời điểm đầu tiên có thể chẩn đoán đúng”; thời điểm rank đạt điều kiện là thuộc tính kết quả thuật toán, không phải nhãn mới.

**Expected baseline family:** local statistical deviation ranker; graph-based ranker cùng evidence/candidate/cutoff; một họ known-window RCA hiện có có thể nhận input hợp lệ; đối chứng không có graph. Exact baseline và adapter sang service để Task D chọn. Mỗi nhóm phải công khai modality, normal history và label budget; không so trực tiếp reproduction có đầu vào khác mà gọi là hiệu ứng graph.

**Evaluation family:** đường Hit@k/MRR theo ngân sách quan sát; paired effect giữa hai điều kiện ở cùng cutoff; runtime/latency-to-result báo riêng; coverage tại cutoff. Nhãn vắng khỏi universe nhận miss/reciprocal rank 0 trong kết quả chính. Phân tích conditional-on-visible chỉ là phân tích phụ giải thích thất bại, luôn kèm denominator. Có thể xem ranking stability như tính chất output, không nhầm stability với correctness. Không tính service anomaly F1, onset detection delay hoặc production false-alarm rate.

**Null hypothesis H0:** ở cùng ngân sách quan sát và chi phí tính toán có thể so sánh, dùng ngữ cảnh đồ thị không cải thiện service-ranking một mức có ý nghĩa so với local evidence; hoặc mọi lợi ích chỉ xuất hiện khi đã quan sát gần trọn case.

**Alternative hypothesis H1:** trên incident chưa dùng để chọn cấu hình, ngữ cảnh đồ thị tạo cải thiện ranking có ý nghĩa ở các ngân sách quan sát ngắn hơn, bao gồm đầy đủ coverage misses, và lợi ích không chỉ nằm ở một service/fault hoặc được giải thích hết bởi tăng compute/input.

**Falsification condition:** H1 không được ủng hộ nếu paired effect không vượt mức ý nghĩa thực tiễn đăng ký trước; hiệu ứng biến mất khi cấm future graph/candidate union; chỉ có hiệu quả sau cửa sổ gần đầy đủ; hoặc chi phí xử lý xóa lợi thế thời gian. Nếu uncertainty quá rộng, kết luận không xác định thay vì khẳng định H0. Mức hiệu ứng, cutoff grid và tiêu chí đầu ra ổn định đều để Task D đăng ký trước, chưa chọn tại đây.

### Nguy cơ, phạm vi và khả năng thực hiện

**Main confounders:** tốc độ sinh span khác nhau; workload/request mix; root chưa được quan sát; mức nặng fault; identity/topology đặc thù từng service; bảy graph độ phủ thấp; tương quan giữa repetitions; protocol cùng thời điểm injection. Số span tăng không phải số thí nghiệm tăng. So cùng wall-clock observation budget và báo volume giúp thấy khác biệt về lượng evidence; không giả định volume đã được randomize.

**Main leakage risks:** toàn bộ graph union 90 case; service universe từ cả case tại prefix sớm; normalizer/log vocabulary fit từ tương lai; path/fault tokens; dùng root label để chọn cutoff, bỏ case hoặc chọn cạnh; chọn ngân sách “đẹp” sau khi xem test; lấy midpoint 720 giây làm detector. Split/tuning phải theo case/group, không chia random span/window. Tập ứng viên tại mỗi cutoff do telemetry quy định trước khi mở label.

**Expected implementation complexity:** trung bình. Cần loader an toàn, feature có provenance thời gian, reuse computation giữa cutoff, comparator cùng hợp đồng. Không cần topology reconstruction, deep model hoặc serving platform. Full traces có 67,345,051 rows nên tránh nhân toàn bộ preprocessing theo mỗi cutoff; compute thực tế còn `OPEN`, chưa chạy benchmark hiệu năng.

**Expected dataset risk:** trung bình–cao. Trace schema và endpoint coverage đã kiểm toàn subset; prefix coverage chưa có số; metric/log schema không được audit toàn 90. RE2-TT là campaign cố định, không chứa healthy-only vận hành dài. Có thể kiểm RQ hẹp bằng data hiện có về mặt phát hành; máy local hiện không có corpus full mới. Nếu prefix root vắng phần lớn ở mọi ngân sách hữu ích, hướng có thể chỉ trả lời một hạn chế quan sát đơn giản, thiếu sức nặng luận văn.

**FlashTicket transfer relevance:** hợp với việc operator muốn có danh sách nên kiểm sau một alert. Cần thử riêng với alert và thời điểm ingest thực tế của FlashTicket trước claim operational latency; không tự thêm service, fault flow hay yêu cầu hệ thống. Một public dataset thứ hai hữu ích cho external validity, không bắt buộc để chấm RQ giới hạn RE2-TT; claim liên hệ thống đòi kiểm chứng bổ sung. DT18 vẫn yêu cầu áp dụng và đánh giá trên FlashTicket.

**Trace-missingness role:** `SECONDARY ROBUSTNESS ANALYSIS`. Giữ bảy case khó và báo profile; không sửa trace, không biến missingness thành đóng góp chính. Candidate availability ở prefix là giới hạn quan sát theo thời gian, không được tự gán là missing-trace pathology.

**Operation role:** `NOT USED` làm đơn vị chẩn đoán chính; có thể giữ literal span fields cho provenance. Không dùng operation GT giả. Nếu operation representation trở thành biến thí nghiệm, đó là CC-02, không lén gộp hai RQ.

**LLM role:** giải thích structured ranked evidence sau khi rank được tạo; không chọn cutoff, không bổ sung candidate, không làm detector và không chấm đúng/sai root. Đánh giá lời giải thích nằm ngoài câu hỏi định lượng chính.

**OUT OF SCOPE:** end-to-end anomaly-onset detection, service anomaly classification, operation/resource/path localization, topology repair, causal proof, multi-root incidents, incident prediction, thuật toán/threshold/window cụ thể, sửa code/hạ tầng FlashTicket.

**Why this may NOT be thesis-worthy:** nếu chỉ chạy lại baseline trên vài đoạn cắt ngắn rồi vẽ đường score, đây có thể là sensitivity analysis thông thường. Cần literature gate xác nhận câu hỏi evidence maturity đủ chưa được cô lập và kết quả có điều kiện thất bại có thể giải thích; nếu không, nên hạ xuống analysis phụ. Không bảo vệ ứng viên chỉ vì dataset chấm được.

## 3. CC-02 — Mức biểu diễn nội bộ nào giúp chẩn đoán ở cấp dịch vụ?

### Câu hỏi và vị trí khoa học

**CANDIDATE ID:** CC-02.

**Working title:** Giá trị và chi phí của việc giữ literal service-operation trong biểu diễn đồ thị khi ground truth chỉ ở cấp service.

**Research Question:** Trên cùng failure case, raw trace observations, metric evidence và service candidate universe, giữ phân tách theo literal `(serviceName, operationName)` trước khi tổng hợp kết quả về service có cải thiện xếp hạng service gốc so với tổng hợp sớm ở mức service hay không, và cải thiện có còn khi kiểm soát dung lượng biểu diễn, độ thưa và chi phí xử lý?

**Why scientifically interesting:** mức biểu diễn là một lựa chọn làm mất hoặc giữ thông tin trước chẩn đoán; nhãn coarse không buộc mọi bước xử lý đều coarse. Nhưng giữ nhiều chi tiết có thể làm bằng chứng phân mảnh hoặc tăng thiên lệch về service có nhiều operations. Bài toán hỏi lợi ích cho đúng output quan sát được, không dùng representation mịn để hứa một kết quả không có nhãn. Có thể cho kết luận âm hữu ích về khi nào aggregate sớm là đủ.

**Closest prior work:** MicroRank dùng service-instance operation và có trường hợp hạ xuống service; TORAI dùng trace operation indicators; DeepTraLog có span/log event graph nhưng output anomaly theo trace; DéjàVu dùng failure units; Eadro xếp service. Đây là **VERIFIED — TASK A**, A C.3/C.7/C.8/C.9/C.10/I. Không lấy accuracy operation của MicroRank hay trace F1 của DeepTraLog làm baseline score service trực tiếp.

**What remains unresolved according to Task A:** A I/L nêu trade-off granularity–observability–label và yêu cầu cùng cases/input/root semantics; đồng thời operation-aware representation ở formulation rộng đã `LIKELY ALREADY COVERED`. Câu hỏi hẹp ở đây là **TASK-C INFERENCE**, không có xác nhận novelty. A L nói so localization nhiều mức cần nhãn nhiều mức; CC-02 chỉ thay representation, giữ duy nhất service localization nên không tuyên bố thực hiện được so accuracy ở nhiều mức. `OPEN`: so sánh có thật sự khác ablation granularity của closest papers hay chỉ lặp lại.

**Task-B evidence making it testable:** B §12.7/12.9/12.15 và full trace JSON chứng minh 161 literal pairs, parent links và membership span→service/operation có thể dựng. Coverage JSON chứng minh full-case service targets đều quan sát được. **Không** có operation root label; đó là lý do primary output được cố định là service rank. Mọi con số 161/27/55 chỉ mô tả union audit, không làm feature vocabulary hoặc topology áp sẵn cho case.

### Hợp đồng đánh giá ở mức cao

**Primary experimental unit:** một case với hai điều kiện representation ghép cặp. Mỗi condition trả cùng loại output service. Các span/operation không trở thành các label instances độc lập; thống kê không dựa vào 67 triệu hàng như sample size.

**Input telemetry:** cùng tập traces được phép xem trong known-incident protocol; cùng metric observations làm evidence phụ nếu mapping hợp lệ. Hai condition khác ở việc giữ hoặc gộp literal operation identity, không khác về cửa sổ, số request được đọc, label budget hay modal availability. Logs chỉ secondary service-bin evidence và phải đi vào cả hai condition theo cùng rule nếu dùng.

**Graph role:** điều kiện coarse tổng hợp quan hệ parent–child đã resolve ở mức service; điều kiện finer giữ literal service-operation và quan hệ parent–child quan sát được trước khi tạo service output. Dùng membership quan sát để quy về service, không đoán protocol/DB type từ chuỗi operation. Không có operation root classifier hoặc kiến trúc neural đã chọn.

**Primary output:** ranked services trên cùng universe được tạo trước nhãn. Có thể xuất supporting operation evidence để kiểm tra thủ công, nhưng các operation ấy không được gọi là correctly localized root operations.

**Ground truth:** `root_cause_service` theo case. Mỗi service xuất hiện đúng một lần trong ranked list; không lặp service nhiều lần qua nhiều operations để tăng cơ hội hit. Không gán mọi operation của root service là positive label, không dùng pseudo-label do LLM hoặc chọn operation lệch nhất làm “ground truth”.

**Expected baseline family:** service-level graph RCA và service-local statistical ranker; finer trace-evidence family có service aggregation được công khai; matched coarse/finer variants của cùng họ scoring nếu khả thi. Graph-free comparator giúp phân biệt lợi ích giữ operation evidence với lợi ích quan hệ graph. Exact aggregation/ranking mechanism và baseline adapter để Task D định nghĩa. Một adapter service từ operation method phải gọi rõ là adaptation, không tuyên bố reproduction nguyên bản.

**Evaluation family:** case-level MRR, Hit@k/AC@k theo định nghĩa đã nêu; optional binary-relevance NDCG chỉ là phép biến đổi vị trí một root, không đo severity. Báo paired effect và uncertainty theo case/scenario; thời gian, bộ nhớ/representation size; stratify theo số literal pairs, evidence sparsity và parent coverage để đọc cơ chế thất bại. Không tính operation accuracy, node F1 hoặc path correctness.

**Null hypothesis H0:** việc giữ operation identity không đem lại cải thiện service-ranking có ý nghĩa sau khi giữ input/candidate/cost đủ công bằng; mọi chênh lệch đến từ nhiều capacity, cách aggregation ưu ái service nhiều operations, hoặc tuning không cân bằng.

**Alternative hypothesis H1:** giữ phân tách operation trong representation làm service evidence ít bị pha trộn hơn và cải thiện service-root ranking trên case held-out, với lợi ích không biến mất trong controls về capacity/cost, operation count và family fault/service.

**Falsification condition:** H1 không được ủng hộ nếu gain mất khi comparator cùng input/budget, gain chỉ theo số operation hoặc một root service, representation mịn làm tăng chi phí mà không cải thiện mức đã đăng ký, hoặc biến thể coarse giải thích được kết quả tương đương. Nếu paired estimate quá bất định thì chưa kết luận, không gọi khác biệt vô nghĩa là bằng chứng không có effect. Không đặt effect size, công thức aggregation hoặc ngưỡng tại Task C.

### Nguy cơ, phạm vi và khả năng thực hiện

**Main confounders:** service có 3 operations khác service có nhiều operations; operation strings có generic GET/POST và tên repository; tần suất/độ dài trace; nhóm fault tác động mạnh chỉ một phần service; mô hình nhiều node có nhiều capacity; graph coverage; normal history ngắn; workload và repetitions tương quan. Cặp literal hỗ trợ reproducibility, không bảo đảm cùng semantic operation qua version/hệ khác.

**Main leakage risks:** lấy 161-pair union từ toàn bộ train/test làm vocabulary; dùng root/fault metadata để chọn operation hoặc trọng số; tune aggregation trên test; dùng service name như prior nhớ injected target; chỉ cho năm root dịch vụ vào output; đổi candidate universe khi đổi granularity; lấy test future graph. Root/fault labels giữ evaluation-only theo B §12.10, không đưa vào fit; bất kỳ nhu cầu supervised root-label training nào là xung đột với hợp đồng dữ liệu này, không được tự mở rộng. Candidate count, raw input window và nhãn phải giống nhau giữa hai condition.

**Expected implementation complexity:** trung bình. Hai deterministic representations và một service-output adapter có phạm vi kiểm soát được; chi phí graph-level exact mechanism chưa chọn. Không cần host/resource schema hay annotation operation. Kiểm công bằng capacity/cost khó hơn dựng graph và có thể trở thành phần tốn công chính.

**Expected dataset risk:** trung bình. Khả năng dựng literal pair trên all-90 traces được xác minh, service GT rõ. Rủi ro lớn là semantics yếu và năm root targets quá ít để kết luận tổng quát; chỉ 90 cases và một collection. Tập metrics/logs chưa kiểm schema toàn bộ. Audit đã tồn tại nhưng chưa có full local corpus cho modeling; cần retrieval được phép ở giai đoạn thực nghiệm.

**FlashTicket transfer relevance:** trả lời có đáng giữ chi tiết operation trong đường xử lý RCA khi operator trước hết cần khoanh service. Thử chuyển sang FlashTicket có thể dùng service fault labels để chấm cùng task; không bắt nhóm phải tạo operation GT. Không biến kết quả benchmark thành yêu cầu tracing/schema mới của bộ hệ thống. Public dataset thứ hai hữu ích để kiểm giảm phụ thuộc literal operation naming; cần nếu claim vượt collection cụ thể. FlashTicket validation theo DT18 vẫn phải có.

**Trace-missingness role:** `SECONDARY ROBUSTNESS ANALYSIS`. Báo các case có parent coverage thấp và sparsity; không yêu cầu reconstruction. Không diễn giải so low/high coverage là can thiệp ngẫu nhiên hay causal effect của missingness.

**Operation role:** `INTERMEDIATE REPRESENTATION`. Quantitative target luôn service. LLM sau này có thể mô tả operation evidence như giả thuyết phụ, không nâng thành operation diagnosis đã chấm đúng.

**LLM role:** downstream structured evidence explanation; không dùng LLM để chuẩn hóa operation thành nhãn chuẩn, điền semantic type, học pseudo-GT hoặc xác nhận root operation. Hữu ích cho giao diện nhưng không phải đóng góp định lượng của CC-02.

**OUT OF SCOPE:** operation-root accuracy, multi-granularity localization metrics, resource graph, trace-event log attachment, semantic CALLS/causal edges, topology repair, causal mechanism validation, chọn GNN/PageRank, code/API/schema/UI FlashTicket.

**Why this may NOT be thesis-worthy:** một ablation “gộp sớm/gộp muộn” có thể quá nhỏ và đã có trong prior; nếu chỉ tăng node count hoặc giữ thêm feature thì là kỹ thuật biểu diễn. Hướng chỉ đáng tiếp tục nếu literature gate xác định được điều kiện chưa cô lập và experiment có controls đủ mạnh để phân biệt lợi ích thông tin với capacity/aggregation bias. Không đủ căn cứ để gọi đây là phương pháp mới.

## 4. Các hướng không sinh thành ứng viên chính trong review này

| Hướng có vẻ khả thi | Lý do không đưa thành primary candidate từ lens dữ liệu | Nguồn/lớp |
|---|---|---|
| Phát hiện anomalous service hoặc chấm node F1 | Root label không phải affected/anomalous-node labels; không có phép chấm hợp lệ | VERIFIED — TASK B; B §12.9/12.12/12.17 |
| Operation/resource/causal-path localization | Thiếu GT cùng đơn vị; representation không cứu được task-label mismatch | VERIFIED — TASK B; B §12.7–12.9 |
| Detection onset “thực tế” hoặc production false alarms trên RE2-TT | Chỉ có injection regimes cùng offset, không independent onset/healthy operating episodes; có thể là secondary bounded injection-window experiment, không kết luận đó | VERIFIED — TASK B + TASK-C INFERENCE; I JSON; B §12.12; L T-002 |
| Tái dựng graph thiếu làm đóng góp chính | Có parent-resolution profile nhưng không complete-topology GT; không đủ để chấm repair truth; không cần tự tạo thêm yêu cầu | VERIFIED — TASK B + TASK-C INFERENCE; B §12.7/12.11; A H/L |
| Multimodal nói chung, hoặc request-level trace-log graph | Prior đã mạnh; join request/span không được hỗ trợ. Một RQ modality contribution hẹp có thể xét sau nhưng lens này không có bằng chứng đủ để thêm làm ứng viên chính | VERIFIED — TASK A/B; A G/L; B §12.5/12.13 |

Đây là giới hạn của lượt discovery C-C, không phải phán quyết tổng hợp loại ứng viên của reviewer khác. Không có output peer nào được đọc để lập bảng này.

## 5. Kiểm hoàn tất và bàn giao

- Đã có hai ứng viên thật; mỗi ứng viên đủ 24 trường hợp đồng §12, thêm trace-missingness/operation/LLM roles.
- Đã phân biệt source facts, inference và OPEN; không chọn winner, thuật toán, threshold, window length hoặc hyperparameter.
- Đã dùng B CLOSED §12 để giải hiệu lực cũ: inject_time được phép là known-window boundary, không detector input; L–M direct chỉ theo bin; full-subset parent rates thay sample estimate.
- Không claim full-case coverage là prefix coverage; không dùng union audit làm graph; không gọi injection boundary là onset; không gọi audit JSON là local modeling corpus.
- Không sửa A/B, reviewer Task B, manifests, raw telemetry, code hoặc sổ quyết định. File tạo mới duy nhất bởi reviewer này: `task-c/phase-1-independent-candidates/reviewer-c.md`.
- Quyết định thêm/thay đổi: không có `DECIDED` hay `USER_CONFIRMED` về nghiên cứu; CC-01/CC-02 đều `CANDIDATE`. Để `OPEN` contribution strength, budget, protocol cụ thể và transfer validity.
- Giả định: boundary ngoài được cung cấp trong task known-window; telemetry cutoff có thể được thực thi bởi loader tương lai; mọi comparison giữ service target và candidate policy. Đây là điều kiện thiết kế, chưa được chứng minh bởi chạy mô hình.
- Kiểm tra đã thực hiện ở reviewer: đọc nguồn hiệu lực/ledger, đối chiếu JSON metadata/coverage/parent/transfer hiện có, kiểm contract và ranh giới claim. Không download, install, baseline reproduction, train hoặc raw rescan. Governance audit repository và đọc lại artifact sau ghi được báo cho main riêng; audit governance không xác nhận scientific validity.
- Nội dung có thể đưa báo cáo đồ án sau khi được duyệt: task-label alignment, leakage/candidate controls, distinctions giữa operation representation và root target; chỉ thêm kết quả hiệu quả sau thực nghiệm.
- Việc kế tiếp của reviewer: **STOP**. Main chỉ checkpoint tính đầy đủ trong phiên recovery; chưa merge, rank hoặc shortlist.

**END OF REVIEWER C-C — COMPLETE**
