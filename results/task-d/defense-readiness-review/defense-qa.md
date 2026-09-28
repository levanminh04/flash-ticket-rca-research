# TASK D — “Nếu giảng viên hỏi…”

> **POST-HOC DEFENSE-READINESS REVIEW — CANDIDATE**  
> Không phải kết quả final efficacy. Không phải parameter selection. Không cho phép đổi method.

Các câu dưới đây là câu trả lời nói trực tiếp, ngắn và trung thực. “Đã chọn” luôn có nghĩa là chọn theo registry development của TD-v1.3, không có nghĩa là tối ưu phổ quát.

## PPR và vai trò của graph

### 1. Tại sao dùng graph?

Vì câu hỏi nghiên cứu không chỉ là service nào bất thường cục bộ, mà còn là dependency thực thi có bổ sung thông tin định vị root hay không. Graph cho phép so sánh có kiểm soát `L` (local-only), `O` (observed graph) và `R` (randomized topology) trên cùng local evidence; nó không mặc định rằng graph sẽ thắng.

### 2. PPR có phải nhóm tự nghĩ ra không?

Không. PageRank/PPR là cơ chế chuẩn; MicroRCA cũng dùng PageRank sau khi đảo anomaly graph trong code chính thức. Phần của nhóm là adaptation: cách dựng graph từ trace, personalization từ local score, hai hướng graph và grid damping. Prior work hỗ trợ primitive, không chứng minh exact TD-v1.3 parameterization. Nguồn: [MicroRCA paper](https://doi.org/10.1109/NOMS47738.2020.9110353), [MicroRCA official code](https://github.com/elastisys/MicroRCA/blob/master/MicroRCA.py), [NetworkX PageRank](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.link_analysis.pagerank_alg.pagerank.html).

### 3. Tại sao PPR phù hợp với C1?

PPR nhận chính local anomaly vector làm personalization rồi phân phối có kiểm soát theo dependency. Vì vậy `O-L` là estimand rõ: graph propagation có thêm giá trị gì ngoài cùng bằng chứng cục bộ. Đây là phép thử tăng thêm, không phải một bộ dự báo độc lập.

### 4. Tại sao không chỉ dùng degree hoặc centrality?

Degree/centrality chỉ phản ánh cấu trúc và có thể ưu tiên hub dù hub không bất thường. PPR giữ local anomaly evidence làm điểm neo, nên đúng hơn với estimand “topology có cải thiện evidence đang có không?”. Nhóm không tuyên bố degree kém hơn trên mọi dataset; nó chỉ không trả lời đúng câu hỏi chính đã đăng ký.

### 5. Tại sao PPR mà không GNN?

Vì C1 cần một operator minh bạch, tái lập được và giữ cố định local evidence để cô lập hiệu ứng graph. GNN sẽ thêm learned representation, capacity, training policy và hyperparameter, làm `O-L` không còn là so sánh graph propagation sạch. Điều này là quyết định scope/fairness, không phải bằng chứng rằng GNN kém.

### 6. Tại sao reverse-call direction?

Trace thô ghi caller → callee. Trong chẩn đoán, triệu chứng có thể xuất hiện downstream và cần dồn bằng chứng ngược về upstream caller; MicroRCA có lineage đảo graph trước PageRank. Đây là heuristic định hướng chẩn đoán, không biến trace edge thành causal edge.

### 7. Tại sao cũng thử undirected?

Vì hướng trace có thể thiếu hoặc không đủ đáng tin cho truyền evidence, trong khi adjacency vẫn có thể mang thông tin. Undirected là bounded alternative đơn giản nhất. Development chọn undirected `.5`, nhưng lựa chọn đó không chứng minh direction vô nghĩa hay graph causal.

### 8. Tại sao damping `.2/.5/.85`?

`.85` là mốc PageRank/MicroRCA quen thuộc; `.2` và `.5` tạo một grid nhỏ từ phụ thuộc graph thấp đến trung bình. Development chọn `.5`, nhưng không có theorem nói `.5` tối ưu. Đây là bounded registry, không phải continuous search.

### 9. Development `O < L` có làm PPR trở thành lựa chọn sai không?

Không. Primary estimand là đo xem observed topology có cải thiện local evidence hay không, nên một kết quả âm vẫn là kết quả khoa học hợp lệ. Development cho thấy method candidate hiện tại chưa cải thiện C1; nó không cho phép đổi operator để tạo kết quả đẹp hơn.

### 10. Hai case HELP có đủ chứng minh graph hữu ích không?

Không. Hai HELP chỉ là quan sát post-hoc trong 30 case; tổng thể có HELP/HARM/UNCHANGED = `2/6/22` và `O < L`. Chúng giúp hình thành giả thuyết cơ chế, không đủ cho claim efficacy hay graph gate.

### 11. Isolate-HARM hoặc `travel × loss` có cho phép thiết kế graph gate không?

Không. Phase 1 ghi rõ đó là post-hoc/candidate mechanism, sample nhỏ và không causal. Dùng chúng để tạo gate sau khi xem outcome sẽ tăng development selection exposure và chỉ có thể đi qua một amendment/version/review được Minh cho phép trước freeze; finding không tự cấp quyền tạo runtime rule. Final60 hiện vẫn chưa mở.

### 12. PPR primary khác value diffusion secondary thế nào?

PPR tìm stationary probability mass có personalization và damping; value diffusion trực tiếp làm mượt giá trị theo láng giềng. Một bên phân phối mass, một bên biến đổi score. Giữ diffusion secondary ngăn việc lấy một operator khác nghĩa để “cứu” kết luận primary.

## Local evidence, số liệu và data-quality gates

### 13. Tại sao window 300 giây?

Không có bằng chứng 300 giây là universal optimum. Nhóm chọn hai cửa sổ cân bằng 300 giây để có 30 bin cho robust summary mà vẫn ở gần incident, rồi đăng ký sensitivity 180/300/420 giây. Kết luận phải thừa nhận window sensitivity.

### 14. Tại sao bin 10 giây cho C1?

Mười giây là thỏa hiệp giữa temporal resolution và support cho sparse trace-count channel. Bin5 và bin20 được đăng ký trước; development cho thấy binning ảnh hưởng mạnh, nên nhóm không được gọi 10 giây là tối ưu.

### 15. Tại sao Q90 thay vì max hoặc mean?

Q90 giữ độ nhạy với phần đuôi cao nhưng giảm quyền quyết định của một spike duy nhất. Max là sensitivity đã đăng ký. Q90 là study-specific aggregation convention, không phải một hằng số do paper chứng minh.

### 16. Tại sao median/IQR?

Vì short-window telemetry có outlier và không nên giả định Gaussian; median/IQR bền vững hơn mean/SD. BARO và GDN hỗ trợ nguyên lý robust normalization, nhưng exact floors và windows của TD là adaptation. Nguồn: [BARO](https://arxiv.org/abs/2405.09330), [GDN](https://arxiv.org/abs/2106.06947).

### 17. Tại sao có relative floor?

IQR có thể rất nhỏ, làm một sai lệch nhỏ bị phóng đại. Relative floor đặt scale tối thiểu theo magnitude điển hình của chính channel. Nó không xử lý trường hợp median tuyệt đối và IQR đều bằng zero; khi đó absolute fallback mới hoạt động.

### 18. Tại sao có `1e-12`?

Nó là absolute nonzero fallback để tránh chia cho zero, không phải physical scale và không phải residual floor. Phase 2 cho thấy ở sparse count channels nó có thể tạo normalized magnitude rất lớn, nên phải disclosure rõ.

### 19. Biết `1e-12` có limitation rồi sao không sửa?

Vì limitation được phát hiện sau development; đổi floor lúc này là thay method dựa trên outcome. Phase 2 cũng cho thấy nó chi phối lambda-loss về số học nhưng không đủ giải thích L-MTL collapse: lag3 phục hồi mạnh dù affected scaler identities giữ nguyên. Vì chưa có causal isolation buộc amendment, nhóm giữ sealed method và ghi limitation thay vì tối ưu hậu nghiệm.

### 20. Tại sao `>=24/30` finite bins?

Đó là 80% completeness guard để median/IQR và Q90 không được tính từ một mảnh dữ liệu quá nhỏ. Exact 80% không có external optimum và chưa có direct sensitivity; nó là condition cho evidence usable, không phải detector threshold hay kết quả tuning.

### 21. Tại sao `>=5 distinct seconds` trong bin 10 giây?

Để một cụm sample trong một thời điểm không đại diện cho cả bin. Năm giây yêu cầu coverage trên ít nhất nửa interval. Exact cutoff là operational convention và hiện cần documentation hardening, không được gắn citation giả.

### 22. Tại sao local C1 chỉ dùng metrics + traces?

Vì C1 cần numeric evidence chung, align được và giống hệt giữa L/O/R để cô lập graph operator. Logs đòi hỏi một representation/model riêng và sẽ đổi estimand. Claim vì vậy chỉ áp cho C1 M+T, không nói logs vô ích.

### 23. Tại sao `log1p` trace count?

Trace counts có zero và heavy tail; `log1p` giữ zero xác định và nén chênh lệch theo cấp số nhân. Nó là transform minh bạch, không phải khẳng định counts trở thành Gaussian.

## C5

### 24. Tại sao G/L/ALL?

Đây là ablation feature-family trên cùng target/scaler: L dùng own lag và ép bốn context slots về zero; G dùng own lag cộng caller/callee graph-neighbor means và coverage; ALL dùng own lag cộng all-other same-type context trong hai context blocks. Vì context set và effective capacity khác nhau, `G > L` không thể quy hoàn toàn cho graph structure.

### 25. ALL cao hơn G thì graph có ý nghĩa gì?

Nó cho thấy all-other context có thể dự báo tốt hơn graph-restricted context trong registered model. Vì G và ALL đều có own lag nhưng dùng context sets và effective capacity khác nhau, không thể kết luận riêng graph gây ra gain. C5 trả lời predictive-context question, không phải causal graph proof.

### 26. Tại sao lag1?

Lag1 là autoregressive baseline có capacity thấp nhất, phù hợp warmup ngắn và dễ audit. Lag3 là sensitivity. Development lag3 phục hồi L-MTL mạnh, nên temporal-memory choice là material limitation và phản bác cách giải thích single-cause bằng `1e-12`.

### 27. Tại sao lambda chỉ có `.1/1/10`?

Ba giá trị logarithmic tạo regularization yếu, trung bình và mạnh mà không mở dense search. Lambda được chọn bằng pre-injection loss, không dùng incident labels. Phase 2 buộc giới hạn interpretation vì zero-scale channels chi phối objective.

### 28. Tại sao q `.95/.975/.99`?

Đó là ba operating points upper-tail từ vừa đến nghiêm, khóa trước outcome. Calibration block ngắn làm các quantile rời rạc, nên q=.95 là development-selected setting, không phải false-positive probability bảo đảm.

### 29. Tại sao streak3?

Ba bin liên tiếp tương đương 15 giây ở primary profile và giảm one-bin alerts. Streak1/3/5 chỉ là event-policy sensitivity; chúng không thay bin-level efficacy và không được dùng để chọn lại detector.

### 30. Tại sao refractory 300 giây?

Năm phút là quy ước gộp nhiều exceedance của cùng incident thành một alert episode, cùng order với observation window. Refractory60/300/600 cho thấy event counts nhạy với policy. Nó không phải SLA và không chứng minh detector tốt hơn.

## Randomization, evaluation và freeze

### 31. Tại sao R dùng 256 chains?

Để không phụ thuộc vào một randomized graph may mắn và giữ Monte Carlo budget cố định, tái lập được. 256 là compute/stability budget; chưa có direct convergence sensitivity nên không được nói nó bảo đảm mixing.

### 32. Tại sao 200E proposals?

Scale theo số edge giúp budget so sánh giữa case sizes; 200E là điểm giữa registered 100E/200E/400E diagnostics. Mobility đã được kiểm trên development, nhưng đó không phải bằng chứng stationarity hay perfect mixing.

### 33. Tại sao MRR là primary?

Vì ground truth là một injected root và nhiệm vụ là xếp root càng cao càng tốt. Reciprocal rank nhấn mạnh vị trí đầu và cho một endpoint dễ hiểu mỗi case. Hit@k/NDCG chỉ bổ sung, không được dùng để rescue primary.

### 34. Tại sao tie-aware expected reciprocal rank?

Vì nếu nhiều service đồng điểm, thứ tự tên không nên quyết định kết quả. Nhóm lấy kỳ vọng reciprocal rank trên tie interval; điều đó làm scoring công bằng và deterministic nhưng không xóa sự mơ hồ của tie.

### 35. Tại sao delta = `.05`?

Đó là prespecified smallest effect of interest của study, không phải SLA. Năm điểm MRR tương đương trực giác khoảng sáu trên 60 case đi từ rank 2 lên rank 1, giúp phân biệt “khác rất nhỏ” với “khác đáng kể về nghiên cứu”. Nguyên lý SESOI có nền tảng; exact `.05` là judgment của study. Nguồn nguyên lý: [Lakens 2017](https://pubmed.ncbi.nlm.nih.gov/28736600/).

### 36. Tại sao grouped development folds?

Vì repeats trong cùng root × fault cell không độc lập. Nhóm giữ cả cell trong một fold để giảm leakage khi chọn config. Với chỉ 10 cells, selection vẫn có variance; leave-cell diagnostics đã cho thấy winner instability.

### 37. Graph development đang thua local, sao vẫn giữ đề tài?

Đề tài khoa học hỏi graph có bổ sung giá trị hay không trong điều kiện xác định, không hứa graph phải thắng. Kết quả âm có kiểm soát, cơ chế failure và limitation là đóng góp trung thực; final claim phải theo data, không theo tên đề tài.

### 38. Tại sao không sửa method sau development?

Vì development đã phơi bày outcome, sửa operator, floor hoặc gate sẽ tăng selection exposure và phải quay lại Task D để version, review và ghi extra attempt trước freeze. TD cho phép con đường amendment có kiểm soát nếu Minh phê duyệt; nó không tự mở final60. Review hiện tại chưa thấy scientific blocker buộc phải dùng con đường đó.

### 39. Final60 dùng để làm gì?

Để đánh giá một lần các contrast của method đã được con người freeze: estimate L/O/R, G/L/ALL và uncertainty mà không tiếp tục tuning. Current-method predictions/labels của final60 vẫn sealed, nhưng TT90 đã có historical outcome exposure; vì vậy đây là prospectively frozen new contrast trên benchmark đã được nghiên cứu, không phải một test set sạch/untouched và không bảo đảm significance.

### 40. Nếu final60 graph vẫn thua thì luận văn còn giá trị gì?

Có. Khi đó kết luận đúng là observed graph/PPR hoặc graph-context method đã đăng ký không cải thiện baseline dưới benchmark và điều kiện này. Thiết kế paired, negative controls, failure analysis và boundary of applicability vẫn là evidence khoa học có giá trị.

### 41. FlashTicket đóng vai trò gì sau public benchmark?

Public benchmark cung cấp ground-truth-evaluable evidence cho phương pháp. FlashTicket là target system cho controlled transfer/validation: ánh xạ telemetry log/trace/metrics, dựng dependency graph, tích hợp cơ chế và kiểm chứng bằng fault có kiểm soát. Hai vai trò bổ sung nhau; chưa được tuyên bố hiệu quả FlashTicket trước khi các phép đo target-system thực sự hoàn tất.

### 42. Tại sao không coi passing data-quality gate là bằng chứng method tốt?

Vì gate chỉ nói input/selection đủ điều kiện để diễn giải. Nó không tạo efficacy, không sửa missing-not-at-random và không chứng minh threshold tối ưu. Kết quả method vẫn phải đến từ endpoint đã đăng ký.

### 43. Vì sao review này không tạo TD-v1.4?

Vì các điểm yếu hiện thấy là limitation hoặc rationale chưa được viết tập trung, chưa phải invariant/code mismatch hay ambiguity làm invalid inference. Bước đúng là harden documentation rồi để Minh quyết định freeze, không tự thay method.
