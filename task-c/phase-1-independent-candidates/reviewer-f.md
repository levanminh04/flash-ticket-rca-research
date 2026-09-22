# C-F — Phản biện độc lập theo ý định phương pháp của giảng viên

- Ngày: 2026-09-20. Trạng thái: `DRAFT`; các hướng dưới đây là `CANDIDATE`, các lựa chọn phương pháp là `OPEN`.
- Phạm vi: `EXECUTE / FORMATION`, chỉ tạo tệp reviewer này. Không duyệt RQ, không chọn thuật toán, ngưỡng hoặc kích thước cửa sổ; không sửa Task A/B hay mã hệ thống.
- Độc lập: nhận nhiệm vụ với ngữ cảnh mới; không đọc tệp ứng viên của reviewer khác, đề xuất sinh viên, E1, A10 hay hội thoại trước. Không sinh reviewer con. Hai ứng viên được hình thành từ Task A/B và nghĩa của yêu cầu phương pháp.
- Nhãn bằng chứng: `VERIFIED — TASK A/B` và `PRIMARY-SOURCE FACT` là `FACT` trong phạm vi nguồn; `TASK-C INFERENCE` là `CANDIDATE`; thiếu đầu vào giữ `OPEN`. Người dùng giao phân tích không đồng nghĩa đã duyệt một lựa chọn.

## 1. Nguồn đã đọc và giới hạn trách nhiệm

Đã đọc yêu cầu gốc Task C tại `C:/Users/84583/.codex/attachments/22e07417-e07b-42f3-a60f-793c63c2aec7/Pasted text.txt`, ledger `D:/Project/flash-ticket-rca-research/task-c/task-c-evidence-ledger.md`, toàn bộ Task A, Task B phần đóng §12.1–12.20, báo cáo Task-B I và F về nhãn/rò rỉ, AGENTS.md, skill govern-capstone-work và tài liệu authority/gates, quy trình chủ, DT18, roles và thư lịch sử 22/08. Ledger xác nhận main đã đọc đủ 11 reviewer Task B; reviewer C-F không nhận việc tái audit mọi báo cáo hay telemetry. Các số liệu máy dưới đây được dùng thông qua kết luận CLOSED và ledger đã đối soát, không khai là C-F chạy kiểm chứng raw độc lập.

Ký hiệu:

- **A:** `D:/Project/flash-ticket-platform/docs/research-rca/task-a-ban-do-bang-chung-doc-lap.md`.
- **B:** `D:/Project/flash-ticket-rca-research/dataset-audit/TASK-B-RCAEval-audit.md`, chỉ §12 là kết luận hiện hành.
- **I/F:** `D:/Project/flash-ticket-rca-research/audits/rcaeval/subagent-i-re2tt-groundtruth.md` và `subagent-f-ground-truth-leakage.md`; F là lịch sử PRE-SAMPLE, không ghi đè chính sách inject_time của B §12.10.
- **DT18:** `D:/Project/flash-ticket-platform/docs/evidence/project-direction/2026-09-18-de-tai-va-nhiem-vu.md`.
- **Thư:** `D:/Project/flash-ticket-platform/docs/evidence/advisor-direction/2026-08-22-dinh-huong-de-tai.md`, §1 nguyên văn lịch sử.
- Các ID A-*, B-*, M-*, P-* trỏ đến ledger, không phải quyết định mới.

Không duyệt web bổ sung: chưa có ứng viên nào phụ thuộc một chi tiết UNVERIFIED chỉ có thể giải quyết bằng nguồn ngoài. Không cài, tải, huấn luyện, chạy baseline hay chạy lại audit dữ liệu.

## 2. Yêu cầu trực tiếp, diễn giải kỹ thuật và phần mở rộng

