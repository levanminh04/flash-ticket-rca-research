# TD-v1.3 — Development preflight, báo cáo A–J

Owner: Minh. Phạm vi: 30 ca RE2-TT development đã được U27/U27R cho phép; không phải final evaluation. Quan sát được ghi FACT; diễn giải và đề xuất là CANDIDATE; quyền development là USER_CONFIRMED; human acceptance/final freeze còn OPEN. P là repository nguồn đồ án, W là repository thực nghiệm được chỉ định. Ngày lập: 28/09/2026.

## A. Executive verdict

**FINAL DEVELOPMENT VERDICT: PASS WITH LIMITATIONS.** Đã hoàn tất toàn bộ development30, mandatory sensitivity, integrated replay và RCD270/270; numerical, leakage/evaluator và scientific reviews đều CLOSED theo bằng chứng đã lưu. Coordinator đối chiếu các kết luận, không còn CRITICAL/MAJOR chưa xử lý trong phạm vi development được giao. Đây là kết luận thực thi và khả năng diễn giải có giới hạn, không phải phê duyệt phương pháp của con người, final freeze hoặc chứng minh graph có lợi.

Lý do không chọn PASS không điều kiện: C1 chưa hỗ trợ graph superiority; C5 có scale pathology, bất ổn độ lớn hiệu ứng và khác biệt capacity; dữ liệu có exposure/confounding và không chứng nhận production/FlashTicket performance. Không chọn RETURN TO TASK D vì không còn ambiguity, leakage, coverage/control hoặc comparator blocker bắt buộc sửa đặc tả hiện tại. Không chọn INVALID RUN vì các lỗi thực thi đã được phục hồi, full evidence hợp lệ và mọi failedattempt được giữ. Nếu sau này thay công thức/registry, vẫn phải amendment và review trước freeze.

Kết luận khoa học của đợt này: chuỗi development chạy được, nhưng chưa chứng minh graph tăng chất lượng chẩn đoán. C1 observed graph kém local trung bình; C5 có điểm phát hiện hữu ích trong một số nhóm nhưng lợi thế so với local phụ thuộc mạnh vào bin/lag và thang chuẩn hóa. Đây là hạn chế thực nghiệm quan trọng, không được giấu bằng một bảng điểm tổng hợp đẹp. Không thay công thức/registry để cứu kết quả.

Đề tài DT18 vẫn gồm xây dựng và đánh giá hệ thống bán vé phân tán, đồ thị, dữ liệu log/trace/metrics và cơ chế chẩn đoán chạy trên FlashTicket. Thực nghiệm public dataset không thay việc tích hợp và đánh giá hệ thống đích.

## B. Làm rõ C5 và amendment

Nguồn chính: [TD-v1.3](D:/Project/flash-ticket-platform/docs/research-rca/task-d-method-and-experiment-specification.md); SHA256 `34fd73f6a84dc6b45834bd7fd4cc7b86e19e54f1011de99735631f027ee18971`. Bản TD-v1.2 trước sửa được giữ nguyên byte: `task-d/td-v1.2-before-c5-amendment.md`, SHA256 `985f1c5fc983422272dfbde8b69ed5ff98ee4fdd1631af075d03788c3770ad54`.

Hai ambiguity D-E27-01/02 được phân tích bởi ba vai trò độc lập trước actual outcome. Coordinator chọn theo nhân quả thời gian, tính xác định và khả năng diễn giải, không bỏ phiếu. [Rationale](../../task-d/td-v1.3-c5-clarification-rationale.md) lưu alternatives/rejection/failure modes; [review receipt](../../task-d/td-v1.3-c5-reviews.json) lưu targeted review và xử lý findings.

| Vấn đề | Policy development TD13 | Lựa chọn không dùng và lý do |
|---|---|---|
| Neighbor membership | Tập E có scaler/input hợp lệ trong fit prefix; tách điều kiện fit own model và availability tại mỗi bin; frozen same-channel neighbor pool, mean trên phần đang available và coverage trên denominator đã khóa | Bắt mọi neighbor đủ own-model rows sẽ loại bằng chứng chỉ vì không đủ dữ liệu dự đoán riêng; availability động làm membership/denominator đổi theo thời gian sẽ trộn graph với missingness |
| Trace conflict | Replay theo event time; identity key xung đột bị quarantine; mask trace ở bin gặp xung đột cho hợp service liên quan; bảo toàn metrics/logs độc lập; không hồi tố bin/graph đã đóng | Mask mọi modality hoặc toàn bộ service vượt chứng cứ trace; hồi tố graph/bins bằng conflict tương lai vi phạm prefix causality |

