# Task C — Reviewer C-E: khả thi hệ thống và kỹ thuật

- Ngày: 2026-09-20. Trạng thái: `DRAFT`; ý định: `EXECUTE`; loại: `FORMATION`.
- Đây là tập ứng viên độc lập để phản biện, không phải shortlist đã duyệt. Hai hướng có trạng thái `CANDIDATE`; không có hướng thắng.
- Đã đọc yêu cầu Task C, evidence ledger, Task A (toàn văn), Task B §12 CLOSED, báo cáo G về tái lập, hiến pháp/skill/references, quy trình chủ, DT18 và roles. Các reviewer A–F/H/I/J/resource của Task B được tiếp nhận qua ledger và phần hòa giải CLOSED; không tuyên bố cá nhân C-E đã đọc toàn văn tất cả các báo cáo đó. Main đã thực hiện ingestion toàn pack.
- Không đọc ứng viên C-A/C-B/C-C/C-D/C-F, hội thoại cũ, E1 hoặc A10; không mở repository legacy; không tìm thêm literature, cài phần mềm, tải dữ liệu, viết detector hoặc chạy lại audit.
- Claim class: `VERIFIED — TASK A/B` và `PRIMARY-SOURCE FACT` tương ứng `FACT`; `TASK-C INFERENCE` tương ứng `CANDIDATE`; `OPEN` giữ nguyên. Các điều kiện thí nghiệm dưới đây đều là đề xuất, không là cấu hình đã chốt.

## 1. Bằng chứng dẫn đến việc hình thành hai câu hỏi

| Bằng chứng | Phân loại và nguồn | Hệ quả nghiên cứu, ghi riêng là suy luận |
|---|---|---|
| Đồ thị có thể thay đổi score theo ngữ cảnh hoặc chỉ xếp hạng sau detector; các tác vụ này khác nhau | VERIFIED — TASK A §B/D/F; ledger A-001/002 | TASK-C INFERENCE: cần xác định giá trị xuất hiện ở khâu nào, thay vì đánh giá một khối hộp đen |
| MicroRCA/MicroRank, CIRCA, Eadro và DéjàVu đã dùng quan hệ để xếp hạng hoặc điều kiện hóa bằng chứng; đã có ablation graph | VERIFIED — TASK A §C/L; A-005/006 | TASK-C INFERENCE: lặp lại “có graph tốt hơn không graph” không đủ luận văn; phải khảo sát một giới hạn vận hành hoặc giả thuyết phân biệt được |
| RE2-TT có 90 sự cố, 5 nhãn root × 6 loại lỗi × 3 lặp; cùng chế độ 720/721 timesteps | VERIFIED — TASK B §12.4; M-001 | TASK-C INFERENCE: có thể kiểm khả năng tổng quát qua kịch bản, nhưng không coi hàng triệu span là số mẫu độc lập |
| 67.345.051 span, 27 service literal, 161 cặp literal service-operation toàn subset; 20–27 ứng viên mỗi full case | VERIFIED — TASK B §12.6/9; M-003/005 | TASK-C INFERENCE: chi phí chính có thể nằm ở đọc/chuẩn hóa dữ liệu; kích thước graph service nhỏ không chứng minh toàn pipeline rẻ |
| Có GT service; không GT operation, vùng ảnh hưởng, đường lan truyền hoặc thời điểm triệu chứng độc lập | VERIFIED — TASK B §12.9/12/17; B-002/003 | TASK-C INFERENCE: câu hỏi chính nên chấm service ranking; không tự tạo bài toán causal path hoặc node anomaly F1 |
| Có 7 case parent resolution dưới 90%; graph chỉ là quan hệ parent-child quan sát được | VERIFIED — TASK B §12.6/7/11; M-004/006 | TASK-C INFERENCE: đây là biến kiểm độ nhạy, không tự động là đóng góp chính hay bằng chứng quan hệ nhân quả |
| Nhiều baseline cần loại input/label/graph khác nhau; MicroRank còn discrepancy paper/code | VERIFIED — TASK A §C/F/J; A-008/009 | TASK-C INFERENCE: tái lập công bằng là công việc thật; không hứa tái lập nguyên bản mọi baseline |
| Nhóm có bốn người, Minh phụ trách chính RCA và nhiều nền tảng chung; các thành viên khác có phạm vi ứng dụng | PRIMARY-SOURCE FACT — roles; P-002 | TASK-C INFERENCE: năng lực RCA gần với một chủ sở hữu chính có cộng tác tích hợp, không phải bốn nghiên cứu viên toàn thời gian |
| Công khai trước, áp dụng và đo FlashTicket sau; cơ chế nhận log, trace, metrics; hệ bán vé còn phải được đánh giá dưới tải/đồng thời | PRIMARY-SOURCE FACT — DT18-NV1/2/3; P-001 | TASK-C INFERENCE: chuyển giao phải giữ nguyên câu hỏi/đầu ra chấm được; không tiêu hết nguồn lực vào pipeline nghiên cứu làm chậm dữ liệu quan sát dùng được |