| Nội dung | Phân loại | Nguồn và ý nghĩa có thể bảo vệ |
|---|---|---|
| Xây đồ thị phụ thuộc giữa dịch vụ/thành phần và ánh xạ telemetry | **DIRECTLY REQUIRED BY SUPERVISOR**, theo yêu cầu Task C hiện hành; **PRIMARY-SOURCE FACT** cho nội dung tương ứng trong thư | Task C §5; thư DH-MT1/2; DT18-NV2 hiện hành còn nêu log, trace và metrics. Không yêu cầu mọi loại cạnh trong mô tả đích phải hiện diện trong RE2-TT. |
| Phát hiện bất thường và suy luận/xếp hạng trên đồ thị | **DIRECTLY REQUIRED BY SUPERVISOR** ở cấp mục tiêu theo Task C §5 | Có hai đầu ra khác nhau. Thư DH-MT2/3 và DT18-NV2 cùng giữ chúng; không thể lấy MRR thay F1. |
| Đồ thị cần thay đổi trực tiếp anomaly score nếu gọi detector là graph-based | **TECHNICAL INTERPRETATION** | A §D.3; kiểm bằng can thiệp vào graph trong khi giữ nguồn quan sát. Đây là phép phân loại phương pháp, không phải thuật toán do cô chỉ định. |
| Thực nghiệm trên dữ liệu công khai và so cùng điều kiện với giải pháp hiện có | **DIRECTLY REQUIRED BY SUPERVISOR** | Task C §5; thư DH-DATA/DH-DO. Tên benchmark là ví dụ; không bắt buộc chạy mọi tập dữ liệu hay mọi metric. |
| Chia metric detection và ranking, dùng tập ứng viên không có nhãn đáp án | **TECHNICAL INTERPRETATION** cần để đánh giá có nghĩa | A §J; B §12.9–12.14. Yêu cầu này ngăn benchmark đo nhầm bài toán. |
| LLM giải thích kết quả và gợi ý kiểm tra ở bước sau | **DIRECTLY REQUIRED BY SUPERVISOR** theo Task C §5 và thư DH-MT4 | Đầu vào là bằng chứng có cấu trúc sau detector/ranker; không sinh nhãn hay thay cơ chế khoa học. Không tự sửa hệ thống. |
| GNN, PageRank, tái dựng trace, nhiều lớp operation/resource | **OPTIONAL EXTENSION** | Không được suy thành bắt buộc từ ví dụ kỹ thuật. RE2-TT không có GT operation/resource. |
| Thực nghiệm kiểm soát trên FlashTicket sau dữ liệu công khai | **PRIMARY-SOURCE FACT — nhiệm vụ hiện hành do Minh xác nhận** | DT18-NV3. Không tự quy DT18 thành một thư mới của cô. Nhóm Minh/Sơn/Tuấn/Tuyến; Minh phụ trách chính RCA đồng thời có nền tảng chung. |

### Khác biệt provenance phải báo cho main

**PRIMARY-SOURCE FACT:** nguyên văn thư 22/08 §1 không liệt kê PageRank/subgraph/GNN hoặc P/R/F1/MRR/NDCG. A §M trình bày các chi tiết ấy trong cột diễn giải email. **TASK-C INFERENCE:** đây là khác biệt về gán nguồn; không được trích các tên này như nguyên văn thư. Yêu cầu Task C hiện hành §5 đã tự đưa năm bước và quy định cách hiểu ví dụ/metric, nên dùng §5 làm thẩm quyền hiện hành. Không sửa A, không khôi phục tên đề tài cũ, không suy ra xung đột cần dừng việc tạo ứng viên.

## 3. Chuỗi suy luận trước khi đặt câu hỏi

1. **VERIFIED — TASK A:** pipeline có thể tốt ở ranking nhưng không cải thiện detection; A §B/D/J phân biệt rõ hai đích. Graph có nhiều vai trò và prior work đã có cả graph detector lẫn graph ranker.
2. **VERIFIED — TASK B:** RE2-TT chấm được rank dịch vụ trên 90 case; cửa sổ injection chỉ là nhãn chế độ thí nghiệm, không phải onset bất thường độc lập. Không chấm F1 từng node, operation hay causal path.
3. **TASK-C INFERENCE:** câu hỏi thuyết phục cô cần xác định công đoạn nào thật sự hưởng lợi, thay vì viện dẫn một điểm tổng hợp cao để gọi cả pipeline là tốt. Đây là nguồn CF-01.
4. **VERIFIED — TASK A:** MicroRank thu thêm dấu vết sau trigger; CIRCA nhận detect_time và dùng reference/test intervals; BARO có độ trễ phát hiện; các setup đó được mô tả ở A §C.3/4/6. Chất lượng sau khi đã thu đủ dữ liệu khác chất lượng có sẵn sớm trong vận hành.
5. **VERIFIED — TASK B:** dấu thời gian và liên kết parent có thể xây đồ thị quan sát; độ phủ root 90/90 mới được kiểm trên toàn case, không chứng minh mọi tiền tố thời gian cũng có root. **TASK-C INFERENCE:** cần kiểm liệu lợi ích graph còn tồn tại khi bỏ quyền nhìn tương lai và tách chờ dữ liệu khỏi thời gian tính toán. Đây là nguồn CF-02.
6. **VERIFIED — TASK A:** chưa gap nào được xác lập mạnh; hai câu hỏi dưới đây là đóng góp thực nghiệm tiềm năng. Không phương pháp cụ thể nào đã được chọn.

