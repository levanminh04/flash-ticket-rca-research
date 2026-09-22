# Reviewer C-D — Thiết kế thực nghiệm và thống kê

- Ngày: 2026-09-20. Ý định: `EXECUTE`; loại tạo tác: `FORMATION`; trạng thái: `DRAFT`.
- Chỉ đề xuất `CANDIDATE` và giữ lựa chọn chưa đủ căn cứ ở `OPEN`. Không chọn hướng thắng, thuật toán, ngưỡng, kích thước cửa sổ hay kiến trúc.
- Phạm vi được giao: sinh câu hỏi độc lập, trước tổng hợp và phản biện chéo. Hai ứng viên dưới đây chưa phải shortlist được duyệt.
- Độc lập: không đọc báo cáo ứng viên C-A/C-B/C-C/C-E/C-F, đề xuất hội thoại cũ, E1/A10 hoặc danh sách trong resume; không tạo agent con. Sổ bằng chứng chung có diễn giải Task C, vì vậy đây là độc lập về sinh câu hỏi, không phải độc lập về nguồn dữ liệu hoặc hoàn toàn mù với cách diễn giải nguồn.

## 1. Nguồn và cách phân loại phát biểu

Đọc đặc tả Task C và toàn bộ evidence ledger trước khi xây dựng ứng viên. Đọc trực tiếp Task A §C.1–C.12, §J–N; Task B toàn bộ §12 để xác minh chi tiết liên quan. Các báo cáo kiểm toán độc lập và JSON được dẫn qua ledger/Task B CLOSED; reviewer này không nhận là đã tự đọc lại toàn bộ 11 báo cáo hoặc kiểm toán lại dữ liệu. Main agent chịu trách nhiệm hoàn thành Phase 0 và đối chiếu toàn bộ gói trước tổng hợp.

| Khóa | Nguồn gốc |
|---|---|
| S | `C:/Users/84583/.codex/attachments/22e07417-e07b-42f3-a60f-793c63c2aec7/Pasted text.txt`, nhất là §1, §5–12, §18–20, §27–28 |
| A | `D:/Project/flash-ticket-platform/docs/research-rca/task-a-ban-do-bang-chung-doc-lap.md` |
| B | `D:/Project/flash-ticket-rca-research/dataset-audit/TASK-B-RCAEval-audit.md`, §12 CLOSED; không dùng §§1–11 để lật kết luận đã hòa giải |
| L | `D:/Project/flash-ticket-rca-research/task-c/task-c-evidence-ledger.md` |
| DT18 | `D:/Project/flash-ticket-platform/docs/evidence/project-direction/2026-09-18-de-tai-va-nhiem-vu.md`, §2 / DT18-NV2–NV3 |
| Vai trò | `D:/Project/flash-ticket-platform/docs/project/roles.md` |

Đã đọc AGENTS.md, kỹ năng govern-capstone-work, reference project-authority-and-gates, quy trình làm việc, DT18 và phân công hiện hành. Không đọc repository cũ/B5.5. Nguồn quản trị chỉ giới hạn quyền và nhiệm vụ, không dùng để lấy phương án nghiên cứu có sẵn.

`VERIFIED — TASK A/B` là phân loại nguồn cho `FACT`; `TASK-C INFERENCE` và `REVIEWER INFERENCE` là lập luận `CANDIDATE`; `OPEN` giữ nguyên. Mọi mô tả thí nghiệm đề xuất bên dưới mặc định mang nhãn **TASK-C INFERENCE · CANDIDATE**, không phải kết quả đã đo. Không có ADDITIONAL TARGETED VERIFICATION: không cần mở rộng literature để tạo các ứng viên có điều kiện này; tính mới vẫn OPEN.

## 2. Điểm xuất phát có thể kiểm chứng