Không có hàng nào chứng minh novelty. Task A §L kết luận không có `STRONG CANDIDATE`. Hai hướng dưới đây sống ở mức câu hỏi thực nghiệm có đường kiểm định; tính đủ sâu cho luận văn còn phải qua literature positioning và phản biện chính thức.

## 2. CE-01 — Giá trị chẩn đoán của bằng chứng tích lũy theo thời gian

### Câu hỏi và động cơ

**Research Question — TASK-C INFERENCE:** Trong RCA được cấp một cửa sổ sự cố đã biết, khi chỉ cho phép dùng telemetry đã xuất hiện tới thời điểm trả lời, ngữ cảnh quan hệ dịch vụ có cải thiện đánh đổi giữa thời gian chờ bằng chứng, chi phí xử lý và độ đúng của xếp hạng service so với bằng chứng cục bộ và các họ RCA hiện có hay không?

Đây là câu hỏi về thời điểm một kết quả chẩn đoán trở nên hữu ích, không chỉ thời gian chạy của hàm ranker. Chờ thêm telemetry có thể đổi root rank; một ranker chạy nhanh sau khi nhận toàn bộ ca lỗi vẫn có thể cần chờ lâu mới trả lời. Đóng góp có thể là kết quả thực nghiệm kiểm soát được về vùng lợi ích/thất bại của graph dưới ràng buộc bằng chứng khả dụng. **OPEN:** chưa có bằng chứng rằng kết quả này mới so với toàn literature; không gọi tối ưu triển khai hoặc vẽ đường runtime là đóng góp tự thân.

### Prior work và khoảng chưa xác lập

- **VERIFIED — TASK A §C.2/3/4/6:** MicroRank thu thêm trace sau trigger; BARO tách detection/runtime ranking; CIRCA cần reference và test interval; MicroRCA nhắm response-time fault. Các bài có cửa sổ/chi phí nhưng những số đó thuộc setup riêng.
- **Closest work:** MicroRank/MicroRCA cho evidence-to-rank theo graph; BARO cho phân biệt độ trễ detector và ranker; CIRCA cho cửa sổ contextual ranking; TORAI cho known-window multi-source RCA.
- **TASK-C INFERENCE:** pack A chưa xác lập một so sánh chung về thời gian quan sát cộng thời gian xử lý, cùng prefix telemetry/candidate universe/supervision, trên các fault khác nhau. “Pack chưa xác lập” không có nghĩa “chưa ai làm”. Đối chiếu hẹp ở bước positioning nếu sự khác biệt này quyết định khả năng giữ hướng.

### Hợp đồng thí nghiệm

