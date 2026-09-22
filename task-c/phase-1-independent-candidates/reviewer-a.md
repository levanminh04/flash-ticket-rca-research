# Task C — Reviewer C-A: câu hỏi nghiên cứu từ tính khả bác bỏ và giá trị khoa học

- Ngày: 2026-09-20.
- Vai trò: reviewer phương pháp luận độc lập; tiếp tục chính lượt C-A bị gián đoạn.
- Trạng thái thực thi: **COMPLETE — INDEPENDENT SUBMISSION COMPLETE**.
- Trạng thái học thuật: `DRAFT`; mọi hướng dưới đây là `CANDIDATE`, chưa được chọn hoặc duyệt.
- Ý định: `EXECUTE` trong đúng phạm vi tạo báo cáo độc lập; tạo tác `FORMATION`.
- Không đọc proposal từ hội thoại cũ, E1, A10, phương pháp cũ hoặc file ứng viên của reviewer khác. Không sinh subagent; không chọn thuật toán, công thức, ngưỡng hay hướng thắng.
- Phục hồi theo yêu cầu hiện hành: dùng lại phần nguồn đã đọc trong lượt C-A và evidence ledger; không khởi động lại khảo sát hoặc audit.

## 1. Nguồn, quy ước và giới hạn độc lập

Ký hiệu nguồn:

- **A:** `D:/Project/flash-ticket-platform/docs/research-rca/task-a-ban-do-bang-chung-doc-lap.md`. Đã đọc toàn bộ báo cáo, gồm pipeline C.2–C.12, taxonomy B/D, đánh giá J, bảng khoảng trống L và red team Q.
- **B:** `D:/Project/flash-ticket-rca-research/dataset-audit/TASK-B-RCAEval-audit.md`. Đã đọc toàn bộ; **§12 là kết luận CLOSED**, §1–§11 là lịch sử được giữ nguyên.
- **R:** `D:/Project/flash-ticket-rca-research/audits/rcaeval/`. Đã đọc đủ 11 báo cáo bắt buộc: metadata A; trace B; graph C; metrics D; logs E; leakage F; reproducibility G; red team H; ground truth I; full trace J; resource observability. Các báo cáo có phạm vi mẫu không được nâng thành kết luận toàn tập.
- **L:** `D:/Project/flash-ticket-rca-research/task-c/task-c-evidence-ledger.md`, đọc trước khi tiếp tục recovery; dùng ID của ledger để truy vết.
- **M:** các kết quả JSON đã lưu của Task B. Đã mở `re2tt-trace-full-subset-audit.json` để đối chiếu schema/identity/parent-resolution và `re2tt-target-candidate-coverage.json` để kiểm giới hạn candidate coverage. Không chạy lại audit dữ liệu thô.
- **G:** root `AGENTS.md`, skill `govern-capstone-work` và reference `project-authority-and-gates.md`, nguồn `DT18-*`, `docs/project/roles.md`. Đã đọc để giữ đúng nhiệm vụ, quyền quyết định và phân công; không lấy thiết kế nghiên cứu cũ làm đầu vào.

Các nhãn `VERIFIED — TASK A`, `VERIFIED — TASK B`, `VERIFIED — MACHINE EVIDENCE`, `PRIMARY-SOURCE FACT` chỉ phân loại nguồn của `FACT`; `TASK-C INFERENCE` là suy luận ứng viên, không phải quyết định. Những lựa chọn cần người duyệt hoặc Task D được giữ `OPEN`.

Độc lập ở đây nghĩa là độc lập **trong hình thành câu hỏi** trước khi xem kết quả C-B/C-C hoặc reviewer khác. Các reviewer dùng chung A/B, nên không tuyên bố độc lập về nguồn dữ liệu. C-A không thực hiện một kiểm toán dữ liệu mới và không xác minh lại toàn bộ paper gốc qua web.

## 2. Chuỗi suy luận trước khi đặt câu hỏi

