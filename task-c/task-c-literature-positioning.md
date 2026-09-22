# Task C — Literature / contribution gate

- Ngày đánh giá: 2026-09-21. Trạng thái: `DRAFT`; loại tạo tác: `FORMATION`.
- Đây là phản biện độc lập ở Phase 4 của Task C Phase 1, sau khi năm câu hỏi C1–C5 đã được chuẩn hóa. Đây không phải một lượt sinh ứng viên mù mới, không phê duyệt RQ và không chọn thuật toán.
- Nguồn: Task A đầy đủ; `task-c-normalized-candidate-universe.md`; `task-c-evidence-ledger.md`; `task-c-targeted-verification.md` TV-01–TV-04; yêu cầu Task C §1, §16, §22, §27. Các giới hạn dữ liệu bên dưới lấy từ ledger và không thay thế hard feasibility gate.
- `PRIMARY-SOURCE FACT` chỉ nội dung bài gốc đã được Task A hoặc targeted verification ghi nhận; `VERIFIED — TASK A/B` chỉ phạm vi pack tương ứng. Mọi phán quyết contribution/gate ở đây là `TASK-C INFERENCE` / `CANDIDATE`; thiếu bằng chứng vẫn `OPEN`. Không có quyết định `DECIDED` hay `USER_CONFIRMED` về hướng nghiên cứu.
- Làm việc từ repository canonical; chỉ ghi supporting artifact ở thư mục `task-c/` do yêu cầu Task C §29 chỉ định. Không sửa Task A/B, ứng dụng, dữ liệu hoặc phân công.

## 1. Kết luận gate, theo thứ tự trung tính

| Hướng | Literature positioning | Khuyến nghị sau gate literature | Đóng góp tối đa hiện có thể nêu |
|---|---|---|---|
| C1 — Thông tin tăng thêm của quan hệ service | `DEFENSIBLE BUT INCREMENTAL` cho contrast hẹp; graph on/off đơn thuần là `LIKELY ALREADY COVERED` | Giữ có giới hạn để qua feasibility/red team. Không được biến một ablation cải thiện điểm thành toàn bộ luận cứ luận văn | `POTENTIAL CONTRIBUTION`: thực nghiệm tách thông tin quan hệ khỏi local evidence và nuisance về topology/capacity trong service ranking |
| C2 — Giá trị graph theo ngân sách event-time | `DEFENSIBLE BUT INCREMENTAL` cho tương tác graph × cutoff; volume/window sweep đơn thuần là `LIKELY ALREADY COVERED` | Giữ có giới hạn để qua feasibility/red team; đầu ra chỉ là đường giá trị theo cutoff hồi cứu | `EMPIRICAL QUESTION WORTH TESTING`: graph thêm/bớt giá trị thế nào khi bằng chứng bị cắt đồng bộ, kể cả coverage failures |
| C3 — Giữ danh tính operation để xếp service | `WEAK / NOT A RESEARCH GAP` ở formulation hiện tại; ý tưởng rộng `LIKELY ALREADY COVERED` | Không giữ làm RQ chính; chỉ có thể làm ablation phụ nếu một RQ sống sót thật sự cần | Kiểm tra representation trong một thực nghiệm; chưa có đóng góp độc lập được lập luận |
| C4 — Graph ở contextual scoring hay sau local scoring | `WEAK / NOT A RESEARCH GAP` ở formulation hiện tại | Không giữ làm RQ chính; có thể là so sánh phụ theo nhu cầu của một RQ sống sót | Kiểm tra vị trí đưa graph vào pipeline; chưa chỉ ra điều kiện khoa học riêng |
| C5 — Graph ở detector so với ranker | `LIKELY ALREADY COVERED` ở câu hỏi rộng; contrast detector–ranker hiện chưa đủ để thành gap | Hoãn RQ chính; không giữ chỉ vì gần định hướng giảng viên | Một đánh giá hệ thống có hai endpoint có thể hữu ích; chưa có methodological contribution và nhãn detector còn hạn chế |