1. **VERIFIED — TASK B:** 90 ca RE2-TT, năm nhãn service gốc × sáu fault × ba lần lặp; injection nằm trong cửa sổ công bố. Root-service có nhãn nhưng operation, affected-node và propagation-path không có nhãn (B §12.4, §12.9). Không gọi ba lần lặp là ba môi trường độc lập.
2. **VERIFIED — TASK B:** có thể dựng quan hệ service từ parent-span cùng trace đã giải được. Tập ứng viên trace toàn ca có 20–27 service và chứa nhãn gốc ở 90/90 ca; điều đó không bảo đảm mọi prefix có cùng coverage (B §12.7, §12.9; L M-005).
3. **VERIFIED — TASK B:** graph-ablation và known-window RCA có đường đánh giá hợp lệ; end-to-end detection chỉ có nhãn chế độ injection, không có anomaly onset độc lập (B §12.10–12.12).
4. **VERIFIED — TASK A:** graph ablation đã có ở Eadro/DéjàVu; MicroRCA tách việc đánh giá localizer qua detector output dùng chung; các phương pháp dùng telemetry, nhãn, cửa sổ và đơn vị output khác nhau (A §C.2, C.3, C.6–C.9; J.2). Không lấy chênh lệch hai bảng paper làm hiệu ứng của graph.
5. **VERIFIED — TASK A:** không có khoảng trống nào ở §L được chứng minh là STRONG CANDIDATE. Hai câu hỏi dưới đây là đóng góp thực nghiệm tiềm năng, không phải phát minh phương pháp.
6. **PRIMARY-SOURCE FACT:** DT18 yêu cầu thực nghiệm dữ liệu công khai rồi áp dụng thử trên FlashTicket; cả log, trace, metrics cần ánh xạ lên graph. Thí nghiệm hẹp chỉ dùng một phần telemetry không tự hoàn tất nhiệm vụ đó. Nhóm bốn người nhưng Minh còn phụ trách nền tảng chung (DT18 §2; Vai trò).

## 3. CD-01 — Giá trị thông tin của quan hệ dịch vụ khi giữ bằng chứng cục bộ cố định