| Bằng chứng | Phân loại | Hệ quả phương pháp luận của C-A |
|---|---|---|
| Detection, biểu hiện bất thường, xếp hạng root, kiểm chứng nhân quả và giải thích là các task khác nhau — A B.1/B.2/D/J; L A-001 | VERIFIED — TASK A | Không dùng điểm RCA để chứng minh detector hoặc cơ chế nhân quả. |
| Graph có nhiều vai trò; các phương pháp và ablation đã có tiền lệ — A C.2/C.6/C.7/C.9, D/F/L; L A-002/A-005 | VERIFIED — TASK A | Câu hỏi cần cô lập một yếu tố thông tin hoặc một điều kiện sử dụng, thay vì đếm công nghệ. |
| B §12.9/12.12 cho nhãn root **service**, không cho operation/affected-node/path labels — L B-002/B-003 | VERIFIED — TASK B | Ưu tiên đầu ra service ranking có thể chấm; không gán root service thành toàn bộ tập node bất thường. |
| 90 case có metrics/traces; 89 có logs; nhãn phủ năm service, sáu fault, ba repeat — B §12.4; L M-001/M-002 | VERIFIED — TASK B | Có thiết kế ghép cặp theo case, nhưng cỡ mẫu suy luận không phải số span hoặc số cửa sổ. |
| M cho 90 trace files, 27 service literals toàn tập, 161 cặp literal service–operation và parent resolution không đồng đều — L M-003/M-004/M-006 | VERIFIED — MACHINE EVIDENCE | Graph là quan hệ quan sát được; không có cơ sở gọi graph đầy đủ hoặc causal. |
| Root nằm trong trace candidate set của 90/90 **toàn case**, mỗi case 20–27 service — B §12.9; L M-005 | VERIFIED — TASK B | Tính đánh giá được của RCA toàn cửa sổ không tự chứng minh coverage tại mọi thời điểm sớm. |
| MicroRank thu thêm trace sau trigger; BARO có detection delay; các bài dùng cửa sổ/normal histories khác nhau — A C.3/C.4/C.6/C.9/C.12 | VERIFIED — TASK A | Độ chính xác cuối cửa sổ chưa đủ biểu diễn thời gian phải chờ có bằng chứng chẩn đoán. Đây là suy luận C-A, chưa phải khoảng trống literature đã xác lập. |
| Task A không có gap nào đạt STRONG CANDIDATE — A L/Q; L A-006 | VERIFIED — TASK A | Cả hai hướng dưới đây chỉ là câu hỏi có thể bảo vệ để qua gate; không có tuyên bố mới. |

Từ chuỗi này, C-A giữ **hai câu hỏi khác nhau về đại lượng cần ước lượng**: giá trị bổ sung của quan hệ quan sát được khi lượng bằng chứng cố định; và chất lượng thứ hạng theo thời gian tích lũy bằng chứng. Câu thứ hai không được sinh ra để sửa trace thiếu. Chúng chưa phải shortlist sau phản biện.

## 3. CA-01 — Giá trị chẩn đoán bổ sung của quan hệ dịch vụ sau khi cố định bằng chứng cục bộ

### Candidate contract