| Trường | Thiết kế ứng viên và giới hạn |
|---|---|
| Đơn vị chính | Một incident run; các lần trả lời ở nhiều thời điểm của cùng run là repeated measures, không phải samples độc lập |
| Dataset/subset | RE2-TT revision trong B §12.2. Cả 90 case về nguyên tắc; pilot giới hạn theo kế hoạch độc lập kết quả và phải giữ fault/root/repeat coverage. Audit toàn trace không đồng nghĩa đã có corpus cục bộ để chạy |
| Inputs | Metric series, durations/service/time từ traces, các parent relation đã resolve và còn khả dụng tại cutoff; logs là thêm có kiểm soát sau khi đáp ứng join/schema/availability. Không cần event-level log–trace join |
| Graph role | Ngữ cảnh cho bằng chứng hoặc ranker; graph tại thời điểm t chỉ dùng dữ liệu khả dụng tới t hoặc nguồn lịch sử training hợp lệ. Không dùng union 27 node/55 cạnh toàn test để cho biết tương lai |
| Output | Danh sách service theo từng thời điểm trả lời, cùng observed-candidate coverage, thời gian chờ telemetry, thời gian xử lý, peak memory và chi phí preprocessing |
| GT | `root_cause_service` chấm thứ hạng; `inject_time` chỉ định ranh giới bên ngoài cho known-window RCA. Không biến thành input phát hiện bất thường |
| Định lượng được | MRR/Hit@k theo thời điểm trả lời; chất lượng theo tổng độ trễ và theo chi phí; độ ổn định thứ hạng mô tả riêng; không xem ổn định là đúng |
| Không định lượng được | Thời điểm nguyên nhân bắt đầu biểu hiện thật, độ chính xác operation, causality/path, node anomaly F1, false alarm vận hành dài ngày |
| Candidate universe | Từ telemetry hợp lệ tại cutoff, chung giữa comparators. Full-case coverage 90/90 không đảm bảo prefix coverage. Root chưa hiện được tính như miss và báo riêng coverage; không đưa root vào nhờ nhãn |
| Baselines | Local statistical deviation/ranking; trace-graph ranking; contextual graph scoring; một họ multi-source known-window nếu inputs đủ. BARO ranking component khi cấp cùng boundary phải ghi rõ là adaptation; end-to-end BARO chỉ được đặt ở bảng riêng với detector thật |
| So sánh công bằng | Cùng prefix, quá khứ, candidate policy, budget chỉnh tham số và label budget. Tách cold preprocessing, warm reuse và amortized compute; không so cached đề xuất với cold baseline |
| H0 | Sau khi kiểm soát lượng bằng chứng, cutoff, candidate coverage và chi phí, ngữ cảnh quan hệ không đem lại cải thiện ranking thực dụng ở độ trễ bằng nhau hoặc giảm độ trễ để đạt chất lượng tương đương |
| H1 | Có miền ngân sách/thời gian đăng ký trước, lặp lại được trên các kịch bản held-out, nơi graph đem lại ranking tốt hơn ở chi phí/độ trễ tương đương hoặc cùng chất lượng sớm hơn; phải nêu rõ miền thất bại |
| Falsification | H1 không được hỗ trợ nếu lợi ích biến mất khi tính thời gian chờ/parse/join, khi universe/cutoff đồng nhất, chỉ có ở một target đã thấy, hoặc uncertainty không phân biệt khỏi mức hiệu quả thực dụng được chốt trước. Không “chọn lại” miền thời gian sau khi nhìn test |
| Ablation | Giữ local evidence không đổi khi bỏ/thay graph; giữ graph và cutoff khi thêm nguồn; tách độ trễ thu thập với xử lý; tách candidate coverage khỏi ranking trên candidates quan sát được. Các ablation phụ không tạo thêm RQ chính |

### Validity, leakage và khả thi

**TASK-C INFERENCE — confounders:** fault mạnh có thể dễ thấy sớm; ít traffic làm prefix ít service; thời điểm phát span/ingestion có thể khác `startTime`; toàn case chứa trace kéo dài qua cutoff. Task D phải quy định khi nào span được coi là khả dụng, không dùng duration kết thúc trong tương lai để giả vờ chạy online. Nếu release không có ingestion time, phép replay chỉ là event-time evaluation với giả định công khai, không phải đo production ingestion latency.

**Leakage:** không dùng path/case ID/fault/root text, normal/fault counts, tổng số dòng/full-case end làm features; normalization/parser/graph học chỉ từ training hoặc lịch sử hợp lệ; không lọc case bằng kết quả. Prefix của cùng case không được rơi vào train và test. Repeats cùng root×fault cần grouping và phân tích độ nhạy vì chưa biết độc lập đến đâu. Cấm chỉnh thời điểm trả lời để khớp vị trí tiêm lỗi cố định rồi gọi detector.

**Construct validity:** GT chỉ cho service bị gắn nhãn root; rank sớm không chứng minh root mechanism. Chất lượng-thời gian phải báo theo incident, không theo span. **Internal validity:** shared preprocessing, CPU/memory budget và cached artifacts phải được mô tả; so sánh paired ở case/scenario. **External validity:** RE2-TT là fault injections có lịch cố định, không chứng minh tải sản xuất, lỗi logic im lặng hay nhiều root; FlashTicket chỉ bổ sung bằng chứng trong hệ đã triển khai.