| Trường §12 | Nội dung |
|---|---|
| **CANDIDATE ID / tên làm việc** | **CD-01 — Giá trị thông tin riêng của quan hệ dịch vụ trong xếp hạng known-window RCA**. `CANDIDATE`. |
| **Research Question** | Trên RE2-TT, khi telemetry, bằng chứng bất thường cục bộ, thời hạn quan sát và tập service ứng viên giống nhau, dùng đúng quan hệ parent–child service quan sát được có cải thiện thứ hạng service gốc so với đối chứng không dùng quan hệ và đối chứng quan hệ bị phá cấu trúc có kiểm soát không? |
| **Vì sao có ý nghĩa khoa học** | Tách lợi ích của thông tin quan hệ khỏi lợi ích do thêm features, tăng năng lực mô hình, đổi detector hoặc thu hẹp candidate set. Đóng góp tiềm năng là xác định khi nào cấu trúc mang thông tin vượt điểm cục bộ và khi nào không; kết quả âm vẫn có giá trị trong phạm vi benchmark. Không gọi đây là kiểm chứng quan hệ nhân quả. |
| **Prior work gần nhất** | **VERIFIED — TASK A:** Eadro thay GAT bằng FC và bỏ từng modality; DéjàVu bỏ aggregation và xóa cạnh; MicroRCA cho localizer dùng detector output chung; CIRCA để parent set ảnh hưởng score (A §C.2, C.6, C.7, C.9). Đây là prior của cách đặt đối chứng, không phải danh sách thuật toán đã chọn. |
| **Điểm còn mở theo Task A** | **VERIFIED — TASK A:** A §L ghi controlled test giữ input/local score/candidate cố định và thay graph đúng/sai/không graph là NEEDS MORE EVIDENCE. **TASK-C INFERENCE:** câu hỏi hẹp còn đáng kiểm nhưng nguy cơ lặp lại ablation đã công bố cao; không có bằng chứng literature-wide rằng chưa ai làm. |
| **Bằng chứng Task B làm nó kiểm được** | **VERIFIED — TASK B:** B §12.7, §12.9, §12.12 cho graph quan sát, service GT và graph ablation; §12.11 buộc giữ các ca parent resolution thấp. L M-003–M-006 chỉ đặc tả full-subset audit, không cung cấp graph test hợp lệ lấy từ hợp tất cả ca. |
| **Đơn vị thực nghiệm chính** | Một fault-injection case; tất cả phiên bản đối chứng chạy trên cùng ca. Service×fault là tầng kịch bản, ba repeat nằm bên trong tầng. Span/window/seed không tăng số incident độc lập. |
| **Input telemetry** | Metrics theo service và trace thống kê cục bộ nếu schema/mapping hợp lệ; traces để dựng quan hệ. Tập features phải giống nhau giữa các nhánh. Logs chỉ thành một khối phân tích phụ khi quy tắc availability/join được đáp ứng; nếu thêm phải cấp cùng dữ liệu cho mọi nhánh. B §12.5/12.13 giới hạn join trace ở service+time. |
| **Vai trò graph** | Cung cấp context quan hệ cho xếp hạng service, với node là literal service và cạnh là trace-derived parent→child relation. Giữ bằng chứng cục bộ trước xử lý graph cố định để cô lập câu hỏi. Không tự gọi pipeline này là graph-based anomaly detector (A §D/J). |
| **Primary output** | Danh sách xếp hạng service, trạng thái không xuất được kết quả nếu có, coverage của candidate set. Bằng chứng cục bộ kèm theo có thể phục vụ giải thích sau này. |
| **Ground truth** | Root-cause service của mỗi ca; fault label chỉ dùng phân tầng đánh giá. Injection time chỉ cung cấp ranh giới known-incident ngoài mô hình (B §12.9–12.10). Không dùng nhãn để học điểm, dựng cạnh hoặc chọn service. |
| **Expected baseline family** | Đối chứng điểm bất thường cục bộ không dùng quan hệ; cùng bộ xếp hạng quan hệ nhưng cấu trúc bị hoán đổi có kiểm soát; thêm họ RCA thống kê có điều kiện known-window khi có implementation/input tương thích. Baseline literature và ablation trong cùng phương pháp có vai trò khác nhau. Supervised model cần nhãn ngoài phạm vi này, không được cấp thêm nhãn rồi gọi là cùng điều kiện. |
| **Evaluation family** | MRR/Hit@k theo ca và chênh lệch ghép cặp; báo phân phối rank, coverage, failure count và chi phí. Mỗi nhánh có cùng candidate universe tại thời điểm chấm. NDCG một nhãn chỉ phản ánh vị trí, không severity. Không tính node F1. Metric/cutoff chính cuối cùng ở Task D. |
| **Null hypothesis H0** | Quan hệ service quan sát được không tạo cải thiện kỳ vọng về chất lượng xếp hạng vượt đối chứng cục bộ và các cấu trúc đối chứng trên phân bố ca đánh giá đã khai báo. |
| **Alternative hypothesis H1** | Quan hệ quan sát được tạo cải thiện vượt cả hai đối chứng, có độ lớn thực dụng được định nghĩa trước và không chỉ do một tầng kịch bản hoặc coverage. Chỉ kết luận cho phạm vi telemetry, fault và hệ được thử. |
| **Falsification condition** | Lợi thế biến mất khi giữ input/universe/calibration budget như nhau; cấu trúc bị phá cho kết quả tương đương hoặc tốt hơn; hoặc khoảng bất định loại trừ mức lợi ích có ý nghĩa được chốt trước. Nếu khoảng quá rộng thì kết luận chưa đủ bằng chứng, không nhận H0 là đã được chứng minh. |
| **Main confounders** | Graph density/degrees, số service, lưu lượng, số features mỗi service, cường độ fault không được quan sát độc lập, baseline history, parent resolution, năng lực/tuning khác nhau. Chênh lệch rank theo resolution là liên hệ mô tả, không hiệu ứng nhân quả của thiếu trace. |
| **Main leakage risks** | Hợp graph toàn bộ 90 ca; dùng tương lai của test window; root/path/fault tokens; chọn năm injected labels; chọn graph perturbation/ablation có kết quả thuận lợi sau nhìn test; fit scaler/parser với test. Giữ nhãn trong evaluator, graph/normalizer chỉ nhận phần telemetry được phép. |
| **Expected implementation complexity** | Trung bình: cùng pipeline evidence và evaluator, thêm adapter đối chứng graph. Chi phí lớn có thể nằm ở đọc và tổng hợp trace, không ở số node. Audit đã quét 67 triệu span nhưng không lưu toàn bộ corpus (B §12.2/12.6); compute/RAM/runtime thực tế OPEN, chưa đo. |
| **Expected dataset risk** | Vừa–cao: chỉ một hệ, năm target labels, graph quan sát không đầy đủ; metric/log schema toàn quần thể chưa được audit như trace. Nếu candidate hiện ra chỉ sau thời hạn, phải tính coverage failure và giữ ca. Dataset thứ hai chưa bắt buộc để phát biểu hẹp RE2-TT, nhưng cần dữ liệu khác trước tuyên bố tổng quát. |
| **FlashTicket transfer relevance** | Áp cùng phép đối chứng lên graph và incident có kiểm soát của FlashTicket để kiểm tra thông tin quan hệ còn có ích hay không. Không giả định kết quả RE2-TT chuyển nguyên vẹn; không thay số service/kiến trúc để làm đẹp thí nghiệm. |
| **OUT OF SCOPE** | Tái dựng trace/topology; causal discovery/path validation; resource/operation RCA; tối ưu detector; gắn nhãn bằng LLM; chọn thuật toán hoặc final method ở Phase 1. |
| **Vì sao có thể không đủ tầm luận văn** | Nếu chỉ chạy lại một ablation graph/no-graph, không cô lập được nguồn hiệu ứng hoặc chỉ cho một chênh lệch nhỏ trên một benchmark, đóng góp quá mỏng. Cần đối chứng cấu trúc hợp lý, phân tích điều kiện thất bại và xác nhận FlashTicket để hỗ trợ lập luận thực nghiệm; ngay cả vậy tính mới vẫn OPEN. |