| Trường | Nội dung |
|---|---|
| **CANDIDATE ID** | **CA-01** |
| **Working title** | Giá trị chẩn đoán bổ sung của quan hệ dịch vụ sau khi cố định bằng chứng cục bộ. |
| **Research Question** | Với RCA được cung cấp cửa sổ sự cố đã biết, quan hệ dịch vụ suy ra từ trace có cải thiện thứ hạng root service so với chính bằng chứng bất thường cục bộ đó khi giữ nguyên telemetry, khoảng quan sát, candidate universe và ngân sách hiệu chỉnh; và mức cải thiện có còn sau các đối chứng làm mất thông tin quan hệ nhưng giữ những thuộc tính gây nhiễu thích hợp của graph không? |
| **Why this is scientifically interesting** | `TASK-C INFERENCE`: phân biệt lợi ích của **quan hệ** với lợi ích do có thêm feature, lọc bớt ứng viên hoặc ưu tiên service xuất hiện nhiều. Một kết quả không có lợi ích, hoặc lợi ích chỉ xuất hiện trong điều kiện hẹp, vẫn trả lời được câu hỏi. Đóng góp tiềm năng là thực nghiệm về điều kiện sử dụng graph; chưa phải thuật toán mới. |
| **What prior work is closest** | `VERIFIED — TASK A`: MicroRCA dùng cùng detector cho một số baseline localizer (A C.2); Eadro thay GAT bằng FC và bỏ modality (A C.7); DéjàVu có w/o aggregation và xóa cạnh (A C.9); CIRCA dùng parents để định nghĩa conditional residual (A C.6). BARO là họ chứng cứ thống kê không graph (A C.4). Không coi tất cả là baseline tái lập nguyên bản trên RE2-TT. |
| **What remains unresolved according to Task A** | A L gọi phép kiểm giữ input/local score/candidate cố định rồi thay graph là `NEEDS MORE EVIDENCE`, không phải gap đã chứng minh. `TASK-C INFERENCE`: điểm cần kiểm là thông tin quan hệ có thực sự giúp xếp root trong một tập thí nghiệm cùng điều kiện, ngoài hiệu ứng topology đơn giản. `OPEN`: các ablation gần nhất đã kiểm đầy đủ đối chứng tương đương này chưa? |
| **What Task-B evidence makes it testable** | `VERIFIED — TASK B`: B §12.7 cho graph quan sát từ parent references đã resolve; §12.9 cho root service; §12.10 cho leakage policy; §12.12 xác nhận graph ablation và ranking đánh giá được; §12.11 yêu cầu giữ case graph thiếu. L B-002/B-004/B-005, M-005. Ground-truth graph hoàn chỉnh không cần cho estimand này vì đối tượng là **giá trị của graph quan sát được**. |
| **Primary experimental unit** | Một fault-injection case; các điều kiện graph được ghép cặp trên cùng case. Repeat của cùng tổ hợp service–fault là quan sát có khả năng phụ thuộc, phải phản ánh trong split và uncertainty. Span và window không phải các lần lặp độc lập. |
| **Input telemetry** | Metrics theo literal entity và trace timestamps/duration/identity/parent links theo schema hỗ trợ. Nhánh chính có thể dùng metrics + traces cho cả 90 case. Log chỉ là nhánh mở rộng có luật availability/join riêng, được cấp đồng đều cho các đối chứng. Không dùng fault/root label để chọn feature. |
| **Graph role** | Mang quan hệ giữa các service vào bước suy luận/xếp hạng; node là exact service literal, edge là resolved trace-derived service relationship. Câu hỏi hiện cô lập giá trị graph ở RCA, không tự tuyên bố detector đã graph-based. Không chọn cơ chế lan truyền hay mô hình. |
| **Primary output** | Một danh sách service có thứ tự trên tập ứng viên hình thành từ telemetry được phép nhìn thấy. Đầu ra phụ: chênh lệch chất lượng giữa các điều kiện graph theo case. |
| **Ground truth** | `root_cause_service` chỉ cho evaluator. Tất cả baseline dùng cùng candidate universe; không giới hạn vào năm tên injected service. Nhãn không đánh giá được affected nodes hoặc causal paths. |
| **Expected baseline family** | Xếp hạng bằng bằng chứng cục bộ không quan hệ; cùng cơ chế xếp hạng nhưng ablate thông tin graph; graph chỉ mang thông tin cấu trúc đơn giản; đối chứng quan hệ bị hoán đổi theo luật bảo toàn thuộc tính gây nhiễu do Task D xác định. Baseline RCA thống kê/graph hiện hữu chỉ được thêm khi đáp ứng input, supervision và output contract; mọi adapter phải ghi rõ. |
| **Evaluation family** | MRR và Hit@k/AC@k theo định nghĩa service-single-root; chênh lệch ghép cặp, độ bất định theo case/scenario và báo cáo theo fault/service strata. Có thể dùng NDCG với binary relevance nhưng không gọi là mức độ nhân quả. Không báo service/node anomaly F1. |
| **Null hypothesis — H0** | Khi kiểm soát bằng chứng cục bộ và candidate universe, graph quan sát không mang lại cải thiện service ranking đạt mức ý nghĩa thực tiễn đã định trước so với baseline không quan hệ; hoặc lợi ích quan sát được được giải thích tương đương bởi đối chứng cấu trúc không mang đúng quan hệ. |
| **Alternative hypothesis — H1** | Graph quan sát cải thiện ranking vượt mức ý nghĩa thực tiễn đã định trước so với các đối chứng phù hợp, và lợi ích còn ở các nhóm case được giữ ngoài bước xây dựng/hiệu chỉnh, không chỉ một target/fault quen thuộc. |
| **Falsification condition** | H1 không được hỗ trợ nếu không vượt đối chứng sau kiểm soát, lợi ích mất khi khóa candidate universe/feature budget, hoặc chỉ đến từ một nhóm case được dùng để hiệu chỉnh. Kết quả bất định rộng là **chưa đủ bằng chứng**, không tự coi H0 đã đúng. Phát hiện leakage vô hiệu thí nghiệm; phải sửa protocol chứ không diễn giải thành thất bại khoa học của graph. |
| **Main confounders** | Root có thể là node nhiều traffic/nhiều metric; các service có số feature khác nhau; topology và workload liên hệ; các repeat không độc lập; khác năng lực mô hình/tuning; graph quality tương quan fault/service; lựa chọn chỉ giữ case tốt; volume triệu chứng cao có thể nằm ở service bị ảnh hưởng. |
| **Main leakage risks** | Path/case/fault/root strings; graph union trên test/future; candidate universe lấy từ năm target; normal reference chứa phần fault; normalization nhìn toàn case; dùng ground truth để chọn graph, chiều edge hoặc loại case. Chỉ evaluator được đọc labels; boundary inject_time chỉ có vai trò external known-window theo B §12.10. |
| **Expected implementation complexity** | `TASK-C INFERENCE`: trung bình cho thí nghiệm RCA hữu hạn, cao hơn nếu cố tái lập nhiều mô hình supervised không tương thích. Phần khó là kiểm soát đối chứng và loader, không phải số layer. Chưa ước lượng runtime bằng số; chưa benchmark compute. |
| **Expected dataset risk** | Trung bình: nhãn đúng task, graph dựng được nhưng không hoàn chỉnh; raw metrics/log prevalence chưa được kiểm toàn tập; 90 case và ba repeat hạn chế uncertainty; không có independent physical-cause proof. Dữ liệu trace audit đầy đủ không đồng nghĩa raw corpus đã sẵn sàng ở máy. |
| **FlashTicket transfer relevance** | Kiểm xem quan hệ thực sự mang thêm ích lợi trên tình huống giao dịch và tải khác sau khi public experiment hoàn tất. FlashTicket cần xác minh lại mapping, coverage và kết quả; không lấy kết quả RE2-TT thay cho kiểm thử FlashTicket, không sửa ranh giới dịch vụ để thuận lợi cho RCA. |
| **What must remain OUT OF SCOPE** | Khôi phục cạnh/span, học resource graph, operation-root accuracy, causal-path correctness, tự động sửa nghiệp vụ, tuyên bố phương pháp mới chỉ vì có graph, biến phương pháp xếp hạng thành detector end-to-end trong tên gọi. |
| **Why this may NOT be thesis-worthy** | Có nguy cơ chỉ là lặp lại ablation đã có. Nếu tất cả khác biệt chỉ là một bảng w/o graph trên một benchmark, hoặc không xác lập được điều kiện có thể khái quát/cơ chế sai khác, đóng góp có thể quá nhỏ cho tiêu chuẩn luận văn. Không được cứu bằng cách thêm GNN hoặc nhiều modality. |