**Khối lượng triển khai dự kiến — TASK-C INFERENCE:** trung bình đến cao. Dùng lại schema/manifest/policy từ Task B; thêm pipeline replay prefix và đo từng tầng; không tái dựng topology, không xây streaming platform chỉ để có benchmark. Khó nhất là tránh nhìn trước và đo chi phí thống nhất, không phải graph service có vài chục node. Có thể triển khai theo case và cache feature với key chứa revision/cutoff/split; chưa kết luận thời gian/RAM thực tế khi chưa chạy Task E. GPU không là tiền đề của câu hỏi; baseline gần nhất nếu yêu cầu GPU vẫn phải được tính chi phí và khả năng tái lập, không loại chỉ vì bất tiện.

**Dataset risk:** trung bình–cao: trace prefix coverage chưa được Task B chứng minh; logs toàn 89 case chưa được xác minh schema; dữ liệu thời gian đến thực tế không có trong pack. Không chạy audit mới ở Task C. Nếu event-time limitation làm mất ý nghĩa triển khai, thu hẹp thành offline evidence-horizon study và đánh giá lại tính đáng luận văn; không đổi tên thành real-time.

**Chuyển FlashTicket:** áp dụng cùng rank output và quy tắc chỉ dùng quá khứ; đo thêm overhead trong điều kiện tải hiện hành sau luồng chính/observability. Đo giao dịch hệ thống theo DT18-NV1 là trách nhiệm riêng, không lấy RCA runtime thay throughput/consistency. LLM nhận ranking kèm cutoff và bằng chứng để diễn giải; không chọn thời điểm đúng bằng root label.

**Ngoài phạm vi:** phát minh detector end-to-end, repair trace, GT operation, autoscaling, tự sửa hệ thống, thay đổi service/Saga, benchmark mọi framework, lời hứa hard real-time. Missing trace chỉ là phân tầng robustness; operation chỉ là nguồn feature nội bộ nếu cần, không mở thêm target.

**Vì sao có thể không đủ luận văn:** nếu kết quả chỉ là “chờ lâu có thêm dữ liệu” hoặc “parse nhanh hơn”, không có giả thuyết phân biệt, điều kiện thất bại và đối chứng sát thì đây là engineering benchmark hẹp. Nếu lựa chọn này được giữ, Task D phải định nghĩa hiệu ứng thực dụng, estimand/uncertainty, lịch cutoff chưa khóa số, policy spans/candidates và baseline reproductions. Bỏ hướng nếu không tạo được so sánh causal-in-time công bằng hoặc closest work đã trả lời đúng cùng câu hỏi.

## 3. CE-02 — Ngữ cảnh quan hệ có giúp xếp nguyên nhân thay vì triệu chứng mạnh nhất?

### Câu hỏi và động cơ

**Research Question — TASK-C INFERENCE:** Trong known-window service RCA, với cùng telemetry, candidate universe và ngân sách nhãn, việc xét bất thường trong ngữ cảnh quan hệ dịch vụ có giúp ưu tiên service root được gán nhãn hơn xếp hạng độ lệch cục bộ hoặc dùng graph chỉ sau khi chấm độ lệch, khi chuyển sang các kịch bản lỗi chưa dùng để hiệu chỉnh hay không?

Đây là nghiên cứu khả năng tổng quát của vị trí graph trong chuỗi suy luận. “Nguyên nhân thay vì triệu chứng” ở đây chỉ được vận hành hóa bằng **root service rank**; không có nhãn affected-node để chứng minh node nào là triệu chứng lan truyền. Không dùng từ “tách được causal root” nếu chỉ có bảng MRR.

### Prior work và cơ sở dữ liệu

- **VERIFIED — TASK A §C.2/3/6/7/9, §D/L:** local-score rồi graph ranking đã có; contextual anomaly và graph aggregation cũng đã có; Eadro/DéjàVu có ablations. CIRCA là prior gần cho conditional scoring và thừa nhận missing parents/common causes. MicroRCA/MicroRank là gần cho graph ở giai đoạn sau. BARO là đối chứng local; Eadro là closest supervised joint approach nếu so sánh cùng label budget.
- **TASK-C INFERENCE:** câu hỏi chỉ còn đáng xem xét nếu isolating graph stage + held-out scenario phân biệt được lợi ích contextual evidence khỏi local severity và service memorization. Task A chưa xác lập novelty của tổ hợp protocol này. Không gọi một phép ablation mới là thuật toán mới.
- **VERIFIED — TASK B §12.4/7/9/12:** 90 case, root labels và observed relations cho phép chấm service rank; operation/resource/path GT không tồn tại. Sáu fault families tạo cơ sở thử held-out fault scenarios; chỉ ba repeats mỗi cặp làm uncertainty lớn.