## 4. CF-01 — Giá trị của ngữ cảnh đồ thị ở từng công đoạn phát hiện và chẩn đoán

**Trạng thái:** `CANDIDATE / TASK-C INFERENCE`. **Phạm vi khả thi:** sống với claim thu hẹp trên RE2-TT; muốn claim phát hiện vận hành phải có kiểm chứng kiểm soát bổ sung.

| Trường hợp đồng | Nội dung |
|---|---|
| CANDIDATE ID / tên | **CF-01 — Giá trị của ngữ cảnh đồ thị ở từng công đoạn phát hiện và chẩn đoán** |
| Research Question | Khi giữ tập telemetry, ngân sách học/hiệu chỉnh và tập ứng viên như nhau, đưa quan hệ dịch vụ quan sát được vào phép chấm bất thường có cải thiện phát hiện chế độ injection và xếp hạng root dịch vụ so với chỉ dùng đồ thị sau detector; lợi ích hoặc tổn hại xảy ra ở công đoạn nào? |
| Vì sao khoa học đáng quan tâm | Tách hiệu ứng graph lên phát hiện khỏi hiệu ứng graph lên xếp hạng; kiểm trường hợp F1 tốt hơn nhưng root rank xấu đi, hoặc rank tốt nhưng detector bỏ sót. Trả lời một vấn đề về validity của cả pipeline, không dùng độ phức tạp để chứng minh đóng góp. |
| Prior work gần nhất | A §C.7 Eadro và §C.12 ARMOR cho graph trực tiếp tác động detector/ranker; §C.2/3 MicroRCA/MicroRank dùng graph sau detection; CIRCA graph-conditioned score nhưng nhận thời điểm sự cố ngoài hệ thống. |
| Chưa được giải quyết theo A | A §L coi kiểm tra giá trị graph dưới input/local-evidence/candidate controls là NEEDS MORE EVIDENCE. Các ablation Eadro/DéjàVu đã tồn tại nên phép bỏ graph đơn giản không đủ mới; câu hỏi hẹp còn lại là phân rã lợi ích theo công đoạn và lỗi nối tiếp trong điều kiện matched information. Không khẳng định chưa paper nào làm điều này. |
| Bằng chứng Task B làm testable | B §12.6/7: dựng được observed service relations; §12.9/12: root dịch vụ và injected windows có sẵn; §12.10: cấm oracle cho detector. Ledger A-001/2/7/8, B-002/4/5, M-001/5. |
| Đơn vị thí nghiệm chính | Một incident/case giữ nguyên giữa mọi biến thể. System-time-bin dùng chấm detection; các bin trong cùng case không là mẫu độc lập. Dùng case/scenario làm đơn vị uncertainty. |
| Dataset/subset | RE2-TT pinned revision của B; dùng mọi case đủ điều kiện theo chính sách tiền đăng ký, giữ case thiếu log và parent coverage thấp. Không giả định đã có corpus đầy đủ tại máy; B2 chỉ lưu kết quả audit trace. |
| Telemetry đầu vào | Metrics và trace statistics với graph service từ parent resolved; logs chỉ khi quy tắc availability/join đã được kiểm đúng phạm vi. Căn L–M tại entity-second; với traces chỉ service+time. So graph phải giữ nguyên chính những feature này. |
| Vai trò đồ thị | Một biến thể cho graph vào anomaly scoring; một biến thể giữ detector local và chỉ dùng graph cho ranking; một đối chứng không graph. Đây là các vị trí can thiệp để kiểm RQ, chưa chọn cơ chế lan truyền/học. Cạnh chỉ là trace-derived parent→child relation. |
| Đầu ra chính | Hai đầu ra ghi tách: system-window score/flag và danh sách root-service candidates; thêm kết quả pipeline thành công/thất bại theo case. Không có output node anomaly truth. |
| Ground truth | Injection regime cho thí nghiệm detection giới hạn; root_cause_service cho ranking. Không có onset thực độc lập, tập node bất thường hay path. |
| Họ baseline | Local/statistical detector và ranker độ lệch kiểu BARO; graph-RCA sau detector như họ MicroRCA/MicroRank; graph-context detection như họ Eadro/ARMOR chỉ khi có phiên bản/input/supervision hợp lệ. Giữ chính sách labels-evaluation-only của B: không tùy ý fit baseline supervised bằng root labels. Baseline cần nhãn huấn luyện không được giả là matched unsupervised. |
| Nguyên tắc so sánh | Cùng telemetry/candidate set/split/ngân sách tuning; một block dùng cùng incident boundary để cô lập ranker; một block detector tự chạy, không nhận inject_time. Không đối chiếu trực tiếp số metric từ paper gốc với số RE2-TT. |
| Họ metric | Detection P/R/F1 ở system-time-bin, gọi đúng là agreement với injection regime; ranking MRR/Hit@k theo case. Binary NDCG chỉ phụ nếu cần, không là bằng chứng severity. Báo riêng missed incidents, false alarms và rank coverage; detection fail không được xóa khỏi báo cáo pipeline. |
| H0 | Sau matched-information controls, graph trong detector không cải thiện detection-regime agreement vượt mức ý nghĩa thực tế định trước, hoặc tổn hại chẩn đoán theo case vượt giới hạn được định trước, so với graph chỉ ở ranker. |
| H1 | Graph trong detector cải thiện detection-regime agreement vượt mức ý nghĩa thực tế định trước, đồng thời tổn hại chẩn đoán theo case không vượt giới hạn đã đăng ký. Nếu chỉ ranking tăng thì đó là kết quả phụ hỗ trợ RCA ranking, không hỗ trợ H1 về graph detector. |
| Điều kiện bác bỏ/không ủng hộ | Không có cải thiện detection đáng tin/đáng dùng sau controls; lợi ích biến mất khi bỏ oracle hoặc khi nhóm scenario không trùng train–test; graph chỉ đổi thứ hạng nhưng không đổi anomaly score; hoặc lợi ích detection trả bằng mất chẩn đoán vượt giới hạn đăng ký. Trường hợp thiếu power là chưa kết luận, không tự nhận H0 đúng. |
| Confounders | Graph variant dùng thêm feature hoặc capacity; local scores không cố định ở block ranking; thời gian fit/tuning khác; fault severity, root service và mức missingness; cố định injection schedule; parent resolution không phải completeness topology. |
| Leakage | Không đường dẫn/case/fault/root text/metadata aggregate làm feature; không inject_time cho detector; không graph hợp toàn 90 case hoặc statistics tương lai. Group split toàn incident, thận trọng repeats cùng service×fault; mapping/tuning fit trước test. Không dùng 5 nhãn root làm universe. |
| Độ phức tạp triển khai | Trung bình–cao: cần các interface thay thế từng công đoạn, matching feature budget, evaluator hai nhiệm vụ và kiểm causal time. Không nhất thiết deep learning; nếu chọn hai baseline nặng mà không tái lập được, giá trị so sánh giảm. Minh còn phụ trách nền tảng; không giả định bốn người cùng làm RCA toàn thời gian. |
| Rủi ro dataset | Cao cho detection claim, vừa cho service ranking. Lịch injection cố định tạo shortcut; thiếu onset độc lập và dữ liệu healthy dài đa workload. Logs/schema metrics chưa được audit toàn subset. |
| Liên quan FlashTicket | Sau public pilot, kiểm mô hình phát hiện/ranking trên telemetry quan sát tốt và các lần chạy tải bình thường/sự cố kiểm soát có nguồn nhãn độc lập. Không để RQ quyết số service/kiến trúc; trao yêu cầu quan sát qua hai cửa đúng governance. |
| OUT OF SCOPE | Graph repair; operation/root-resource accuracy; propagation-path proof; LLM chấm nhãn; learned algorithm family/threshold/window cuối; thay code hệ thống ở Task C. |
| Vì sao có thể không xứng tầm luận văn | Chỉ lặp ablation bỏ graph đã có ở Eadro/ARMOR, hoặc chỉ một bảng F1/MRR trên 90 injection quen thuộc thì đóng góp mỏng. Nếu không cô lập cơ chế và báo failure conditions, nó chỉ là tích hợp/benchmark. |