### Hợp đồng thực nghiệm và phản bác CD-01

**TASK-C INFERENCE · CANDIDATE:** đối chứng “graph sai” phải bảo toàn các thuộc tính nhiễu quan trọng theo câu hỏi cụ thể, giữ nguyên node/features, không biến test thành lỗi phần mềm hoặc so sánh khác số parameters. Các giả định của phép hoán đổi phải được công khai; hoán đổi graph là ablation thông tin, không phải thử nghiệm can thiệp lên hệ thật. Không lựa cấu trúc đối chứng dựa trên vị trí nhãn gốc.

**TASK-C INFERENCE · CANDIDATE:** so sánh ghép cặp theo case, trình bày hiệu ứng từng service×fault và độ bất định có xét repeat trong tầng. Có 30 tổ hợp theo metadata nhưng chưa chứng minh 30 cụm độc lập: công bố giả định về campaign/workload và phân tích nhạy cảm nếu provenance không xác định. Không lấy hàng triệu span làm mẫu thống kê và không lấy nhiều seed làm thêm incident. Chọn số đối chứng, metric chính, quy tắc multiplicity và phương pháp interval ở Task D trước chấm test.

**Phân vai bắt buộc:** trace missingness = SECONDARY ROBUSTNESS ANALYSIS, không là đóng góp chính; operation = NOT USED cho câu hỏi chính; LLM = downstream explanation từ ranked evidence, không học/sửa nhãn. Construct validity giới hạn ở tìm service injected; internal validity dựa vào pairing và giữ input; external validity giới hạn một deployment/fault suite. Hướng này tự nó chưa hoàn thành yêu cầu đánh giá detector trong nhiệm vụ tổng thể.

**Điều kiện bỏ hướng:** không tạo được comparator giữ input/universe như nhau; phải dùng nhãn hoặc topology ngoài release để graph hoạt động; bằng chứng literature sau kiểm hẹp cho thấy cùng câu hỏi đã được trả lời đầy đủ và phần thêm không đủ giá trị. Không cứu hướng bằng cách thêm GNN, nhiều modality hoặc service mới.

## 4. CD-02 — Chất lượng RCA theo ngân sách chờ bằng chứng sau cảnh báo