### Hợp đồng thí nghiệm

| Trường | Thiết kế ứng viên và giới hạn |
|---|---|
| Đơn vị chính | Incident run; chênh lệch rank giữa comparators trên cùng run; phân tích theo root×fault và repeats |
| Dataset/subset | RE2-TT cùng revision; không nhập số service từ Eadro/TORAI collection khác. 90 full cases có target trong 20–27 literal trace services |
| Inputs | Metric series, observed trace latency/count/evidence, graph resolved parent relation. Logs service-time là phần bổ sung nếu cùng availability policy cho cả nhánh; tên service cần cho identity nhưng không dùng prior chỉ năm target |
| Vai trò graph | Biến ngữ cảnh đổi score trước ranker, so với cùng local score + graph ở ranker và đối chứng local; không chốt cơ chế tính hoặc thuật toán cụ thể |
| Output và GT | Ranked root-service list; GT service evaluation-only. Score node nội bộ không phải nhãn anomaly node |
| H0 | Sau khi giữ cố định evidence, labels và universe, contextual graph không cải thiện root-service ranking có ý nghĩa thực dụng trên scenario held-out so với local-score và graph-only-at-ranking |
| H1 | Contextual graph cải thiện ranking trên held-out scenarios mà không chỉ nhớ service/fault đã thấy, và mức cải thiện còn tồn tại trong các kiểm tra cấu trúc đối chứng và ngân sách tương đương |
| Bác bỏ/không hỗ trợ | Lợi ích mất khi label budget/input đồng nhất; lợi ích tương đương graph ngẫu nhiên hoặc topology-only prior; chỉ thắng trên recurring faults đã thấy; kết quả không vượt practical-effect criterion/uncertainty được khóa trước. Không xem p-value không có ý nghĩa là chứng minh hai phương pháp bằng nhau |
| Baseline families | Local statistical; local plus trace-graph ranking; graph-conditioned contextual; supervised multimodal/graph nếu đủ budget labels và có bảng riêng. Không ép CIRCA nguyên bản chạy khi thiếu required structural metric mapping rồi gọi thất bại của paper |
| Độ đo | MRR/Hit@k theo incident; effect paired và uncertainty theo nhóm; báo theo fault/root; runtime/peak memory bổ trợ. Single-root NDCG nếu báo phải ghi gain, cutoff, công thức và sự dư thừa thông tin; không node F1 |
| Ablation quyết định | Giữ local inputs, candidate policy, scorer family/budget để so graph stage; đối chứng graph-free và cấu trúc bị phá có kiểm soát chỉ là negative control, không tuyên bố learned graph correctness; loại service-identity shortcuts; tách thêm modality khỏi thêm graph |
| Missing trace | Giữ các case thấp coverage, báo tương tác exploratory với parent resolution; không sửa cạnh, không coi low/high groups là một can thiệp ngẫu nhiên |
| Operation | Chỉ feature/aggregation nội bộ nếu cần và nếu không tạo lợi thế input riêng; không đánh giá operation accuracy |
| LLM | Diễn giải thứ hạng/bằng chứng sau kết quả, phải nói rõ unsupported cause hypotheses; không tham gia tạo GT hay chấm rank |

### Validity, leakage và khả thi

**Confounders — TASK-C INFERENCE:** high-degree service dễ đứng cao; workload chung tạo correlated deviations; low-parent coverage có thể đi cùng một root/fault; root mạnh local dễ che mọi giá trị graph; normalization với ít normal history có thể quyết định toàn kết quả. Đồ thị trace không có causal sufficiency. Nếu ghép observed relations thành parent context, kết quả chỉ là predictive/contextual utility.

**Leakage:** split theo case/scenario, không rải windows cùng incident; hold-out fault/root là các phép thử khác nhau, không gộp thành “unseen incidents” mơ hồ. Nếu leave-root-out, mọi label-dependent tuning phải loại root đó, nhưng candidate universe vẫn gồm mọi service quan sát được. Không dùng GT để mapping/repair graph. Parser/statistics/feature selection phải fit trong training. Cấm feature case index, đường dẫn hoặc token root text. Nếu graph từ trước incident chưa có một service, phải báo coverage và miss; không cấp union test topology.