Fit120s/warmup180s, model eligibility18 fit/9 calibration rows, cal-only nodes MODEL_ABSENT, event streak/refractory, exact weighted calibration và MT/MTL invariants được triển khai và kiểm theo đặc tả. Technical policy vẫn CANDIDATE trong development được ủy quyền; không biến thành USER_CONFIRMED algorithm hoặc human APPROVED. Không sửa TD sau khi nhìn các điểm số dưới đây.

## C. Evidence table và 16 câu falsification

Mức tin cậy trong bảng là độ chắc của kết luận giới hạn trên evidence đã kiểm, không phải xác suất thành công dự án. R033/R035/R036/R037/R038/R041 là các thư mục `results/task-e/e27-...` tương ứng.

| # | Câu hỏi | Evidence / kết quả | Tin cậy và giới hạn |
|---:|---|---|---|
| 1 | Local evidence informative? | R033: L MRR .744206, Hit1 17/30; không all-tie/empty/zero case ở cấu hình chọn | Cao trên development; không ngoại suy dataset khác |
| 2 | Local gần ceiling? | 13/30 chưa rank1; MRR còn .255794 headroom | Cao: mạnh nhưng không ceiling toàn bộ; không dùng ceiling để biện hộ graph thua |
| 3 | Graph có cấu trúc/mobility? | R019/022/026: 20–27 nodes,20–55 edges;30/30 case và180 topology jobs đạt kiểm invariant/mobility;46,080 draws đã giữ và kiểm lại không sinh mới | Cao cho finite controls; không chứng minh mixing hoặc topology causal truth |
| 4 | O khác L? | R033: ΔMRR −.041801;2ca tốt hơn,6ca kém,22ca không đổi | Cao cho số liệu; diagnostic interval[−.126229,.055841] không xác nhận superiority hay bounded-negative criterion |
| 5 | O khác R? | R033: ΔMRR +.024171; MC SE .000463; interval[−.005774,.079596] | Trung bình về scientific inference: vượt MC noise nhưng chưa vượt uncertainty/incidence và δ=.05 |
| 6 | Effect bị vài case chi phối? | Travel/loss là cell O−L dương duy nhất (+.252381); bỏ fault loss thì O−R thành −.003609 | Cao, yêu cầu giữ toàn bộ per-case/leave-group bảng |
| 7 | Ổn định root/fault/cell? | R033/036: hiệu ứng đổi theo nhóm và bin; R037: G−L .5974 giảm còn .00966 ở10s/.02836 ởlag3; G−ALL đổi dấu | Cao rằng không ổn định; thiết kế không cross đầy đủ root×fault nên không tách nguyên nhân nhóm |
| 8 | PPR/diffusion lỗi số học? | Independent numeric audit:69,120 ranks,46,080 graph invariants, equation residual tối đa5.83e−16; integrated PPR≤1.88e−16 | Cao trong saved evidence; không bảo đảm mọi input tương lai |
| 9 | C5 availability đủ? | R035:8 arms × 30 ca,7560/7560 bins/arm;0 unavailable/failures; R037:56summaries đều VALID | Cao trong development; system availability không đồng nghĩa mọi channel đều có model |
| 10 | G/L/ALL do graph hay capacity/missingness? | Target masks/model counts tương đương; effective df và feature count khác. ALL-MTL hơn G; bin10/lag3 làm local gần G | Không thể gán chênh lệch riêng cho graph; không có capacity-matched topology proof |
| 11 | Prefix/residual scale stable? | Hơn99.999999984% weighted normal forecast MAE do channel scaler1e−12;λ chọn thay khi bỏ cell; L threshold2.2169e14 | Cao rằng scale/selection có điểm yếu nặng; finite arithmetic không tự nghĩa là mô hình ổn định |
| 12 | Threshold/events usable? | G-MTL26/30có post-trigger, median delay60s có điều kiện,17 pretriggers/4.5 normal-hours; integrated plannedMRR .470935 | Chỉ đủ chứng minh bounded replay; chưa production alarm rate, còn miss/false alarm và diagnosis yếu theo nhóm |
| 13 | BARO/RCD fidelity? | BARO contextual adapter R033; RCD pinned real runtime018 và chunk-equivalence040; R041 đủ270 cấu hình, independent addenda CLOSED | BARO bounded qualified; RCD đã đủ270 chunks; numerical/leakage/scientific addenda CLOSED |
| 14 | Có leakage? | Independent033/035/036/037/038 audits kiểm seals, prefix, support, evaluator và first-trigger-only; không CRITICAL/MAJOR trong scope đó | Bounded assurance; API/process discipline không là OS sandbox;RCD041 đã kiểm và đóng |
| 15 | Buộc sửa D trước freeze? | Không có performance/sensitivity finding tự thân buộc sửa D; extreme scales là documented method/data weakness theo registered robustness policy | RCD và final reconciliation đã đóng; nếu đổi scaler/objective/registry phải amendment riêng trước freeze; hiện không tự đổi |
| 16 | Hỗ trợ/không hỗ trợ claim nào? | Hỗ trợ executable pipeline, input/control feasibility, negative/heterogeneous development observations, scale/capacity limitations | Không hỗ trợ graph superiority/necessity/novelty, final efficacy, production readiness, generalization hay FlashTicket validation |