**Ablation tối thiểu — TASK-C INFERENCE:** giữ feature, bỏ graph; giữ detector, thay graph chỉ ở ranker; giữ ranking protocol, thay graph ở detector; đối chứng cấu trúc không mang quan hệ thực nếu định nghĩa được công bằng. Không buộc mọi baseline dùng chung một score vốn không tương thích với thuật toán gốc: ablation nội bộ và so method hoàn chỉnh là hai bảng riêng.

**Trace missingness:** `SECONDARY ROBUSTNESS ANALYSIS`, giữ nguyên cả case thiếu links và báo theo coverage; không suy nhân quả từ việc hai strata có performance khác nhau. **Operation:** `NOT USED` như đích; nhãn operation chỉ có thể là `SECONDARY EVIDENCE` nếu giữ input nhất quán. **LLM:** tầng sau, giải thích score/rank/coverage đã có, không tham gia metric chính.

**Bổ sung bắt buộc có điều kiện:** RE2-TT đủ cho câu hỏi bị giới hạn bởi injection regime. Claim phát hiện anomalous behavior trong vận hành thật cần healthy controls/onset độc lập trên FlashTicket hoặc dataset bổ sung phù hợp; không gọi điều này đã được public data chứng minh. Public pilot vẫn diễn ra trước FlashTicket theo DT18. Không chốt bộ bổ sung ở đây.