**Construct validity:** root ranking là task thật; “giảm nhầm triệu chứng” chỉ là cách giải thích hiệu ứng, chưa đo affected labels. **Internal validity:** mô hình contextual nhiều capacity hơn có thể thắng vì capacity, cần comparator tương xứng; không so model supervised với unsupervised rồi gán mọi lợi ích cho graph. **External validity:** chỉ năm targets, sáu resource/network fault classes; không chứng minh multi-root/logic faults hoặc causal discovery. Held-out fault cùng một workload không là cross-system transfer.

**Khối lượng triển khai — TASK-C INFERENCE:** trung bình–cao, cao nhất ở fairness và debugging để cùng feature thực sự đi qua các nhánh. Dùng lại Task B identities/joins/manifest; sửa adapters đầu vào cho baseline cần thiết, ghi rõ adaptation; thêm khả năng kiểm feature/graph provenance cho từng rank. Không cần nhiều tầng operation/resource hoặc mô hình lớn chỉ để làm luận văn trông khó. Nếu closest baseline cần structural metric mapping không có, phải ghi unsupported exact reproduction và dùng comparator hợp lệ; không tạo architecture facts để lấp.

**Compute:** service graph nhỏ; metric dimensionality/feature training/baseline dependency có thể lớn. Không suy diễn wall-clock từ paper. Cần tính cả repeated grouped evaluation, ablations và tuning budget; chưa xác định CPU/GPU/RAM/chạy bao lâu ở Task C. Số graph nhỏ không loại rủi ro overfit trên 90 case.

**Dataset risk:** trung bình đối với service ranking; cao nếu hứa chứng minh lan truyền/causality hoặc anomaly detector thật. **Research risk:** cao về novelty, trung bình–cao về sample diversity. Ưu tiên tính khoa học không đồng nghĩa bắt buộc thêm GNN/causal graph/resource layers.

**Chuyển FlashTicket:** đóng góp có ý nghĩa nếu cùng nguyên lý giữ hiệu lực khi tải và tên dịch vụ thay đổi, với target injection được ghi độc lập. FlashTicket cần high-quality observation theo nhiệm vụ hiện hành; không cố tình làm trace hỏng để phù hợp câu hỏi. Có thể kiểm các tình huống root ranking dưới tải trong luồng đã phê duyệt; không thêm dịch vụ/nghiệp vụ để tạo khó. Kiến trúc và vị trí triển khai qua cổng hệ thống, không được C-E quyết.

**Ngoài phạm vi:** causal-path recovery, topology repair, operation/root-resource localization, fault classifier, LLM làm RCA, toàn bộ các baseline Task A, thiết kế service/Saga/schema mới. Graph trực tiếp đổi score không đủ để gọi là incident detector đã được đánh giá: detector P/R/F1 vẫn là bài đo riêng với giới hạn injection-regime labels.

**Vì sao có thể không đủ luận văn:** prior CIRCA/Eadro/DéjàVu đã phủ phần lớn câu chuyện; nếu chỉ đổi một công thức và thử lại RE2-TT thì contribution nhỏ. Phải tìm ra và giải thích được điều kiện tổng quát/thất bại, có kiểm soát capacity/input/label/graph stage và xác nhận chuyển FlashTicket. Task D cần khóa grouping, comparators hợp lệ, graph availability, effect criterion, capacity budgets và nhãn dùng ở từng nhánh; không khóa ở đây. Bỏ hướng nếu không chứng minh được câu hỏi vượt ablation thông thường hoặc không có đối chứng sát có thể tái lập hợp lệ.

## 4. Các hướng đã cân nhắc nhưng không đưa thành ứng viên chính