## D. C1 development results

C1 đánh giá xếp hạng với cửa sổ trước/sau thời điểm chèn lỗi đã biết; không phải phát hiện sự cố tự động. Phần C5 và chuỗi trigger-to-ranking bên dưới kiểm tra câu hỏi khác, vì vậy không trộn các điểm MRR này thành một chỉ số duy nhất.

L chọn trước bằng absolute local MRR: floor .01, channel pool q90, availablemean fusion; PPR undirected damping .5, diffusion phụ undirected .85. Margin local .005806; PPR .001557. Leave-cell local giữ9/10, PPR7/10, diffusion9/10. Selection trên development không phải unbiased evaluation; không dùng O−L để chọn local.

| Arm | MRR | Hit1 | Hit3 | Hit5 | NDCG5 |
|---|---|---|---|---|---|
| L | 0.744206 | 0.566667 | 0.900000 | 0.933333 | 0.786968 |
| O | 0.702405 | 0.566667 | 0.800000 | 0.833333 | 0.726779 |
| R | 0.678235 | 0.566667 | 0.742708 | 0.800000 | 0.696040 |
| Ldiffusion | 0.744206 | 0.566667 | 0.900000 | 0.933333 | 0.786968 |
| diffusion | 0.720162 | 0.600000 | 0.833333 | 0.866667 | 0.752844 |
| Rdiffusion | 0.696729 | 0.585807 | 0.793750 | 0.828255 | 0.722158 |
| BARO | 0.659120 | 0.533333 | 0.733333 | 0.900000 | 0.709459 |
| Local_MAX_MT | 0.741178 | 0.566667 | 0.900000 | 0.933333 | 0.785507 |

Mẫu số30 ca giữ nguyên. R là trung bình **metric mỗi draw**, không rank của score trung bình; đủ256 draws/case. Tie-aware expected rank metrics dùng cùng chuẩn hóa/làm tròn giữa L/O/R. Không loại ca âm/khó hoặc chọn seed thuận lợi. Bảng per-case, ties, quality/cost nằm trong R033 `c1-results.json`; toàn bộ sensitivity trong R036 `c1-sensitivity.json`.

| OFAT | L MRR | O MRR | O-L | seconds |
|---|---|---|---|---|
| bin5 | 0.498343 | 0.337060 | -0.161283 | 7.37 |
| bin20 | 0.752963 | 0.754206 | 0.001243 | 16.21 |
| horizon180 | 0.703078 | 0.656938 | -0.046140 | 15.61 |
| horizon420 | 0.796734 | 0.786667 | -0.010067 | 17.51 |
| floor-0.0001 | 0.433770 | 0.409822 | -0.023948 | 17.71 |
| floor-0.001 | 0.546522 | 0.486529 | -0.059993 | 15.74 |
| temporal-max | 0.652937 | 0.605289 | -0.047648 | 15.18 |
| old-cap20 | 0.583466 | 0.462749 | -0.120716 | 15.72 |
| old-fixed-fusion | 0.744206 | 0.702405 | -0.041801 | 15.92 |