**Task D còn phải định nghĩa — OPEN, Minh quyết sau C2:** primary endpoint và effect size tối thiểu, score/graph mechanism, normal-fit/calibration protocol, leakage-safe split, số đo hợp lý cho detector misses, baseline compatibility và compute budget. Không khóa giá trị nào trong reviewer này.

## 5. CF-02 — Lợi ích chẩn đoán của đồ thị dưới giới hạn bằng chứng theo thời gian

**Trạng thái:** `CANDIDATE / TASK-C INFERENCE`. **Phạm vi khả thi:** service-ranking sau sự cố đã biết; không tuyên bố tự phát hiện sự cố. Không phụ thuộc CF-01 thành công.

| Trường hợp đồng | Nội dung |
|---|---|
| CANDIDATE ID / tên | **CF-02 — Lợi ích chẩn đoán của đồ thị dưới giới hạn bằng chứng theo thời gian** |
| Research Question | Sau một mốc sự cố được cung cấp từ bên ngoài, quan hệ dịch vụ quan sát được có giúp đưa root dịch vụ lên sớm trong danh sách với ít thời gian chờ telemetry hơn phương pháp chỉ dùng bằng chứng cục bộ, khi mỗi kết quả chỉ dùng dữ liệu đã có tại thời điểm phát hành? Lợi ích này đổi thế nào giữa các nhóm lỗi và có còn sau khi tính cả chi phí xử lý? |
| Vì sao khoa học đáng quan tâm | Một rank đúng khi nhìn toàn case có thể không giúp vận hành sớm. RQ kiểm đánh đổi chất lượng–thời gian có bằng chứng, tách thời gian chờ dữ liệu khỏi compute; không tối ưu tốc độ vô nghĩa bằng cách chỉ đo runtime ranker. |
| Prior work gần nhất | A §C.3 MicroRank chờ thêm trace sau trigger; §C.4 BARO tách detector chậm/ranker nhanh; §C.6 CIRCA dùng delay/test intervals; §C.8 TORAI so ranking/runtime sau mốc ngoài. |
| Chưa được giải quyết theo A | Task A ghi các collection/reference/test interval và runtime, nhưng chưa cung cấp một kết luận kiểm soát chung về đường chất lượng theo bằng chứng sẵn có, dưới cùng universe và budget. Đây là thiếu bằng chứng trong pack, không đủ để nói literature chưa giải. Nếu targeted review sau cho thấy cùng RQ đã trả lời, phải thu hẹp hoặc bỏ contribution claim. |
| Bằng chứng Task B làm testable | B §12.6/7 có timestamps/duration/parent IDs; §12.9 có root service; §12.10 cho phép incident boundary ngoài hệ thống. M-005 chỉ chứng minh full-case candidate coverage nên early coverage trở thành kết quả cần báo, không được giả định. |
| Đơn vị thí nghiệm chính | Một case với một quỹ đạo ranking theo các cutoff tiền đăng ký; các cutoff lặp trong case là quan sát phụ thuộc, không tạo thêm N. So paired tại cùng cutoff. |
| Dataset/subset | RE2-TT pinned revision như B; đủ 90 cases cho known-window contract, subject to retrieval/feature validation về sau. Phân tầng theo fault/root/coverage do evaluator giữ, không gửi vào model. |
| Telemetry đầu vào | Trace statistics và metrics đã hoàn thành đến cutoff; logs có thể dùng với luật availability đã khai. Không dùng duration của span chưa hoàn thành như đã biết trong online replay; tính khả thi cột thời gian/đơn vị phải khóa ở Task D từ dữ liệu đã có. Nếu không có timestamp đến collector thì gọi event-time replay, không hứa wall-clock ingest latency. |
| Vai trò đồ thị | Cung cấp quan hệ giữa bằng chứng dịch vụ để hỗ trợ ranking theo prefix. Graph history không vượt cutoff; chỉ parent resolved, không hoàn thiện cạnh bằng kiến trúc/nhãn. Không đòi sửa graph thiếu. |
| Đầu ra chính | Ranked service list tại từng cutoff; đường MRR/Hit@k theo độ trễ thu thập và runtime; coverage/miss và thay đổi rank giữa các cutoff. Không có detector output làm đích chính. |
| Ground truth | Một root service mỗi case. Injection time chỉ mốc benchmark known incident bên ngoài, không là feature và không chứng minh onset thật. Không GT causal chain hoặc anomaly-node. |
| Họ baseline | Ranker local robust deviation kiểu BARO; graph-localization sau incident kiểu MicroRCA; known-window dependency/causal reasoning kiểu CIRCA/RCD/TORAI khi inputs/semantics cho phép. Resource graph của bản gốc không có thì phải khai adaptation, không tự bổ sung resource nodes. Không baseline nào được nhìn dữ liệu muộn hơn comparator. |
| Nguyên tắc so sánh | Cùng raw-input cutoff, candidate universe và graph history; cùng normal/reference access. So đường chất lượng theo thời gian trước; runtime tính riêng trên cùng hardware; chi phí tổng gồm graph building/feature extraction. Không đặt một cutoff thuận lợi cho từng method rồi so như cùng điều kiện. |
| Họ metric | MRR/Hit@k theo case và cutoff; uncertainty cluster theo scenario; độ trễ tới một mức chất lượng do Task D đăng ký là phụ, chưa chọn ngưỡng. Báo tỷ lệ chưa đạt trong observation horizon như censored/failure, không chỉ trung bình trên ca thành công. Rank stability phụ, vì sai ổn định vẫn sai. |
| H0 | Với cùng lượng thông tin đã có, graph không cải thiện đường ranking quality theo thời gian so local evidence, hoặc lợi ích bị triệt bởi graph/feature processing cost. |
| H1 | Graph đem lại cải thiện có ý nghĩa thực tế ở phần quỹ đạo được định trước hoặc đạt chất lượng đã định trước sớm hơn, sau khi giữ công bằng candidate/input/cost và công bố nhóm lỗi nơi graph gây hại. Không đòi lợi ích đồng đều mọi nhóm. |
| Điều kiện bác bỏ/không ủng hộ | Lợi ích biến mất khi cấm full-case graph/statistics; chỉ tồn tại khi bỏ case root chưa xuất hiện; mọi lợi ích sớm mất sau tính compute; comparator local đạt chất lượng tương đương; hoặc khác biệt chỉ thuộc một nhóm nhỏ không đủ lặp. Không suy H1 từ endpoint tốt tại cutoff chọn sau khi xem kết quả. |
| Confounders | Prefix ngắn làm thiếu candidate/links; startup/traffic volume; fault intensity và nhóm lỗi; graph built bằng future data; số cutoff/horizon tạo multiple testing; repeated runs cùng configuration; runtime parsing/I/O khác nhau; missing links gắn với fault thay vì ngẫu nhiên. |
| Leakage | Cấm path/metadata labels trong pipeline. Không union 27 services/55 relations từ toàn corpus làm graph online. Universe phải chung giữa comparator ở mỗi cutoff, root vắng vẫn tính miss; báo conditional coverage chỉ là phân tích phụ. Không full-case normalization, imputation bằng tương lai, log parser học test tương lai hay chấm completion của span chưa kết thúc. |
| Độ phức tạp triển khai | Trung bình: replay prefix/evaluator nghiêm ngặt và phép so paired; graph theo dịch vụ nhỏ nhưng raw traces lớn nên feature preparation/I/O có thể chi phối. Không cần thêm framework như điều kiện định nghĩa RQ. Complexity sẽ tăng nếu mở thành adaptive online learning, vì vậy phần đó ngoài phạm vi. |
| Rủi ro dataset | Vừa: có dữ liệu thời gian và service GT; thiếu telemetry arrival time và independent onset giới hạn latency claim. Coverage root tại prefix chưa biết. Chỉ ba repeats mỗi scenario; 90 case không phải 90 môi trường độc lập. |
| Liên quan FlashTicket | Dùng contract biết được bằng chứng nào vào lúc nào, với observability tốt, để đánh giá khi nào danh sách gợi ý đủ hữu ích. FlashTicket có thể bổ sung arrival timestamps và alert/injection/event timing độc lập; chưa ép bổ sung API hoặc infrastructure nào trong Task C. |
| OUT OF SCOPE | Tự động phát hiện onset làm đóng góp chính; sửa trace/topology; operation/resource GT; nguyên nhân đa gốc; online adaptive learner; LLM chọn thời điểm/nguyên nhân; thuật toán/cutoff cuối; quy định SLO vận hành từ kết quả benchmark. |
| Vì sao có thể không xứng tầm luận văn | Chỉ quét kích thước cửa sổ để tune một ranker là đánh giá tham số thông thường. RQ chỉ có giá trị nếu đưa ra insight có thể bác bỏ về lợi ích graph, failure conditions và chi phí thông tin, với controls rõ. Prior work có thể đã có sensitivity tương đương mà Task A chưa khảo sát đủ. |