| Trường §12 | Nội dung |
|---|---|
| **CANDIDATE ID / tên làm việc** | **CD-02 — Đánh đổi giữa thời gian chờ bằng chứng và chất lượng xếp hạng service có dùng graph**. `CANDIDATE`. |
| **Research Question** | Với một ranh giới incident được cung cấp từ bên ngoài, một phương pháp RCA có dùng quan hệ service giữ được chất lượng xếp hạng như thế nào khi chỉ được đọc các prefix telemetry ngày càng dài sau ranh giới đó, và so với họ đối chứng trên cùng ngân sách quan sát/tính toán, lợi thế của nó xuất hiện sớm, muộn hay không xuất hiện? |
| **Vì sao có ý nghĩa khoa học** | Chất lượng trên cửa sổ đầy đủ có thể che việc một phương pháp phải chờ thêm dữ liệu. Biến nghiên cứu là ngân sách bằng chứng theo thời gian, không phải thay threshold để thắng metric. Đóng góp tiềm năng là đường đánh đổi chất lượng–độ trễ có giới hạn rõ, đủ để bác bỏ tuyên bố phương pháp hữu ích cho chẩn đoán sớm dù final rank tốt. |
| **Prior work gần nhất** | **VERIFIED — TASK A:** MicroRank thu thêm trace sau trigger; CIRCA có reference/delay/test window; BARO báo detector delay và ranker runtime riêng; MicroRCA đánh giá localizer trên detector output chung; DéjàVu dùng cửa sổ lịch sử (A §C.2–C.6, C.9). Các chi tiết chứng minh thời gian quan sát và thời gian chạy là khác nhau. Không chuyển số giây của paper thành budget dự án. |
| **Điểm còn mở theo Task A** | **VERIFIED — TASK A:** A §J.1–J.2 nói rank tốt không chứng minh detection/latency, protocol quyết định ý nghĩa metric. **TASK-C INFERENCE:** trong gói đã đọc chưa thấy một phép so sánh công bằng đầy đủ đường chất lượng–thời gian trên cùng release/candidates; đây là điểm chưa được pack giải đáp, không phải chứng minh khoảng trống của toàn literature. |
| **Bằng chứng Task B làm nó kiểm được** | **VERIFIED — TASK B:** B §12.4 cho published windows, §12.6 cho timestamps trace và §12.9 cho service GT; §12.10 cho dùng inject_time như ranh giới ngoài trong known-window RCA. B §12.9 chỉ chứng minh target coverage toàn ca; prefix coverage là kết quả phải đo sau, chưa thể khẳng định. |
| **Đơn vị thực nghiệm chính** | Một incident với một đường kết quả qua các cutoff. Các prefix của cùng incident là repeated measures lồng nhau, không phải thí nghiệm độc lập. Ba repeat giữ cùng tầng service×fault như CD-01. |
| **Input telemetry** | Cùng reference history được cho phép và telemetry chỉ tới cutoff hiện tại; trace để dựng graph quan sát, metrics/trace features có cùng ngân sách. Logs là bổ sung có availability rule, không bắt buộc cho đường thử chính. Không dùng full-case counts, thời điểm kết thúc hoặc graph toàn ca để tính kết quả prefix. |
| **Vai trò graph** | Context quan hệ cho RCA tại thời hạn hiện hành. Có thể kiểm tra riêng việc tích lũy evidence trên graph tham chiếu cố định với việc cập nhật graph từ telemetry đã tới; cách tách này là ablation dự kiến, chưa chọn final graph policy. Không gọi timestamp trace là timestamp ingest thực tế. |
| **Primary output** | Ranked service list theo cutoff, đường rank-quality theo thời gian quan sát, candidate coverage và chi phí xử lý. Có thể xuất “chưa đủ kết quả” khi input không đủ theo rule đã định trước; phải giữ lần thất bại đó trong báo cáo. |
| **Ground truth** | Service injected; published inject_time chỉ định mốc bắt đầu một kịch bản known-window. Không có nhãn độc lập về thời điểm operator nhận cảnh báo, onset triệu chứng hay thời điểm kết quả đã đủ an toàn để thao tác. |
| **Expected baseline family** | Họ thống kê known-window RCA không dùng quan hệ và họ graph RCA có dữ liệu/đơn vị output thích hợp. Mọi baseline nhận cùng prefix và reference, không cho một phương pháp full window. Adapter service-output phải được khai báo; kết quả adaptation không là exact reproduction. |
| **Evaluation family** | MRR/Hit@k theo cutoff, curve theo từng case/tầng, coverage, wall-clock preprocessing/inference và memory trên cùng máy sau này. Chỉ báo “thời gian tới rank đúng” như phân tích hồi cứu có censoring, không làm online stopping rule. Không dùng chỉ số ổn định rank làm xác suất đúng. Metric tóm tắt đường cong và miền tích phân còn OPEN để tránh chọn sau nhìn dữ liệu. |
| **Null hypothesis H0** | Trong miền ngân sách đã xác định trước, phương pháp graph không có lợi thế chất lượng xếp hạng so với đối chứng đồng ngân sách, hoặc lợi thế final-window chỉ xuất hiện khi thời gian chờ vượt mức hữu ích được xác định trước. |
| **Alternative hypothesis H1** | Trong miền ngân sách được người dùng/nghiên cứu chấp nhận trước thử nghiệm, phương pháp graph cải thiện chất lượng service rank ở cùng ngân sách, hoặc đạt mức chất lượng tương đương theo biên được chốt trước với ít thời gian chờ hơn. Hai cách kiểm là những nhánh giả thuyết cần chọn trước ở Task D, không thử cả rồi chọn nhánh thuận lợi. |
| **Falsification condition** | Đường chất lượng graph không hơn đối chứng trong miền budget đã chốt; lợi thế biến mất sau tính preprocessing/coverage; hoặc mọi lợi thế cần dữ liệu tương lai/full-case graph. Khoảng bất định rộng là inconclusive. Nếu muốn tuyên bố “tương đương nhưng nhanh hơn”, không-significant difference không đủ: phải có biên và phép kiểm tương đương phù hợp được định trước. |
| **Main confounders** | Prefix dài có nhiều event và nhiều service hơn; volume thay đổi theo fault; graph growth cùng feature stability; fixed injection schedule; caching/warmup/hardware; reference history; runtime khác do implementation. Đường rank tốt hơn theo thời gian không tự chứng minh graph đã tìm được propagation. |
| **Main leakage risks** | Fit features/graph/parser toàn ca rồi cắt prefix; cho span chưa hoàn tất đóng góp duration sớm; sửa candidate set bằng full-case target knowledge; cấp injection offset để tự nhận incident; chọn cutoff tốt nhất mỗi test case; dùng GT để quyết định dừng. Prefix availability phải có rule cho trường chỉ biết khi span kết thúc. |
| **Expected implementation complexity** | Trung bình–cao: replay theo cutoff, quản lý availability, tính lại/ghi nhận preprocessing, paired evaluator. Trace subset lớn nên nhiều cutoff không được nhân vô hạn việc đọc dữ liệu; tái sử dụng tính toán phải giữ semantics availability. Runtime và số cutoff chưa chốt, không hứa realtime. |
| **Expected dataset risk** | Cao hơn câu hỏi full-window: release không có ingest time nên replay chỉ có event-time assumption; prefix target coverage chưa xác minh; mọi ca có injection cố định và phần trước injection không thay tập healthy-only dài hạn. Dữ liệu hiện có hỗ trợ đường rank hồi cứu có điều kiện, không chứng minh giảm MTTR hay độ trễ production. |
| **FlashTicket transfer relevance** | Controlled validation sau này có thể ghi mốc fault, alert và telemetry arrival riêng để đánh giá độ trễ thật; đây là vai trò xác nhận khả năng áp dụng, chưa tạo yêu cầu triển khai mới. Public-only kết luận giữ ở event-time replay. |
| **OUT OF SCOPE** | Tự phát hiện incident; học chính sách dừng tối ưu; adaptive threshold; dự báo propagation; trace repair; online closed-loop remediation; chứng minh giảm MTTR/operator burden; LLM quyết định khi nào rank đúng. |
| **Vì sao có thể không đủ tầm luận văn** | Nếu chỉ quét nhiều window size rồi báo window tốt nhất, đây là tuning, không phải nghiên cứu. Nếu không tách được availability, coverage và compute, đường latency sai nghĩa. Nếu không có kết quả về điều kiện hữu ích/thất bại hoặc transfer validation, nên hạ thành experiment phụ của hướng khác. |