### Giới hạn và điều kiện giữ CA-01

- **Construct validity:** `TASK-C INFERENCE` — estimand là hiệu quả xếp **nhãn injected root service**, không phải chứng minh đã phân biệt mọi symptom/root theo cơ chế vật lý. Hiệu ứng của graph trong thuật toán cũng không chứng minh các cạnh có nghĩa causal.
- **Internal validity:** khóa local evidence cho so sánh chính; tách thí nghiệm so toàn pipeline khỏi phép cô lập graph. Bỏ graph mà đồng thời bỏ trace-derived features sẽ đổi hai yếu tố và không trả lời RQ.
- **External validity:** một deployment/fault suite và năm target là giới hạn. FlashTicket bổ sung một domain kiểm chứng có kiểm soát; không đại diện production nói chung. Dataset thứ hai hữu ích, chưa bắt buộc để kiểm RQ hẹp trên RE2-TT; bắt buộc thu hẹp claim nếu chỉ có một collection.
- **Reproducibility:** giữ revision, rule tạo node/cạnh, telemetry cutoff, candidate count, fit/test partition, ngân sách tuning và seed của đối chứng. Raw GT không được vào feature/calibration; normal telemetry có thể dùng theo giao thức đã khóa. Task D phải quy định effect-size tối thiểu và uncertainty trước khi xem kết quả test.
- **Trace missingness:** `SECONDARY ROBUSTNESS ANALYSIS`; báo parent-resolution theo case và stratum. So low/high coverage chỉ là phân tích quan sát, không chứng minh missingness gây ra thay đổi ranking. Không sửa graph để giữ H1.
- **Operation role:** `NOT USED` trong biểu diễn chính; không cần operation labels cho mục tiêu service ranking.
- **LLM role:** downstream; diễn giải ranked evidence sau phương pháp. Không dùng lời giải thích để chấm root hoặc tạo ground truth.
- **Supervisor alignment:** trực tiếp phục vụ dependency graph, graph reasoning và RCA baseline. Nếu yêu cầu detector graph-based được hiểu nghiêm ngặt, CA-01 một mình chưa hoàn thành nhiệm vụ detector; phần đó cần contract riêng và nhãn tương ứng, không được đổi tên để lấp chỗ trống.
- **Điều kiện bỏ:** targeted verification cho thấy cùng câu hỏi/đối chứng/điều kiện đã được giải đủ; hoặc không thể tạo baseline công bằng mà vẫn giữ đúng input/GT contract. Phản biện về độ mới là `MAJOR` còn mở, không giả vờ đã giải quyết.