Không có cấu hình PPR đăng ký trong primary curve vượt L đã chọn. Bin20 cho chênh lệch dương nhỏ .001243 không cứu claim chính. O−L interval và O−R interval đều giao δ=.05; đây là kết quả development chưa đủ precision cho kết luận confirmatory. 256 draws và50,000 bootstrap samples không phải số incident độc lập.

## E. C5 development results và tích hợp

λ chung10 chọn bằng forecast MAE MTL cho G/L/ALL; q=.95 mọi arm. Fit và calibration theo prefix, threshold chỉ dùng normal endpoints trong training-fold. Primary mỗi arm có3240normal+4320positive bins; không nhầm macroF1 với pooledF1. Labels là injection-regime proxy, không chứng nhận thời điểm anomaly thực hoặc causal truth.

| Detector | Macro P | Macro R | Macro F1 | q | Full threshold |
|---|---|---|---|---|---|
| G-MTL | 0.798049 | 0.649537 | 0.669994 | 0.95 | 5300.84 |
| L-MTL | 0.170600 | 0.050231 | 0.072555 | 0.95 | 2.21695e+14 |
| ALL-MTL | 0.807611 | 0.668750 | 0.690865 | 0.95 | 4361.7 |
| TV-MTL | 0.293692 | 0.048611 | 0.078600 | 0.95 | 2.40517e+24 |
| G-MT | 0.806515 | 0.665509 | 0.688862 | 0.95 | 4361.7 |
| L-MT | 0.175208 | 0.048611 | 0.072001 | 0.95 | 1.58891e+14 |
| ALL-MT | 0.806515 | 0.664583 | 0.687474 | 0.95 | 4361.7 |
| TV-MT | 0.321157 | 0.043519 | 0.074813 | 0.95 | 1.16505e+24 |

Extreme scales có ý nghĩa khoa học: sparse count có median/IQR0 vẫn có ít nhất một positive fit observation, dẫn scaler1e−12 theo rule đã khóa. MAE bị các channel này chi phối; L forecast MAE hơi tốt hơn G nhưng detectorF1 thấp hơn rất nhiều. Không được diễn giải thành graph cải thiện mọi forecast. Mean ridge df G/L/ALL MTL lần lượt1.194/1.085/1.264; same coverage không làm capacity giống nhau. M/T components giữ bit-identical giữa MT và MTL tại fixed config; logs thêm vào không có lợi phổ quát.

| MTL OFAT | G F1 | L F1 | ALL F1 | G-L | G-ALL |
|---|---|---|---|---|---|
| bin10 | 0.661715 | 0.652055 | 0.665116 | 0.009660 | -0.003401 |
| prefix240 | 0.740912 | 0.084072 | 0.747319 | 0.656839 | -0.006407 |
| lag3 | 0.679172 | 0.650814 | 0.656562 | 0.028358 | 0.022610 |
| residual-floor-0.001 | 0.608138 | 0.072555 | 0.618152 | 0.535583 | -0.010014 |
| residual-floor-0.1 | 0.684615 | 0.072555 | 0.703017 | 0.612060 | -0.018402 |
| relative-floor-0.0001 | 0.438039 | 0.072555 | 0.437744 | 0.365484 | 0.000294 |
| relative-floor-0.001 | 0.576171 | 0.072555 | 0.609233 | 0.503617 | -0.033062 |

Sensitivity gồm đúng7 OFAT×30 ca,56 detector summaries và40 event-only settings; không Cartesian search. Giữλ/q primary, calibration lại theo quy tắc từng variant; không thay primary bằng cấu hình đẹp hơn. G−L dương trên finite grid nhưng độ lớn không bền; ALL vượt G ở primaryMTL và nhiều variant. Numeric review đã đóng51flags do audit arithmetic/order/denominator; saved scalar equations exact, normwise ridge stationarity≤3.72e−15. Điều này không chứng nhận forward accuracy của bài toán điều kiện kém.

G-MTL:17 pre-injection triggers trên4.5giờ normal quan sát,26/30 ca có post-trigger; median delay60s chỉ trên26ca đó, range20–665s. Refractory60/300/600 tạo271/80/52total triggers; streak1/3/5 tại300s tạo82/80/76. Local post-trigger9→4→0 khi streak1→3→5. Đây không phải production false-alarm estimate.