**Ablation tối thiểu — TASK-C INFERENCE:** graph-free với đúng feature budget; graph build causal-time so với cùng graph rule áp full-case như đối chứng oracle chỉ để chỉ rõ optimism, không trình oracle như kết quả deployable; tách graph construction/feature/ranking runtime; giữ universe và thay evidence horizon. Mọi oracle upper bound phải gắn nhãn riêng, không cấp vào kết quả chính.

**Trace missingness:** `KNOWN LIMITATION` và `SECONDARY ROBUSTNESS ANALYSIS`; nghiên cứu thiếu bằng chứng vì cutoff không đồng nghĩa nghiên cứu mất trace hay tái dựng topology. **Operation:** `NOT USED` làm đích; có thể `INTERMEDIATE REPRESENTATION` cho trace aggregate nhưng không được chấm operation accuracy. **LLM:** sau mỗi evidence packet, chỉ nêu rank, evidence cutoff và giới hạn; không thay đổi rank/GT.

**Phù hợp giảng viên:** đáp ứng trực tiếp graph reasoning và baseline RCA trên public data; detector vẫn là một chức năng riêng của toàn hệ thống, không được tuyên bố CF-02 hoàn thành graph anomaly detection. Nếu người hướng dẫn đòi đóng góp khoa học chính phải nằm ở graph-conditioned detector, CF-02 chưa đủ tự thân. Yêu cầu Task C §5 hiện cho phép graph AD/graph reasoning; không tự bỏ nhiệm vụ phát hiện trong DT18.