## 4. CA-02 — Thời gian tích lũy bằng chứng và độ ổn định của thứ hạng root service

### Candidate contract

| Trường | Nội dung |
|---|---|
| **CANDIDATE ID** | **CA-02** |
| **Working title** | Thời gian tích lũy bằng chứng và độ ổn định của thứ hạng root service sau mốc sự cố đã biết. |
| **Research Question** | Trong RCA nhận mốc sự cố đã biết, graph reasoning có giúp đưa root service lên đầu danh sách **sớm và ổn định hơn theo lượng thời gian telemetry đã quan sát** so với xếp hạng cục bộ trên cùng các prefix, hay lợi ích chỉ xuất hiện khi được phép nhìn toàn cửa sổ lỗi? |
| **Why this is scientifically interesting** | `TASK-C INFERENCE`: endpoint MRR không phân biệt phương pháp hữu ích sớm với phương pháp chỉ đúng sau khi chờ nhiều dữ liệu, hoặc thứ hạng đúng thoáng qua rồi đảo chiều. Câu hỏi khảo sát chất lượng quyết định khi bằng chứng đến dần, không đánh đồng runtime thuật toán, độ trễ phát hiện và thời gian tích lũy dữ liệu. Đóng góp tiềm năng là một đánh giá temporal service-RCA có đối chứng, chưa phải chính sách dừng mới. |
| **What prior work is closest** | `VERIFIED — TASK A`: MicroRank có trigger rồi thu thêm khoảng năm phút trace (A C.3); BARO tách detector có delay khỏi ranker nhanh (A C.4); CIRCA/DéjàVu sử dụng các reference/test windows (A C.6/C.9); ARMOR có persistent detection delay (A C.12). Đây là các điểm tựa cho vấn đề thời gian; không khẳng định các paper chưa từng có window-sensitivity ngoài phần Task A ghi nhận. |
| **What remains unresolved according to Task A** | Task A J yêu cầu tách detection latency khỏi ranking và giữ đúng evaluation unit; các pipeline C dùng các lượng lịch sử/cửa sổ khác nhau. `TASK-C INFERENCE`: A chưa thiết lập câu trả lời so sánh về đường cong **đúng và ổn định của service rank theo prefix** trên cùng case/candidate contract. `OPEN`: cần xác minh hẹp xem MicroRank, BARO hoặc các graph localizer gần nhất đã đánh giá đúng estimand này chưa; A không đủ để gọi đây là gap mạnh. |
| **What Task-B evidence makes it testable** | B §12.4/12.9 cho mốc injection và root-service target hợp lệ ở 90 case; §12.6 có trace timestamps/identity; §12.12 cho known-window RCA; §12.10 cho phép boundary trong đúng setting này. L M-001/M-005/B-005: coverage đã biết chỉ cho toàn case, vì thế ở mỗi prefix phải tính lại candidate coverage và ghi thất bại nếu root chưa quan sát được. Không cần operation/path labels để chấm rank tại các prefix. |
| **Primary experimental unit** | Một case với cả quỹ đạo các prefix được xem là một quan sát có cấu trúc. Các prefix cùng case phụ thuộc nhau; repeat cùng service–fault cũng phải xử lý phụ thuộc. Không coi từng timestamp hoặc span là một thử nghiệm độc lập. |
| **Input telemetry** | Metrics và trace records nằm trong prefix được phép nhìn thấy; lịch sử tham chiếu có trước boundary theo known-window protocol. Logs chỉ có thể thêm với availability/join contract công bằng. Phép replay ban đầu là **offline theo thời gian ghi nhận**, không mặc nhiên là replay theo thời điểm telemetry đến collector. |
| **Graph role** | Graph từ quan hệ đã quan sát được đến cutoff, dùng làm ngữ cảnh suy luận/xếp hạng trên từng prefix. Có thể kiểm graph nền hình thành trước boundary và graph cập nhật tới cutoff như hai điều kiện khác nhau nếu Task D khóa trước; không dùng graph toàn case để hỗ trợ thời điểm sớm. Chưa chọn cơ chế graph reasoning. |
| **Primary output** | Chuỗi ranked service lists tại các cutoff đã định trước; chất lượng ranking theo thời gian quan sát; độ ổn định rank như số lần đổi thứ hạng hoặc giữ root trong top-k. “Đúng ổn định” chỉ là đại lượng đánh giá hồi cứu, không phải tín hiệu dừng có sẵn cho model. |
| **Ground truth** | Root service cố định theo case; injection boundary là mốc quy ước known-window, **không phải onset triệu chứng quan sát độc lập**. Không có nhãn thời điểm sự cố đã trở nên chẩn đoán được. Root chưa nằm trong observable universe ở cutoff phải nhận miss, đồng thời báo coverage riêng. |
| **Expected baseline family** | Xếp hạng thống kê cục bộ và xếp hạng dùng graph chạy trên cùng prefix, cùng lịch sử và candidate rule. Endpoint trên toàn cửa sổ chỉ là điểm tham chiếu dùng nhiều dữ liệu hơn, không được gọi là comparator thời điểm sớm công bằng. Các phương pháp phải chờ đủ cửa sổ được ghi rõ thời gian chưa có output, không giả định sẵn ranking. |
| **Evaluation family** | Đường cong MRR/Hit@k theo observation horizon; summary theo case của đường cong được khóa trước; tỷ lệ chưa đưa được root vào top-k ở cuối horizon; thời gian tới thứ hạng đúng theo định nghĩa hồi cứu; rank stability và uncertainty theo case/scenario. Không bỏ những case không bao giờ đúng rồi chỉ tính thời gian trên case thành công. Không dùng P/R/F1 để đánh giá thời gian ranking này. |
| **Null hypothesis — H0** | Với cùng lượng telemetry quan sát được, graph reasoning không cải thiện chất lượng ranking sớm hoặc độ ổn định vượt mức thực tiễn đã định trước so với local comparator; mọi lợi thế endpoint chỉ do chờ thêm dữ liệu. |
| **Alternative hypothesis — H1** | Trên các case ngoài bước phát triển, graph reasoning đạt đường cong chất lượng ranking sớm tốt hơn và giữ lợi ích qua các prefix tiếp theo, trong cùng ngân sách quan sát và không che giấu case không thành công. |
| **Falsification condition** | Không hỗ trợ H1 khi lợi thế chỉ xuất hiện ở endpoint, mất khi loại future graph/normalization, chỉ tồn tại tại cutoff được chọn sau khi xem test labels, hoặc thứ hạng đúng thoáng qua nhưng không ổn định. Nếu mọi phương pháp đều có rank giống nhau theo thời gian, câu hỏi có kết quả âm; không phát minh detector/dừng sớm để cứu đóng góp. |
| **Main confounders** | Fault type có tốc độ biểu hiện khác nhau; traffic làm tăng tốc thu đủ trace; candidate universe tăng theo thời gian; graph coverage và feature counts đổi; các service hoạt động không đều; normal reference quá ngắn; fault schedule cố định; clock/instrumentation timing bất thường; root có trong metrics nhưng chưa xuất hiện trong trace universe. |
| **Main leakage risks** | Future spans/parent references, graph hoặc statistics của toàn case; sử dụng thời lượng kết thúc case để định nghĩa feature/cutoff thích nghi; chọn “thời điểm đủ tốt” bằng root label rồi đưa lại vào pipeline; path/fault strings; fixed midpoint dùng như detector; chia prefix của cùng case vào train và test. Boundary được cấp ngoài chỉ cho known-window RCA, không dùng để tuyên bố phát hiện tự động. |
| **Expected implementation complexity** | `TASK-C INFERENCE`: trung bình đến cao do cần loader/replay chống look-ahead và kiểm soát graph/candidate tại từng cutoff; không nhất thiết cần mô hình phức tạp. Chưa có bằng chứng runtime/compute cho workload thí nghiệm. Khối lượng phải giới hạn vào một số họ baseline phù hợp, không làm đồng thời detector, adaptive stopping và explainability research. |
| **Expected dataset risk** | Cao hơn nghiên cứu endpoint: Task B chưa kiểm coverage từng prefix; không có telemetry-ingestion time, không có independently observed anomaly onset; timing fields và duration cần contract rõ trước khi giả lập online. RE2-TT đủ cho câu hỏi **offline prefix known-window** với claim hẹp; chưa đủ cho tuyên bố tiết kiệm thời gian xử lý sự cố ngoài thực tế. |
| **FlashTicket transfer relevance** | Controlled validation có thể kiểm những rank sớm có hữu ích khi dữ liệu được thu thực hay không, với collector arrival/completion timing và mốc fault có kiểm soát. Đây là phần xác minh chuyển giao sau public experiment; không tự yêu cầu thêm fault campaign hoặc sửa application scope lúc này. |
| **What must remain OUT OF SCOPE** | Phát hiện onset chính xác, production false-alarm rate, chính sách dừng tự động đã hiệu chỉnh xác suất, operation-root accuracy, trace reconstruction, ground-truth propagation, tự động khắc phục. Không dùng elapsed time-to-injection làm detector input. |
| **Why this may NOT be thesis-worthy** | Có thể chỉ là sensitivity analysis theo độ dài window mà prior work đã làm. Nếu chỉ tạo thêm đường cong MRR tại vài cửa sổ nhưng không thay đổi hiểu biết về chất lượng chẩn đoán/đánh đổi thời gian, đóng góp có thể quá mỏng. Nếu muốn biến thành hệ RCA online hoàn chỉnh thì scope có thể vượt bằng chứng và công sức luận văn. |