| Detector/commonPPR | MRR/planned30 | Hit1 | Hit3 | Valid/30 |
|---|---|---|---|---|
| G-MT | 0.469988 | 0.400000 | 0.500000 | 26 |
| G-MTL | 0.470935 | 0.400000 | 0.500000 | 26 |
| L-MT | 0.013828 | 0.000000 | 0.000000 | 5 |
| L-MTL | 0.011483 | 0.000000 | 0.000000 | 4 |
| ALL-MT | 0.497766 | 0.433333 | 0.533333 | 26 |
| ALL-MTL | 0.511869 | 0.433333 | 0.566667 | 26 |
| TV-MT | 0.000000 | 0.000000 | 0.000000 | 0 |
| TV-MTL | 0.008333 | 0.000000 | 0.000000 | 1 |

R038 có124unique triggers:114valid,10insufficient-history;240detector-case compositions. Tất cả arm dùng chung PPR/MTL diagnosis; tên L/G/ALL ở bảng integrated là **detector**, không phải ranking arm. Chỉ firstpost trigger được chấm, absent/failure/history-short giữ0; later trigger tốt hơn không cứu case. G-MTL conditionalMRR .543386 trên26ca không thay plannedMRR .470935 trên30. Khác biệt so với C1 còn do horizon, placement, logs và missing-trigger penalty, không cô lập riêng detector cost.

## F. Comparator fidelity

BARO MRR .659120 là contextual adapter theo TD, cùng candidate/service mapping và known-window evaluation. Không tuyên bố tái lập nguyên benchmark/paper. RCAEval pinned commit `7600283af1ea5e2e9fff6f07124951d0e989de42`; source/patch/hash trong `baselines/task-e-source-manifest.json`. RCD chỉ bỏ cột time sau wrapper split như patch đăng ký; real engine đã qualified ở018, single-config process tương đương batch ở040(9configs,3testsPASS).

RCD034 aggregate9config timeout300s là lỗi ngân sách vận hành; ba primary seed của ca timing đã tốn303s. R039 giữ sáu completion records rồi native exit3221225477 ở604s, không phải timeout; không coi toàn attempt là COMPLETE. Nguyên nhân nội bộ của native crash chưa được xác định đầy đủ; thành công khi tách process chứng minh cách phục hồi chạy được, không chứng minh đã biết chính xác nguyên nhân crash. R041 tách process/checkpoint theo seed×bin,1800s/config,6workers; cùng algorithm/input/grid và đủ270 planned chunks. Tái dùng24 prior completed configurations theo provenance, không theo điểm số; các kết quả COMPLETE từ interrupted041 tiếp tục được giữ. Sáu abandoned chunks chưa có raw result đã được bảo toàn và chạy bù; không dùng failure zero của interruptedattempt để đánh giá phương pháp.

RCD041 đã hoàn tất270/270 cấu hình SUCCESS,30/30 ca,0 lỗi thực thi; mỗi bin giữ đủ90 seed runs. Mainbins5 giữ nguyên, không thay bằng bins3 có điểm cao hơn.

| RCD bins | MRR | Hit1 | Hit3 | Hit5 | NDCG5 | Summed completed-config seconds |
|---|---:|---:|---:|---:|---:|---:|
| 5 | 0.253367 | 0.122222 | 0.247009 | 0.395123 | 0.254162 | 11348.15 |
| 3 | 0.354273 | 0.255556 | 0.359419 | 0.430152 | 0.341115 | 11878.28 |
| 7 | 0.293702 | 0.166667 | 0.300814 | 0.412589 | 0.288224 | 8607.64 |

Tổng31834.07s là thời gian từng cấu hình thành công cộng lại, có cả các completion được tái dùng; không phải wall-time của resume mới, không gồm đủ mọi wasted/interrupted compute. Resume01 wall1850.146s và kết thúc bằng lỗi từ chối ghi đè6 directory chưa hoàn tất;102 kết quả mới của lượt đó vẫn được giữ. Resume02 wall205.914s, tái dùng264 COMPLETE và chạy đúng6 phần thiếu. Toàn041 có24 priorcompletedconfigs tái dùng từ034/039 và246 unique completed executions mới; 162/264 là số COMPLETE được tái dùng ở từng checkpoint, không cộng thêm vào270.