**Dữ liệu bổ sung:** không bắt buộc dataset thứ hai để chấm known-incident service-ranking theo event time. FlashTicket controlled validation bắt buộc ở cấp nhiệm vụ DT18; arrival-time/healthy regimes cần khi nâng claim sang hiệu quả vận hành thực. Không buộc collection mới để cứu operation/causal claims không thuộc RQ.

**Task D còn phải định nghĩa — OPEN, Minh quyết sau C2:** cutoff grid và observation horizon, primary quality summary, effect size, completion/availability semantics, graph history/reference fitting, same-candidate policy, censored cases, grouped uncertainty, baseline adaptation và compute accounting. Không chọn giá trị cụ thể ở đây.

## 6. Điều kiện chung để hai hướng có thể được bảo vệ

- **Construct validity:** CF-01 detection label chỉ chế độ injection; CF-02 thời gian là known-boundary/event-time cho đến khi có arrival timestamps. Root service không là mọi service bị ảnh hưởng. Trace relation không là causal relation.
- **Internal validity:** controls giữ đầu vào và cutoff, ngăn thông tin tương lai, tách ablation nội bộ khỏi exact baseline reproduction; cấm metric hoặc candidate được lựa chọn sau khi thấy nhãn test. Thất bại/timeout/absence phải được lưu, không chỉ ca chạy được.
- **External validity:** RE2-TT một system và sáu fault labels, ba repeats; không nói kết quả áp dụng mọi microservice, fault logic hoặc production workload. Public data và FlashTicket có vai trò bổ sung, không thế chỗ nhau.
- **Reproducibility:** pin revision/checksum, lưu split manifest do evaluator quản lý, parser/version, cutoff provenance, feature and graph construction, configuration/seed nếu stochastic, outputs từng case và failure logs. Audit JSON không thay telemetry để chạy thí nghiệm.
- **Phạm vi triển khai:** chỉ một câu hỏi chính được Minh khóa ở C2; không ghép hai hướng thành hai đề tài song song. Logs/traces/metrics cần cho nghĩa vụ DT18 tổng thể nhưng việc thêm modality phải có điều kiện alignment, không tự tạo novelty.
- **Ngân sách và đóng góp:** chưa định mức compute/tuần công và chưa xác minh mọi baseline chạy được. Có thể chọn cách thống kê đơn giản nếu trả lời RQ; không lựa chọn thuật toán trong Phase 1. Một kết quả âm có thể có giá trị thực nghiệm nếu controls và giới hạn có sức thuyết phục; không tự bảo đảm đạt chuẩn luận văn.