Không hướng nào đạt `STRONG POSITIONING`. Hai hướng được giữ ở gate literature không đồng nghĩa hai hướng đã đủ sức cho luận văn hoặc phải cùng vào shortlist. C1 và C2 có estimand khác nhưng chia sẻ phần lớn hợp đồng; không được đếm chung một kết quả thành hai đóng góp độc lập. Red team có quyền loại cả hai.

## 2. Prior work gần nhất và đối chiếu đã xác minh

| Mã | Nội dung bằng chứng và nguồn chính | Giới hạn sử dụng |
|---|---|---|
| P1 | `PRIMARY-SOURCE FACT`: Eadro §V-G/Table IV thay GAT bằng FC; ablation này cùng ablation modality đã đo detection và localization. [Bài Eadro](https://arxiv.org/html/2302.05092). Task A C.7/F; TV-01 | Đã có câu hỏi graph có ích và fusion có ích. Không suy rằng mọi đối chứng thông tin quan hệ đã được thực hiện |
| P2 | `PRIMARY-SOURCE FACT`: DéjàVu §5.5/Fig.15 kiểm seen/unseen faulty failure units; Task A C.9/H còn ghi edge deletion và w/o aggregation. [Bài DéjàVu của tác giả](https://netman.aiops.org/wp-content/uploads/2022/11/DejaVu-paper.pdf). TV-02 | Scenario-held-out không phải novelty tự thân; failure unit của bài không đồng nhất service × fault của RE2-TT |
| P3 | `PRIMARY-SOURCE FACT`: BARO §4.8.1 thay vị trí anomaly boundary, §4.8.2 thay tham số. [Bài BARO](https://arxiv.org/html/2405.09330v1). TV-03 | Chưa đồng nghĩa cố định boundary rồi cắt đồng bộ tất cả telemetry/graph ở các cutoff khác nhau |
| P4 | `PRIMARY-SOURCE FACT`: MicroRank §5.4.4/Fig.13 thay số traces mỗi window, §5.4.3 khảo sát graph weights, §5.5 báo overhead thành phần. Task A C.3/I ghi operation ranking và service-level output khi production thiếu operation name. [artifact chính thức, file WWW2021_MicroRank.pdf](https://github.com/IntelligentDDS/MicroRank). TV-04 | Trace volume, graph weights, operation information và chi phí đã có tiền lệ. TV-04 chỉ xác minh các đoạn nêu trên, không chứng nhận mọi chi tiết baseline |
| P5 | `PRIMARY-SOURCE FACT` qua Task A C.6/D: CIRCA dùng graph parent set trong conditional residual rồi descendant adjustment; nhận external detect time. [Bài CIRCA](https://doi.org/10.1145/3534678.3539041), [artifact](https://github.com/NetManAIOps/CIRCA) | Contextual scoring đã tồn tại; causal/metric graph của bài không đồng nhất observed trace relation của RE2-TT |
| P6 | `PRIMARY-SOURCE FACT` qua Task A C.2/C.3/D: MicroRCA và MicroRank dùng graph ở localization sau local detection. [Bài MicroRCA](https://doi.org/10.1109/NOMS47738.2020.9110353), [bài MicroRank](https://doi.org/10.1145/3442381.3449905) | Đối chiếu pipeline là prior về stage; lấy điểm từ hai paper khác nhau không tạo fair comparison |
| P7 | `PRIMARY-SOURCE FACT` qua Task A C.10–C.12/F: DeepTraLog graph-level detection; GDN graph-conditioned forecast residual; ARMOR graph representation cho detector và localizer. [DeepTraLog](https://doi.org/10.1145/3510003.3510180), [GDN](https://doi.org/10.1609/aaai.v35i5.16523), [ARMOR v3](https://arxiv.org/abs/2603.25538v3) | GDN không phải microservice RCA evidence; ARMOR là bản tác giả có giới hạn publication metadata ghi trong Task A. Không lấy sự khác biệt miền làm bằng chứng gap |
| P8 | `PRIMARY-SOURCE FACT` qua Task A C.8/I: TORAI dùng operation-derived trace time series, xếp service rồi indicator, có missing-trace evaluation. [Bài TORAI](https://doi.org/10.1145/3808137), [artifact](https://github.com/phamquiluan/RCAEval/tree/fse26) | Indicator không tạo operation-root GT; RE2-TT release phải theo Task B |

**Hiệu chỉnh bắt buộc:** câu Task A C.3 về thu thêm khoảng năm phút trace sau trigger không được dùng để tạo gap “giảm chờ năm phút”. TV-04 xác minh thao tác flush detection window nhằm tránh repeated detection; không xác lập một post-alert wait bắt buộc. Task A được giữ nguyên; Task C dùng hiệu chỉnh được ghi rõ này.

## 3. C1 — Giá trị thông tin tăng thêm của quan hệ service

**Contrast được xét:** trên cùng failure case, cùng telemetry hợp lệ, cùng bằng chứng cục bộ, cùng candidate universe, root/fault labels chỉ dùng chấm kết quả, hỏi quan hệ service quan sát được có thêm thông tin để xếp root service hay không. Đối chứng phải phân biệt thông tin gắn với quan hệ giữa đúng các service với lợi ích do capacity, smoothing hay topology nuisance. Đây là thay đổi thông tin trong một pipeline; không phải can thiệp vào hệ thống để chứng minh nguyên nhân vật lý.

| Sáu câu hỏi bắt buộc | Đánh giá |
|---|---|
| 1. Cùng câu hỏi đã được trả lời? | `PRIMARY-SOURCE FACT`: P1/P2/P6 đã hỏi lợi ích graph/aggregation và cho thấy graph sai có thể gây hại. `TASK-C INFERENCE`: “graph có giúp không?” đã quá rộng; câu hỏi tăng thông tin khi local evidence/candidates cố định hẹp hơn |
| 2. Cùng cơ chế đã được đánh giá? | Có graph vs no graph, w/o aggregation và graph perturbation. Chưa chọn cơ chế mới, nên không có methodological novelty để tuyên bố. TV-01 không xác lập rằng P1 đã kiểm đầy đủ matched information/capacity/nuisance contrast |
| 3. Chỉ ghép buzzwords? | Không bắt buộc, nếu chỉ xét giá trị quan hệ. Thêm multimodal, GNN hoặc causal naming không làm contrast mạnh hơn |
| 4. Gap chỉ là implementation difference? | Sẽ đúng như vậy nếu chỉ đổi model hoặc chạy lại graph ablation trên RE2-TT. RE2-TT khác collection không tự là contribution |
| 5. Có điều kiện khoa học đáng đo mà prior chưa cô lập đầy đủ? | `TASK-C INFERENCE`: có một điều kiện đủ cụ thể để kiểm: sau khi loại khác biệt evidence và nuisance, lợi ích còn gắn với relations giữa đúng service hay không. Kết quả âm cho thấy cải thiện graph-on/off có thể không xuất phát từ thông tin quan hệ; kết quả dương chỉ hỗ trợ setup đã xét. Task A/TV chưa đủ để nói literature-wide chưa từng làm |
| 6. Loại đóng góp? | Tiềm năng **empirical contribution**, không phải phương pháp mới. Phân tích graph missingness tự nhiên chỉ là robustness phụ/limitation, không tự nâng thành hướng chính |

**Phán quyết:** `DEFENSIBLE BUT INCREMENTAL`, giữ có giới hạn. Phần có ý nghĩa là quy kết lợi ích thực nghiệm cho thông tin quan hệ, với uncertainty và cases bất lợi; không phải một bảng MRR có graph cao hơn. Cần bác bỏ được giả thuyết graph thêm thông tin: nếu lợi ích biến mất dưới đối chứng công bằng hoặc không phân biệt được với nuisance, không được công bố graph evidence giúp. Đây vẫn là kết quả âm hợp lệ của câu hỏi; nó không tự cứu một thiết kế quá yếu/cỡ mẫu quá nhỏ.

**Điều kiện loại khỏi shortlist:** nếu hợp đồng cuối chỉ giữ graph on/off, không thể tạo controls hợp lệ mà không thay local evidence/candidate set, hoặc mọi ý nghĩa còn lại chỉ là một dataset replication. Khi đó hạ C1 xuống ablation, không viết “sẽ nghiên cứu sâu hơn” để giữ ghế.

## 4. C2 — Giá trị graph theo ngân sách event-time

**Contrast được xét:** với incident boundary đã được cung cấp, tại mỗi cutoff chung cho tất cả modalities, graph và comparators, đo chênh lệch service-ranking giữa graph và control rồi xem chênh lệch đó thay đổi theo ngân sách evidence thế nào. Quantity chính là **sự thay đổi giá trị tăng thêm của graph theo cutoff**, không chỉ “thu thêm dữ liệu thì tốt hơn”. Coverage được báo cùng kết quả; candidate bị thiếu không bị xóa khỏi mẫu chấm.

| Sáu câu hỏi bắt buộc | Đánh giá |
|---|---|
| 1. Cùng câu hỏi đã được trả lời? | P3 có boundary sensitivity, P4 có trace-count sensitivity và overhead. “RCA theo thời gian/evidence volume” không còn là câu hỏi mới. TV-03/04 chưa cho bằng chứng cùng contrast graph-value × matched multimodal cutoff |
| 2. Cùng cơ chế đã được đánh giá? | Thay window/volume/graph weights có prior. C2 không đưa cơ chế mới; tách cố định boundary khỏi cutoff mới là định nghĩa estimand khác, không tự là novelty |
| 3. Chỉ ghép buzzwords? | Không nếu giữ đúng evidence budget và endpoint service rank. Các từ online, real-time, anytime hoặc multimodal không được dùng để nâng claim vượt event-time replay |
| 4. Gap chỉ là implementation difference? | Là implementation difference nếu chỉ đo runtime hoặc thêm vài window lengths cho baseline. Một trace-count sweep đã gần P4. Không dùng lời giải thích “baseline phải đợi năm phút” vì đã bị TV-04 bác cách diễn giải đó |
| 5. Có điều kiện khoa học đáng đo mà prior chưa cô lập đầy đủ? | `TASK-C INFERENCE`: có: graph có bù được evidence cục bộ còn ít hay cần đủ evidence cấu trúc mới có lợi, khi các nhánh đều chỉ thấy cùng prefix? Tương tác này có thể bằng không hoặc đổi dấu; không tương đương sensitivity của boundary hay số trace. Tuy vậy chưa được chứng minh là chưa ai nghiên cứu ngoài pack |
| 6. Loại đóng góp? | Tiềm năng **empirical contribution** về điều kiện hoạt động; sensitivity/robustness là phần phụ. Không phải detector mới, scheduling policy, stopping rule hay latency SLA |

**Phán quyết:** `DEFENSIBLE BUT INCREMENTAL`, giữ có giới hạn. Cần tách thay đổi ranking khỏi thay đổi candidate coverage; cùng cutoff không có nghĩa có cùng số bản ghi giữa modalities. Prefix kết thúc ở event-time không cho biết collector đã nhận đủ dữ liệu khi đó. Chi phí xử lý có thể mô tả riêng, không biến thời gian sự kiện thành thời gian chẩn đoán vận hành.

**Điều kiện loại khỏi shortlist:** nếu chỉ còn average accuracy tăng theo prefix hoặc runtime table; nếu graph/history/template/features nhìn thấy phần sau cutoff; hoặc câu hỏi thực tế muốn nói “phát hiện sớm”/“dừng an toàn” nhưng không có nhãn và protocol tương ứng. Không dùng missing-trace reconstruction hoặc FlashTicket mới như cách cứu C2 tự động.

## 5. C3 — Danh tính operation như biểu diễn trung gian

**Contrast được xét:** giữ hay gộp literal service–operation identity trước khi tạo service ranking; output/GT đều ở service. C3 không phải operation localization.

| Sáu câu hỏi bắt buộc | Đánh giá |
|---|---|
| 1. Cùng câu hỏi đã được trả lời? | P4/P8 và Task A I/L có operation evidence, indicator/finer units. Không xác lập mọi controlled service-vs-operation pooling contrast đều đã được trả lời; nhưng prior đủ bác “dùng operation là gap” |
| 2. Cùng cơ chế đã được đánh giá? | Representation ở operation/trace event level đã có; exact encoder/pooling ở Task D còn chưa chọn. Không thể lấy việc chưa chọn implementation làm khoảng trống |
| 3. Chỉ ghép buzzwords? | Formulation không buộc buzzword, nhưng “fine-grained graph” không phải contribution. Node nhiều hơn không là bằng chứng tốt hơn |
| 4. Gap chỉ là implementation difference? | Trong formulation hiện tại, có: thay granularity representation rồi xem service rank. Chưa chỉ ra failure condition riêng khiến khác biệt này trả lời một câu hỏi khoa học vượt ablation |
| 5. Có điều kiện khoa học đáng đo mà prior chưa cô lập đầy đủ? | Có thể đo effect của gộp operation, nhưng “đo được” chưa đủ. Task A L đã yêu cầu lợi ích/định nghĩa/edge/label cụ thể. Chuẩn hóa C3 chưa cung cấp điều kiện unresolved độc lập; không được tự thêm cơ chế lỗi hoặc nhãn operation để tạo gap |
| 6. Loại đóng góp? | Hiện chỉ là **representation ablation**. Chưa có empirical/methodological contribution độc lập được biện minh |

**Phán quyết:** `WEAK / NOT A RESEARCH GAP` ở C3 hiện tại; không vào shortlist RQ chính. Có thể dùng làm ablation phụ nếu cần giải thích một kết quả C1/C2, nhưng không bắt buộc tăng scope. `VERIFIED — TASK B` B-003 cho phép representation nội bộ, không cho quantitative operation accuracy. Không nâng C3 bằng lời hứa thu operation GT trên FlashTicket sau này; đó là đổi câu hỏi và cần gate riêng.

## 6. C4 — Graph ở contextual scoring hay sau local scoring

**Contrast được xét:** so vị trí graph trước/trong score với graph chỉ dùng sau local score, cùng endpoint root-service ranking. Không có endpoint detection trong C4.

| Sáu câu hỏi bắt buộc | Đánh giá |
|---|---|
| 1. Cùng câu hỏi đã được trả lời? | P5 có contextual scoring; P6 có late graph ranking; P1/P2 có graph-conditioned representation. Stage taxonomy đã được biết. Không có bằng chứng rằng mọi stage comparison trên cùng data đã xong, nhưng thiếu một comparison không tự tạo research gap |
| 2. Cùng cơ chế đã được đánh giá? | Các cơ chế theo stage đều đã có. Chọn giữa chúng là implementation/model choice nếu không gắn với một điều kiện khoa học được nêu trước |
| 3. Chỉ ghép buzzwords? | Không nhất thiết; tuy vậy từ “contextual”, “causal” hoặc graph-first không thêm scientific contribution. Trace parent relation không đủ cho causal parent assumptions của CIRCA |
| 4. Gap chỉ là implementation difference? | Hiện đúng. “Đưa graph sớm hay muộn” dễ thay đồng thời scoring function, capacity, supervision và training; không thể quy cải thiện cho stage chỉ từ hai implementations khác nhau |
| 5. Có điều kiện khoa học đáng đo mà prior chưa cô lập đầy đủ? | Chưa được xác lập trong C4. Scenario-held-out là kiểm validity đã có tiền lệ P2, không là điều kiện cứu novelty. Không tự bịa failure class hay mechanism mới để giải thích tại sao stage matters |
| 6. Loại đóng góp? | Hiện là **pipeline ablation/comparative implementation study**, có thể phục vụ empirical study khác; chưa đủ độc lập |

**Phán quyết:** `WEAK / NOT A RESEARCH GAP`, không giữ RQ chính. Không gộp lén vào C1 vì C1 cố định local evidence còn C4 thay score. Nếu về sau dùng C4 làm supporting comparison thì phải ghi rõ contrast khác và kiểm nuisance; không được chuyển service MRR thành bằng chứng graph anomaly detection.

## 7. C5 — Graph ở detector so với ranker, hai endpoint riêng

**Contrast được xét:** graph tham gia detector/ranker ở đâu và ảnh hưởng thế nào tới detection-regime endpoint và diagnosis endpoint. Việc báo hai endpoint đúng là yêu cầu validity, chưa phải contribution.

| Sáu câu hỏi bắt buộc | Đánh giá |
|---|---|
| 1. Cùng câu hỏi đã được trả lời? | P1/P7 đã làm graph detection/joint AD-RCL; P6 làm local AD → graph ranker. Task A D/L xếp câu hỏi graph-aware AD rộng là `LIKELY ALREADY COVERED` |
| 2. Cùng cơ chế đã được đánh giá? | Có graph ở representation/detector/ranker, joint training và detector-first. Không được gọi thay pipeline placement là cơ chế mới khi chưa có contrast riêng |
| 3. Chỉ ghép buzzwords? | “Graph + detection + ranking” là tổng hợp chức năng đã có. Không dùng LLM sau ranker để tạo vẻ mới; lớp giải thích không thay detector/GT |
| 4. Gap chỉ là implementation difference? | Với C5 hiện tại, phần khác biệt chủ yếu là cấu hình pipeline và triển khai. Xây end-to-end FlashTicket có giá trị ứng dụng nhưng không chứng minh một research gap về phương pháp |
| 5. Có điều kiện khoa học đáng đo mà prior chưa cô lập đầy đủ? | Error propagation giữa detector và ranker có thể đáng đo, nhưng C5 chưa nêu điều kiện thất bại riêng/đối chứng nào khiến đây là gap vượt evaluation thông thường. RE2-TT còn chỉ hỗ trợ injection-regime agreement, không tự cho true anomaly onset, affected-node labels hay production false alarms (ledger T-002/B-002) |
| 6. Loại đóng góp? | Có thể là **systems/application evaluation** nếu thực hiện đầy đủ trong phạm vi được chọn; chưa đủ để giữ một RQ chính độc lập theo chuẩn Task C. Không có methodological novelty đã chứng minh |

**Phán quyết:** `LIKELY ALREADY COVERED`; hoãn khỏi shortlist chính. Không dùng mức phù hợp hướng dẫn giảng viên để bỏ qua gate literature. Hệ thống vẫn phải thực hiện nhiệm vụ phát hiện/chẩn đoán và đánh giá phù hợp DT18; hoãn C5 như RQ chính không có nghĩa bỏ các chức năng đã duyệt. Muốn tái mở C5 phải có câu hỏi khác đủ cụ thể và evidence/nhãn tương ứng; đó là đề xuất mới, không phải một “OPEN sau này” bảo đảm C5 sống sót.

## 8. Ranh giới kết luận và handoff

1. Các targeted checks đã giải bốn câu hỏi về prior; không còn dùng `NEEDS TARGETED VERIFICATION` như cách trì hoãn phán quyết cho C1–C5. Không có web call mới trong lượt gate này; các link nguồn chính lấy từ Task A/TV, không có paper mới nhập universe.
2. Task A không phải systematic exhaustive review. “Không thấy exact contrast trong pack” khác “chưa có trong literature”. C1/C2 được giữ như empirical questions có thể kiểm, không phải phát hiện novelty bằng lập luận vắng mặt.
3. C1/C2 cần đi tiếp qua feasibility/statistics/red team trước khi vào shortlist. Các câu hỏi effect-size có ý nghĩa thực tiễn, budget và mức tham vọng luận văn thuộc lựa chọn của Minh/giảng viên; dữ liệu không tự trả lời chúng. Không lựa chọn winner bằng số lượng ưu điểm.
4. Nội dung nên chuyển vào báo cáo chính thức khi đã được chọn và thực hiện: bảng closest prior, exact contrast, nguồn hiệu chỉnh MicroRank, giới hạn event-time/GT, controls và kết quả âm. Chưa viết contribution như kết quả đã đạt.
5. Chỉ tạo `task-c-literature-positioning.md`. Không thay nguồn/decision register. Phản biện góp ý đều giữ `CANDIDATE`; authority chọn RQ vẫn ở con người. Main agent kiểm complete diff/file set và chạy audit governance chung khi tổng hợp.