### Hợp đồng thực nghiệm và phản bác CD-02

**TASK-C INFERENCE · CANDIDATE:** mọi phương pháp dùng cùng candidate policy tại mỗi cutoff. Coverage thiếu phải báo và tính như thất bại trong chất lượng đầu-cuối của known-window ranking; không xóa ca hoặc chỉ chấm nhóm có nhãn hiện ra. Để tách tác động graph/evidence trưởng thành khỏi tác động candidate universe mở rộng, báo thêm phân tích trên universe tham chiếu dựng từ dữ liệu trước incident nếu khả thi, vẫn giữ coverage failure. Không dùng full-case union làm universe prefix. Cách chọn một policy chính thuộc Task D.

**TASK-C INFERENCE · CANDIDATE:** thời gian chờ dữ liệu và runtime phải tách, cộng lại chỉ theo mô hình thực thi đã công bố; không cộng bừa thời gian từ paper/hardware khác. Cutoff chỉ cho biết event-time evidence có thể có, chưa biết khi nào collector nhận. Span duration là thông tin biết khi span kết thúc; nếu dùng phải có quy tắc availability thích hợp. Ranh giới injection được cho trước là oracle có tuyên bố của bài toán known-window, tuyệt đối không gọi là end-to-end AD.

**TASK-C INFERENCE · CANDIDATE:** uncertainty theo toàn bộ đường kết quả của incident hoặc summary đã preregister, không coi mỗi cutoff là observation độc lập; giữ pairing và clustering kịch bản. Không chọn cutoff “đẹp” từ test. Phân tích nhiều cutoff phải có kiểm soát multiplicity hoặc simultaneous uncertainty thích hợp; exact protocol và biên thực dụng ở Task D. Chỉ ba repeat/kịch bản khiến kết luận subgroup dễ thiếu lực thống kê; không hứa power bằng số span.