## 7. Những hướng chưa phát triển thành ứng viên riêng

| Hướng xem xét từ bằng chứng | Lý do không thêm candidate để đủ số |
|---|---|
| LLM giải thích là đóng góp chính | Task C §6 đặt downstream; A §L nói evidence gap yếu và cần survey riêng. Không có rubric/expert ground truth trong B. Giữ nghĩa vụ sản phẩm phía sau. |
| Tái dựng topology/trace thiếu | B chứng minh incomplete observed links, không cung cấp complete truth để chấm repair; Task C không mặc định đây là đóng góp chính. Chi phí/rủi ro không được biện minh bằng yêu cầu giảng viên. |
| Operation hoặc causal-path localization | B thiếu GT. Biểu diễn operation không cấp nhãn và LLM không bù được. |
| Thêm ba modality/GNN làm luận điểm mới | A chứng minh prior work dày. Công nghệ hoặc số nguồn quan sát không là câu hỏi khoa học. |

## 8. Bàn giao và tự kiểm

- **Quyết định:** không có quyết định mới; CF-01/CF-02 là CANDIDATE. Không xếp thứ hạng, không chỉ định winner hoặc thuật toán.
- **Giả định:** triển khai tương lai chỉ sau C2/Task D; baseline phải có input/label policy tương thích; cảnh báo known-window chỉ là protocol ngoài hệ thống, không input oracle detector.
- **Tệp ghi:** duy nhất `D:/Project/flash-ticket-rca-research/task-c/phase-1-independent-candidates/reviewer-f.md`.
- **Kiểm tra nội dung:** đủ RQ/H0/H1/falsification, unit/input/graph/output/GT, baseline/metrics/controls, confounders/leakage, implementation/data risk, FlashTicket/out-of-scope/điều kiện không xứng tầm; phân biệt detection/ranking và provenance thư/Task C.
- **Audit hợp nhất:** main thực hiện audit governance và xác nhận toàn bộ file-set khi tổng hợp; C-F không chạy audit dataset và không thay artifact bằng chứng.
- **OPEN:** khoảng trống literature của cả hai hướng chưa chứng minh mới; effect size, nguồn lực, baseline khả dụng, requirement về trọng tâm detection/graph reasoning, validation vận hành và RQ cuối cần quyết ở C2/Task D.
- **Đưa vào báo cáo chính thức sau này:** tách nhiệm vụ/metric; nguồn cạnh và thời điểm hiệu lực; kết quả âm và coverage failures; giới hạn nhãn; attribution đúng giữa thư lịch sử và DT18 hiện hành. Không mang proposal này vào báo cáo như kết quả đã đo.

**KẾT THÚC REVIEW ĐỘC LẬP C-F — 2 ứng viên; chưa hợp nhất; chưa xem ứng viên reviewer khác.**