Không coi RCD thấp là chứng minh graph superiority: adapter/window/feature/service aggregation khác nhau; đây là contextual comparison trong development. Mọi seed, bin sensitivity và per-cell results được giữ. FinalresultSHA256 `7dcab2e14efa3552bde3d8c00696b9c5b6e17894547f363640e5b9bc0ef45969`. Ba scoped RCD audit addenda đã đóng; không chạy lại model để kiểm toán.


License: RCAEval MIT không tự chứng minh license độc lập của toàn upstream originalRCD; giữ giới hạn source provenance/license như qualification manifest. Sự đủ điều kiện chạy development không tự cấp quyền phân phối sản phẩm.

## G. Failure attribution và phân xử review

| Loại | Finding / xử lý |
|---|---|
| Spec ambiguity trước run | D-E27-01/02 → TD13 trước outcome, alternatives và targeted review/fixtures được lưu |
| Implementation bugs đã sửa trước affected fullrun | Input-clock/mask handling, pandas readonly-copy, C1 cascade selection, L normalization/tie parity, integrated fixture/contract boundary; dùng các qualified run IDs và failedattempt history, không xóa dấu vết |
| Engineering execution | RCD034 aggregate deadline quá ngắn;039nativeprocess crash;041interrupted raw-pending chunks; phục hồi từng phần, giữ thuật toán và mọi completed artifact |
| Reviewer-check artifacts | C5 scalar safe pooling vs vectorized mean/dot và denominator cancellation; initial flags giữ nguyên, adjudication đóng bằng exact equation/backward error; không sửa predictions |
| Method/data weakness | C1 không hơn local, tác dụng tập trung vài cell; C5 count-scale domination,λinstability,capacity/temporal sensitivity; TVdetector yếu; không tuning cứu kết quả |
| Expected limitation | Proxy labels/event-time replay, root×fault confounding, dataset/history exposure,30 cases10 cells, finite R chưa mixing proof, system availability khác per-channel coverage |
| Provenance packaging MINOR | Source snapshot text chuẩn hóa newline; raw source bytes khớp declaredhash; source recovery phải dùng bytes/hash hoặc khôi phục line endings, không hash normalizedtext như raworiginal |
| Unresolved development blocker | Không còn sau scoped RCD addenda và coordinator reconciliation; các gate formal/stage sau vẫn OPEN |

Ba reviewer đang có được sử dụng cho phần việc còn thiếu; không lập reviewer mới. Phần CLOSED chỉ tái mở khi source/input/hash đổi hoặc finding mới thực chất. Numerical audit đã đóng C1/C5/OFAT/integrated; leakage audit đã đóng thêm037 và040; scientific interpretation của C1/C5/OFAT/integrated đã lưu. Các addenda RCD cuối đã đóng bằng hai receipt độc lập và scientific closure; không mở lại phạm vi đã kiểm. Không cộng số vai trò/lượt thành năm reviewer độc lập.

## H. Files changed và bảo toàn

Exact paths/hash/purpose được chốt trong `development-preflight-file-inventory.json` và bản Markdown bên cạnh ở bước đóng gói cuối. Đây là inventory toàn gói D/E local, không tuyên bố tất cả mới tạo trong riêng lượt resume. Không commit/push. Các source runcontracts pin đúng phiên bản thực thi; gitHEAD chỉ là base, không đủ tái lập uncommitted code nếu thiếu manifest.