**Phân vai bắt buộc:** trace missingness = KNOWN LIMITATION, có thể thêm SECONDARY ROBUSTNESS ANALYSIS; thiếu evidence do cutoff là biến thời gian quan sát, không tự đồng nghĩa trace hỏng. Operation = NOT USED cho nhiệm vụ chính; LLM = giải thích ranking đã xuất, không xác nhận độ tin cậy. Construct validity là ranking theo event-time budget; internal validity đòi cùng history/cutoff/universe; external validity còn thiếu ingest delays, operator alerts và hệ khác. Chưa chứng minh chất lượng detector.

**Điều kiện bỏ hướng:** không mô tả được availability của input mà không nhìn tương lai; chất lượng chỉ đo được sau full-case; hoặc phần thêm so literature chỉ là chọn window tốt. Khi đó có thể giữ đường rank–budget như đánh giá phụ, không buộc giữ CD-02 thành primary RQ.

## 5. Ràng buộc chung về công bằng và thống kê

Các mục sau là **TASK-C INFERENCE · CANDIDATE** cho Task D, chưa khóa protocol:

- Tách development/calibration khỏi final evaluation theo incident hoặc nhóm kịch bản; không rải các window cùng ca vào train/test. Baseline nào cần fault labels để fit không tương thích khóa Task B “evaluation only” trong phạm vi hiện tại; không âm thầm dùng nhãn để train. Nhãn cho phân tầng evaluator không được lộ sang pipeline.
- Công bố toàn bộ ca dự kiến, lỗi chạy, input thiếu, tie policy và cách chấm target ngoài candidate set. Chỉ báo conditional-on-coverage accuracy như metric phụ đi kèm coverage; không thay score trên toàn bộ ca.
- Công bố mean/median hoặc distribution per-case phù hợp, paired effect và độ bất định; phân tầng fault/service và sensitivity với graph coverage. Macro theo tầng làm lộ thất bại khó, không tạo độc lập thống kê mới. Với thiết kế cân bằng và không có missing case, macro các tầng bằng kích thước có thể trùng overall mean.
- Suy luận thống kê phải nêu estimand: hiệu ứng trên 90 ca hữu hạn có thể mô tả trực tiếp; interval nhằm suy rộng tới repeat/campaign chưa quan sát cần giả định sinh mẫu. Không để cluster bootstrap hay p-value che việc chỉ có một deployment và ít repeat.
- Ngưỡng hiệu ứng thực dụng, biên tương đương nếu dùng, cách tổng hợp nhiều metrics/cutoffs và số lần ngẫu nhiên phải định trước sau quyết định của Minh/Task D. Không invent numeric cutoff ở Phase 1.
- Hash input/revision, split manifest, mapping service, graph source/cutoff, cấu hình đối chứng, seed nếu có, hardware và bảng kết quả từng ca là dữ liệu tái lập cần lưu khi được phép chạy thí nghiệm. Audit JSON hiện tại không thay thế model-ready telemetry.
- Baseline paper có graph resources, operation GT hoặc topology ngoài release phải khai rõ phần không tái lập được; không cứu bằng đoán schema hoặc bỏ điều kiện để giữ tên baseline.