### Giới hạn và điều kiện giữ CA-02

- **Construct validity:** thời gian từ injection tới rank đúng không phải thời gian phát hiện triệu chứng, thời gian khắc phục hoặc thời gian người vận hành tiết kiệm được. Quỹ đạo đúng theo ground truth dùng cho evaluator, không tạo một confidence signal cho người dùng.
- **Internal validity:** phải phân biệt hiệu ứng “nhiều evidence hơn” với “graph reasoning tốt hơn”. Tại mỗi cutoff, baseline có cùng observable input và candidate rule. Thay đổi độ phủ candidate phải được báo song song với ranking; không lọc bỏ case thiếu root sớm.
- **Timing constraint:** B chứng minh timestamps và quan hệ quan sát, không chứng minh thời điểm span/log được xuất hoặc collector nhận. Nếu dùng span duration để chỉ cho phép span đã kết thúc, phải xác minh unit/semantics trước trong Task D; không tự coi `startTime` là thời điểm toàn bộ span đã khả dụng. Không chạy kiểm này trong recovery và không tự nâng claim thành real-time.
- **External validity:** injection có lịch cố định và lượng bình thường ngắn không mô phỏng mọi incident thật. Chỉ được nói về các prefix của các case đã kiểm. Claim về operational latency cần FlashTicket controlled validation; dataset công khai thứ hai chưa bắt buộc cho RQ hẹp nhưng hữu ích nếu có cùng time/label contract.
- **Reproducibility:** snapshot, danh sách cutoff, boundary handling, graph construction cutoff, tie rule, candidate update rule, aggregation of curves và cách xử lý never-success phải được Task D khóa trước. Label dùng đánh giá, không dùng chọn thời điểm riêng cho từng case hoặc hiệu chỉnh ranker.
- **Trace missingness:** `KNOWN LIMITATION`, có thể báo `SECONDARY ROBUSTNESS ANALYSIS`; biến chính là observation horizon. Trace chưa quan sát vì cutoff và parent chưa resolve trong full record là hai loại thiếu khác nhau, không được gộp thành cùng “mất trace”.
- **Operation role:** `NOT USED` cho mục tiêu định lượng; literal operation fields không biến thành operation-root ground truth.
- **LLM role:** downstream, có thể mô tả evidence cập nhật và sự thay đổi thứ hạng; không dùng văn bản để chứng minh time-to-correct hoặc tự tin đúng.
- **Supervisor alignment:** phục vụ graph reasoning, so baseline và phân tích hạn chế. Chỉ có known-window ranking chưa đáp ứng một detector graph-based độc lập; không trộn metric detection vào contract này để làm báo cáo đủ cột.
- **Điều kiện bỏ:** closest work đã giải cùng temporal estimand với đối chứng tương đương mà không còn câu hỏi đáng kể; hoặc prefix coverage/timing khiến chỉ có thể so endpoint; hoặc nhóm muốn tuyên bố online delay nhưng không có nguồn arrival/completion phù hợp để xác minh. Không coi thiếu operation GT là lý do loại CA-02 vì output không phải operation.