| Hướng | Điểm dừng | Lý do và bằng chứng | Tương lai |
|---|---|---|---|
| Dựng resource/queue/DB graph để tìm shared cause | Sàng lọc dữ liệu | B §12.8/17 không hỗ trợ identity/edges/GT; thêm mapping bằng suy đoán vi phạm evidence | Chỉ xem lại khi có nguồn riêng và gate phù hợp, không buộc FlashTicket sinh dữ liệu ngoài RQ |
| Operation localization chính | Sàng lọc target | B §12.7/9: literal representation có, operation GT không; LLM không thay GT | Có thể là qualitative evidence hoặc future controlled validation, không định lượng RE2-TT |
| Tự sửa incomplete traces/topology | Sàng lọc phạm vi | A §H/L: prior mạnh, uncertainty cao; B không có topology hoàn chỉnh/GT missingness; user không yêu cầu | Sensitivity giữ lại, primary repair chưa có căn cứ ưu thế |
| Hệ thống liên hợp detector + ranker + explanation + action mới | Sàng lọc khả thi | Tách tác vụ theo A §B/J; 90 injection cases không cấp đủ GT để chấm mọi tầng; nhân sự theo roles có owner RCA chính | Xây integration tối thiểu phục vụ một câu hỏi, không biến toàn pipeline thành một contribution |
| Chỉ thêm ba modality hoặc một mô hình sâu | Sàng lọc khoa học | A §C/G/L: Eadro/TORAI/ARMOR đã có; engineering cost không là novelty | Modality/model là lựa chọn phương pháp ở Task D, không RQ |

## 5. Kiểm khả thi trước khi tổng hợp, không xếp hạng

| Trục | CE-01 | CE-02 |
|---|---|---|
| Nội dung khoa học cần bảo vệ | Bằng chứng khả dụng và tổng độ trễ ảnh hưởng lợi ích graph thế nào | Lợi ích graph ở score hay ở ranking có tổng quát qua scenario không |
| Ground truth | Service rank đủ; arrival/onset độc lập thiếu | Service rank đủ; symptom/causality labels thiếu |
| Rủi ro chính | Trượt thành profiling tối ưu kỹ thuật hoặc giả online | Trượt thành ablation đã có hoặc so capacity/supervision không công bằng |
| Triển khai | Prefix/replay và đo tầng, tránh nhìn trước | Shared evidence + context/rank controls, tránh shortcuts |
| Compute | Đọc dữ liệu và repeated prefix evaluation có thể chi phối | Tuning/grouped ablation và model capacity có thể chi phối |
| Baseline reproducibility | OPEN ở môi trường/hardware; phân biệt waiting và processing | OPEN ở exact graph/input mapping và label budget |
| FlashTicket | Độ trễ trả ranking và overhead hữu ích vận hành | Tính bền vững thứ hạng khi tải/kịch bản khác hữu ích vận hành |
| Alignment | Graph reasoning trực tiếp; detection là phần riêng chưa được chứng minh | Graph-conditioned score; incident detection vẫn cần evaluation riêng |
| Quyết định | CANDIDATE, cần red team | CANDIDATE, cần red team |

Không suy “hai hướng sống độc lập” thành “nên làm cả hai”. Một luận văn với một RQ chính có thể dùng một vài phép đo của hướng kia làm kiểm tra phụ; việc hợp nhất chỉ sau khi tất cả reviewer nộp độc lập và không được âm thầm mở phạm vi.

## 6. Handoff và tự kiểm

- Chỉ tạo file reviewer-e.md này. Không thay A/B, raw, manifests, application, infrastructure, B16 hoặc decision-register; không nâng trạng thái quyết định.
- Assumptions: kinh phí/hardware/thời gian RCA chưa biết; baseline chưa chạy; log schema ngoài samples chưa được chứng minh. Các đánh giá complexity là TASK-C INFERENCE, không dự toán đã đo.
- Task A/B không mâu thuẫn material cần dừng: G lịch sử ghi raw manifest chưa có; CLOSED §12.2 và ledger đã thay thế giới hạn lịch sử đó. Không khôi phục blanket inject-time ban hoặc blanket time-only log–metric join cũ.
- Không numerical operation accuracy; không root→anomaly-node substitution; không năm-label Top-5; không gọi observed relations là CALLS/causal edges; không dùng full-subset statistics làm graph test được phép nhìn trước.
- Nội dung cho báo cáo chính thức sau này: problem definition, unit/GT/metrics, thời điểm bằng chứng khả dụng, chính sách split/leakage, baseline adaptations, hiệu ứng âm và limits; chưa đưa candidate thành method đã chọn.
- Kết quả phản biện này còn phải qua barrier tất cả reviewer, positioning và red team của main; không chọn winner, algorithm, threshold, exact windows hoặc môi trường cài đặt.

**KẾT THÚC REVIEWER C-E — ĐÃ NỘP TẬP ỨNG VIÊN ĐỘC LẬP.**