## 6. Những hướng không nâng thành ứng viên độc lập

| Hướng | Lý do và trạng thái |
|---|---|
| Phát hiện bất thường từng service với F1 | Không có affected/anomalous-service GT; root injected không thay nhãn node anomaly. `REJECT — NOT EVALUABLE` theo B §12.9/12.17; không cần thí nghiệm mới để biết giới hạn này. |
| Xếp hạng operation/propagation path | B §12.7/12.9 có representation nhưng thiếu target; không chấm quantitative accuracy và không nhờ LLM sinh nhãn. `REJECT — NOT EVALUABLE`. |
| Nghiên cứu thiếu trace là mặc định | A §C.8/C.9/C.12 có prior; B chỉ cho natural coverage, chưa cho missingness mechanism/complete topology. Giữ phụ hoặc limitation ở hai hướng, không sinh yêu cầu reconstruction. |
| Mô hình đa nguồn chỉ vì có ba modality | A §G/L đã có prior mạnh; B §12.5/12.13 chưa chứng minh event-level joins hay toàn-89 log-schema. Chỉ dùng modality như input/ablation được kiểm soát, không coi số nguồn là đóng góp. |
| Hiệu chuẩn xác suất nguyên nhân hoặc giảm thời gian xử lý của operator | Chưa có probability-calibration setup/operator outcome ground truth trong pack; có thể là nghiên cứu khác nhưng sẽ mở rộng scope/nhãn. `OPEN`, không thêm để đủ số ứng viên. |

## 7. Bàn giao và giới hạn

- Hai đề xuất CD-01/CD-02 đều `CANDIDATE`; không có quyết định nghiên cứu được nâng trạng thái. CD-01 kiểm giá trị thông tin của quan hệ tại ngân sách chung; CD-02 kiểm đường chất lượng theo ngân sách và availability. Chúng không tương đương về estimand, nhưng CD-02 có thể bị hạ thành phân tích phụ nếu literature/contribution gate không đủ mạnh. Không hợp nhất trước khi mọi reviewer nộp.
- `OPEN`: đóng góp thực nghiệm có đủ mức mong muốn của Minh/giảng viên; budget thực dụng; mức validation FlashTicket; implementation/runtime baseline. Không hỏi lại các sự thật dataset đã được B xác minh.
- Giả định: known-incident boundary là điều kiện bài toán được công khai; public dataset chỉ đại diện release được pin; các đối chứng sau này có thể thực hiện trên cùng input. Giả định chưa được thử không được viết thành kết quả.
- File duy nhất do reviewer này tạo/sửa: `D:/Project/flash-ticket-rca-research/task-c/phase-1-independent-candidates/reviewer-d.md`. Không đổi A/B, evidence, code, index hoặc decision register; không cài đặt, tải dataset, chạy baseline hay audit raw mới.
- Nội dung dành cho báo cáo chính thức sau khi có kết quả: đơn vị thực nghiệm; nguồn/giới hạn GT; cơ chế đối chứng; provenance; effect/uncertainty; ca thất bại; giới hạn event-time/known-window; giải thích vì sao không chấm node F1/operation accuracy. Chưa đưa kết luận ưu thế phương pháp vào báo cáo.
- Kiểm tra tự rà soát: cả hai hướng có đủ 24 trường §12; có H0/H1/falsification, chi phí, validity, leakage, trace/operation/LLM role; không chọn algorithm/threshold/winner; không dùng 27-node full-subset union như graph prefix; không suy CALLS/causal edges từ parent link; không coi graph ranking là detector.

**KẾT THÚC BÁO CÁO C-D — CHỜ HÀNG RÀO HOÀN THÀNH CÁC REVIEWER VÀ TỔNG HỢP PHASE 1.**