## 5. Phản biện chung và các hướng không được tự động nâng thành đóng góp

| Ý tưởng có vẻ hợp lý | Đánh giá độc lập của C-A |
|---|---|
| Chấm service/node anomaly F1 từ root-service label | Không đánh giá được: B §12.9/12.12/12.17. Root label không cho toàn bộ affected/anomaly set. |
| Chẩn đoán operation/resource hoặc causal path trên RE2-TT | Không có ground truth tương ứng; B §12.7–12.9. Không cho LLM sinh nhãn. |
| Có ba modality hoặc mô hình graph phức tạp hơn | Prior work đã rõ ở A C.7/C.8/C.12/G. Chưa phải câu hỏi khoa học. |
| Repair topology để khai thác bảy case coverage thấp | Không tự nảy sinh từ Task B; chưa có ground-truth graph đầy đủ hoặc bằng chứng ưu việt so với hướng khác. Giữ missingness là giới hạn/phân tích phụ của hai ứng viên. |
| Giải thích bằng LLM là đóng góp chính | A L ghi cần evidence/survey riêng; không phù hợp việc khóa RQ upstream từ pack hiện có. Giữ downstream theo yêu cầu người dùng. |
| Đo detection theo midpoint lịch injection cố định rồi gọi production detector | Không có construct validity tương ứng; L T-002, B §12.10/12.12. |