| Nhóm tệp | Mục đích | Kết quả đạt được |
|---|---|---|
| P `docs/research-rca/task-d-method-and-experiment-specification.md` | Sửa hai ambiguity C5 thành quy tắc có thể triển khai duy nhất | TD13 trước outcome; cùng hash xuyên suốt full development |
| P nguồn U27/U27R và hai decision registers | Lưu quyền chạy, sửa, review và giới hạn đúng lời người dùng | Không xin lại quyền đã cấp; không phê duyệt thuật toán thay người dùng |
| W `task-d/td-v1.2-before-c5-amendment.md`, `td-v1.3-*` | Snapshot, alternatives, lý do chọn/bác và review amendment | Bảo toàn lịch sử, tách policy khỏi outcome |
| W `scripts/task_e/loader.py`, `replay.py`, `input_adapters.py` | Kiểm đầu vào, cutoff, trace identity, graph và masks | 30 ca thực dùng được; log thiếu ở một ca được giữ, không loại M/T |
| W `ranking.py`, `detection.py`, `calibration.py`, `evaluator.py` cùng thư mục | Công thức xếp hạng, forecast, threshold, event và planned-denominator evaluation | Đủ C1/C5; đã kiểm phương trình, membership, masks, ties và event boundaries |
| W `worker.py`, `boundary.py`, `contract.py`, `execution.py` | Tách numeric worker khỏi metadata/evaluator; ghi provenance và seals | API/process boundary được kiểm; không tuyên bố OS sandbox |
| W `c1_development.py`, `c5_development.py`, `integrated_development.py` | Điều phối registry, local-first selection, sensitivity và first-trigger composition | Đủ development30,9 C1 OFAT,7 C5 OFAT,40 event settings; không mở grid mới |
| W `rcd_*`, `baselines/`, `environments/` | Qualify upstream, isolated runtime, chẩn đoán timeout/crash và phục hồi theo cấu hình | 270/270 kết quả cuối; giữ failed/interrupted attempts và đủ seed |
| W `tests/task_e/` | Fixtures từ đặc tả và regression cho bug thực chất | Các lần PASS/FAIL đều có receipt; không dùng fixture PASS thay efficacy |
| W `configs/`, development raw allowlist, `results/task-e/e27-*` | Registry/pins và toàn bộ đầu vào, đầu ra, source snapshots, cost/logs | Tái lập theo phiên bản thực chạy; không động final60 |
| W ba `final-*-review.md` và JSON audit | Review số học, leakage/evaluator và diễn giải độc lập | Đóng theo phạm vi, không đếm lượt agent thành reviewer mới |
| W `continuation-*`, report/inventory/repro và P state/handoffs/map | Phục hồi sau usage limit, tổng hợp và chỉ dẫn đọc | Có checkpoint, scope ledger, báo cáo16câu và danh mục hash |

Riêng lượt phục hồi cuối: thêm báo cáo A–J, các checkpoint/ledger, preservation plan/receipt, hai helper bảo toàn/chạy bù và helper đóng gói; bổ sung scoped RCD review receipts; cập nhật derived trạng thái sau bằng chứng. Không sửa numeric model source để cải thiện điểm số. Sáu thư mục chưa có seal được chuyển sang `e27-041-rcd-development-recovery/attempt-history/interrupted-01/`; toàn bộ18 tệp giữ byte/hash, không có COMPLETE artifact bị chuyển hoặc xóa.

P: canonical TD; nguồn U27/U27R; append research/project decisions; derived CURRENT, D/Ehandoff, ARTIFACT-MAP. W: TD snapshot/rationale/reviews, registry/environment locks/upstreampatch; execution modules/tests; datasetsdevelopmentallowlist; immutable run contracts/predictions/reviews/checkpoints/report. README P ngoài scope giữ hash `3646cb1b6e8da832e8b9513fd8318d749f7f5f6788b5d3223eda7f5a9a662274`.

## I. Reproducibility

P branch `codex/rca-research-program`, baseHEAD `3d7ec9d824d12c98dc233705ef50908b62adf235`; W branch `main`, baseHEAD `f49859df7664758f1143a1033535da7f6f29d7d6`. Dataset revision `afeacb11bcc94dadfd1c8f483ee4377b2b8b614e`;89telemetryobjects verified, M30/T30/L29(authcpu1missinglog). ExactDEV IDs/folds/smoke/seeds trong `configs/task-e-td13-development.json`. Final60 không mở.

Python3.12.10 với numpy2.5.3/pandas3.0.6/pyarrow25 cho controller; isolatedRCD Python3.9/numpy1.23.5/pandas2.0.1/scipy1.10.1/sklearn1.2.2 và pinned causallearn/customfiles; locks/qualification receipts ghi exactpackages. Máy i5-1240P/16GB; BLAS/OMP threads1 trong numericchildren. Chi phí theo run execution receipts và per-case/per-chunk seconds, không cộng reusedchunks như compute mới. Không có chứng nhận peak-RSS hay SLA production; thời gian này gồm các workload khác nhau, không phải phép đo latency phục vụ trực tuyến công bằng giữa mọi phương pháp.

Mỗi run có `run-contract.json`(command/source/input/TD/config/env/hardware), `source-manifest.json`, outputs/seals/logs và execution receipt khi kết thúc. Run034interrupted không có finalreceipt; run041 dùng resume receipt riêng. Không overwrite runID để tái lập. Read-only verification dùng các reviewer receipts đã lưu; không gọi predict để kiểm lại artifactCOMPLETE.