Hai ứng viên có thể dùng chung một số hạ tầng đánh giá nhưng **không đồng nghĩa khoa học**: CA-01 ước lượng phần lợi ích do quan hệ khi horizon cố định; CA-02 ước lượng đánh đổi thời gian–chất lượng của quỹ đạo chẩn đoán. Có thể trở thành câu hỏi chính và phụ sau quyết định của người dùng, nhưng C-A không gộp hoặc phân vai lúc này.

## 6. Những điểm OPEN cần giải trước khi chốt hướng

1. **Contribution gate CA-01:** kiểm hẹp ở prior work gần nhất xem đối chứng giữ local evidence/candidate và bảo toàn nuisance topology đã thực sự có chưa. Task A chỉ cho `NEEDS MORE EVIDENCE`; không được nâng thành “chưa ai làm”.
2. **Contribution gate CA-02:** kiểm hẹp xem prior work gần nhất đã đo prefix-wise service ranking, never-success và ổn định rank với cùng observation budget chưa. Sự vắng mục này trong Task A không là bằng chứng vắng trong literature.
3. **Scope value judgment:** người dùng/giảng viên cần quyết định liệu đóng góp thực nghiệm có điều kiện, gồm kết quả âm, có đủ cho mục tiêu luận văn hay đòi một cải tiến phương pháp. Đây không phải điều code/dataset tự trả lời.
4. **Detection responsibility:** nếu muốn detector graph-based là contribution định lượng chính, phải định nghĩa task/label contract khác có nguồn phù hợp. Hai ứng viên không tự bao trùm yêu cầu đó; chưa chỉ định dataset bổ sung hoặc detector.
5. **Task D sau quyết định:** định nghĩa protocol, effect-size thực tiễn, baseline adapters, feature/graph/candidate cutoff, statistical uncertainty và luật falsification cụ thể. Không có algorithm/window/threshold nào được chọn tại đây.

Không thực hiện web verification, tải thêm dữ liệu, cài package, huấn luyện, sửa audit/script/application hoặc chạy baseline trong lượt C-A. Những câu hỏi literature trên được nêu chính xác để kiểm sau barrier, không mở rộng ngầm universe nguồn.

## 7. Kiểm tra hoàn tất và bàn giao

- Hai ứng viên đều có RQ, rationale, closest work, giới hạn literature, Task-B support, experimental unit, input, graph role, output, GT, baseline/evaluation families, H0/H1, falsification, confounders/leakage, feasibility, dataset risk, FlashTicket relevance, exclusions và lý do có thể không đáng làm.
- Phân biệt root-service ranking với detection/affected-node/operation/path evaluation; edge giữ nghĩa trace-derived relationship.
- Không dùng năm service labels làm candidate universe; không lấy coverage toàn case làm coverage prefix; không coi hàng triệu span là cỡ mẫu độc lập.
- B §12 được ưu tiên trước báo cáo lịch sử, kể cả ngoại lệ known-window inject_time và sửa nghĩa log–metric bin join.
- Không chọn winner; không tự phê duyệt RQ; không gộp với reviewer khác; không bắt đầu Task D.
- Thay đổi duy nhất của reviewer: file `task-c/phase-1-independent-candidates/reviewer-a.md` trong workspace nghiên cứu đã được người dùng chỉ định. Task A/B, manifests, telemetry và application được giữ nguyên.
- Tư liệu phù hợp cho báo cáo chính thức sau này: luận cứ tách detection/RCA/causality; giới hạn giá trị nhãn injected root; thiết kế đối chứng và diễn giải kết quả âm. Không được viết hypotheses thành kết quả thực nghiệm.

**END OF INDEPENDENT REVIEW C-A — INDEPENDENT SUBMISSION COMPLETE.**