Exact commands, measured durations và run identity được đóng gói trong `development-preflight-reproducibility.json`. Khi cần một replay được ủy quyền riêng, lấy command của đúng contract, tạo runID mới với cùng nguồn/pins; không chạy command cũ trên thư mục cũ. Runtime inference không nhận path/service/label/τ; trusted controller/evaluator giữ metadata. Đây không phải sandbox chống maliciousworker.

Các điểm vào bằng chứng chính (đường dẫn tính từ tệp này):

- [R033 — C1, selection, per-case/group/precision](e27-033-c1-development-full/c1-results.json).
- [R035 — C5 primary, P/R/F1, calibration/selection](e27-035-c5-development-full/c5-selection.json).
- [R036 — toàn bộ C1 OFAT](e27-036-c1-development-sensitivity/c1-sensitivity.json).
- [R037 — toàn bộ C5 OFAT và event settings](e27-037-c5-development-sensitivity/sensitivity-summary.json).
- [R038 — first-trigger-to-ranking](e27-038-integrated-development/integrated-results.json).
- [R041 — RCD đủ seed/bin, per-case/group/cost](e27-041-rcd-development-recovery/rcd-development-results.json).
- [Numerical audit](final-numerical-review.md), [leakage/evaluator audit](final-leakage-review.md), [scientific interpretation](final-scientific-review.md).

Wall-time các stage hoàn chỉnh: C1 full100.92s; C1 OFAT137.85s; C5 full1437.88s; C5 OFAT2438.14s; integrated518.99s. Không cộng chúng với summed per-config RCD như một benchmark công bằng: concurrency, reused work và nhiệm vụ khác nhau. Run contracts chứa hardware/env và saved command để phân biệt.

## J. Remaining OPEN và vật liệu báo cáo đồ án

Development đã đóng. Những việc thật sự thuộc gate/stage sau: human method acceptance và năm independent assurance theo yêu cầu đánh giá chính thức; final freeze/nextstage authorization; final evaluation/extension dataset nếu được cấp quyền; tích hợp và đánh giá FlashTicket; explanation layer; production alarm/latency/resource validation; independent originalRCD license provenance. Không tự mởF/G/H/I hoặc bỏ trách nhiệm hệ thống DT18.

Nếu muốn sửa scaler count/objective/primarybin/lag/event sau khi biết điểm, phải versionD và review impact/selection-exposure trước futurefreeze. Hiện giữ nguyên TD13 và báo negative/unstable evidence. Chưa có lý do biến một finding performance xấu thành giấy phép thêm thuật toán.

Đưa vào báo cáo chính thức: lịch sử clarification trước outcome; dữ liệu/split/provenance và exposure; tableL/O/R, O−L/O−R với uncertainty/heterogeneity; equalcoverage nhưng capacitykhác; scale pathology và toàn sensitivity; first-triggerplanned denominators/censoring; comparator adaptation/failures; đối chiếu public dataset với trách nhiệm kiểm chứng trên FlashTicket. Không dùng số liệu này làm kết quả final hoặc khẳng định novelty.

## Coordinator reconciliation / closure

Scientific report SHA256 `5c4f41465961140590819938bacd1ef6ea42ef3bbf8bc9781c5fa676126ea593` đóng điều kiện cuối sau khi đọc numeric RCD receipt `ff12723ff950d062d5fd3d731104bf6d316e0a2e87608943d862c3f172b03430` và leakage RCD receipt `32c0b761c5de8216cc6263fa1c622ad1335a57fa5cae8cbfda871fe425679ade`. Coordinator chấp nhận kết luận bounded PASS WITH LIMITATIONS với toàn bộ giới hạn được ghi ở A/C/D/E/F/G/J; không lấy đa số phiếu làm căn cứ. Không còn bất đồng số học hay yêu cầu chạy thêm trong gói development này.

Các lần agent kết thúc lượt khi vẫn có pending chỉ là checkpoint lịch sử. Báo cáo này được chốt sau scientific CLOSED; toàn bộ review cũ được giữ, chỉ bổ sung phần evidence chưa có. Final run/check receipts được bảo toàn; không tạo reviewer mới. Báo cáo/inventory/reproducibility và canonical state là handoff, không cấp quyền F–I hoặc commit/push.
