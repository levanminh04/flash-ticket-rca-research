# Task B — Subagent D: Metric Auditor

- Trạng thái: `DRAFT` — kiểm chứng độc lập trên dữ liệu thô.
- Phạm vi bằng chứng: `RAW SAMPLE FINDING` — đúng sáu ca trong kế hoạch mẫu; không suy rộng cho toàn bộ RCAEval.
- Mục tiêu: kiểm tra `metrics.parquet` thực tế, không suy diễn kiến trúc hệ thống từ tên cột.
- Nguồn: `phamquiluan/RCAEval` tại revision `afeacb11bcc94dadfd1c8f483ee4377b2b8b614e`, theo manifest tải mẫu cục bộ.
- Tệp sản phẩm: `audits/rcaeval/subagent-d-metrics-data.json` chứa toàn bộ schema và từng tên cột nguyên văn.

## 1. Cách kiểm tra có thể tái lập

Đã chạy script độc lập [audit_subagent_d_metrics.py](../../scripts/audit/audit_subagent_d_metrics.py) bằng Python 3.12.10, PyArrow 25.0.1 và pandas 3.0.6 trong môi trường nghiên cứu. Script chỉ đọc `raw-sample-plan.json`, `cases.parquet`, sáu thư mục `raw-samples/<case>/`, và không gọi mạng hay tải thêm dữ liệu. Nó kiểm tra đúng sáu case trong kế hoạch, đọc trực tiếp từng `metrics.parquet` bằng PyArrow, sau đó tạo JSON có đầy đủ schema, cột, missingness, thời gian và đối chiếu metadata.

Đã chạy script hai lần liên tiếp; JSON đầu ra giống nhau ở cả hai lần (`SHA-256: F164CEC7B88032AC7274C03D6D08EB4B7C88A7D972B893EAD00510FFD2FAB1DE`). Invariant check xác nhận: 6/6 case có metrics, mọi case có `time`, không case nào có cột raw per-row fault label, và mâu thuẫn inject-time RE1 vẫn được bắt.

Mọi mốc `inject_time`, `normal_timesteps` và `faulty_timesteps` dưới đây được xử lý là `PROVENANCE/EVALUATION ONLY`, đồng thời là `FORBIDDEN MODEL INPUT`. Chúng không được dùng để tạo đặc trưng, chọn cửa sổ đầu vào, hoặc suy ra nhãn theo từng hàng metrics.

## 2. Schema và cardinality quan sát được

`RAW SAMPLE FINDING`: cả sáu `metrics.parquet` đều là bảng wide-format. Trường thời gian duy nhất là `time` (`int64`); mọi trường còn lại là `double`. Không có cột riêng cho `service_id`, `resource_id`, `metric_name`, `trace_id`, `span_id`, `log_id`, `is_faulty`, `label`, hay `root_cause`.

Tên cột metrics thực tế được tách **chỉ** bằng quy tắc suffix hiện diện rõ ràng: `<entity_token>_<metric_identity>`. Các identity quan sát được là `cpu`, `mem`, `diskio`, `socket`, `workload`, `load`, `error`, `latency`, `latency-50` và `latency-90`. Danh sách đủ từng cột, schema Arrow và fingerprint có trong `subagent-d-metrics-data.json`; bảng dưới chỉ tổng hợp count đã máy kiểm tra.

| Case | Hàng | Cột metrics | Entity token tách được | Metric identity và số cột |
|---|---:|---:|---:|---|
| `re1ob_productcatalogservice_cpu_3` | 63 | 58 | 19 | cpu 12; mem 12; load 17; latency 10; error 7 |
| `re2ob_productcatalogservice_loss_1` | 1,441 | 72 | 12 | cpu 11; mem 11; diskio 5; socket 11; workload 11; error 3; latency-50 10; latency-90 10 |
| `re2ss_orders_loss_2` | 1,441 | 76 | 15 | cpu 15; mem 15; diskio 8; socket 15; workload 7; error 2; latency-50 7; latency-90 7 |
| `re2tt_ts-auth-service_cpu_1` | 1,441 | 369 | 68 | cpu 68; mem 68; diskio 67; socket 68; workload 28; error 14; latency-50 28; latency-90 28 |
| `re3ss_carts_f1_1` | 1,441 | 80 | 15 | cpu 15; mem 15; diskio 6; socket 15; workload 8; error 5; latency-50 8; latency-90 8 |
| `re3tt_ts-route-service_f2_1` | 1,801 | 316 | 68 | cpu 68; mem 68; diskio 26; socket 68; workload 27; error 5; latency-50 27; latency-90 27 |

Ví dụ tên cột nguyên văn cho thấy đây là token trong tên cột, không phải nhãn thực thể có kiểu: `productcatalogservice_cpu`, `frontend-external_workload`, `carts-db_cpu`, `ts-route-service_latency-90`, `ts-route-mongo_diskio`. Không có cột phân biệt chính thức service, database, queue, hoặc external dependency.

### Entity và resource identity

| Câu hỏi | Kết quả | Phân loại |
|---|---|---|
| Có entity ID riêng trong bảng metrics không? | Không. Chỉ có entity-like token nằm trong tên cột. | `RAW SAMPLE FINDING` |
| Có resource ID/type riêng không? | Không. Các token như `carts-db`, `ts-route-mongo`, `redis` có mặt nhưng ý nghĩa resource chỉ là suy diễn từ chuỗi. | `RAW SAMPLE FINDING` cho sự vắng mặt của trường; `UNKNOWN` cho loại resource thực sự |
| Có thể tạo một tập entity metric-level không? | Có, bằng quy tắc suffix tường minh nêu trên; phải giữ nguyên token gốc và không tự đồng nhất `frontend` với `front-end` hoặc `frontend-external`. | `DERIVABLE BY EXPLICIT RULE` |
| Có thể tạo resource node đáng tin chỉ từ metrics không? | Chưa. Cần evidence thô bổ sung hoặc quy tắc mapping được duyệt. | `REQUIRES EXTERNAL INFORMATION` |

## 3. Thời gian, metadata và cửa sổ bình thường/lỗi

`RAW SAMPLE FINDING`: `time` không null, không timestamp lặp, và các timestamp phân biệt có delta số học 1 trong cả sáu case. Giá trị có độ lớn giống Unix epoch seconds là một `INFERENCE`; `metrics.parquet` không chứa metadata về đơn vị hoặc timezone.

| Case | Khoảng `time` thô | Vị trí inject theo file | Đối chiếu metadata | Trạng thái cửa sổ |
|---|---|---|---|---|
| `re1ob_productcatalogservice_cpu_3` | 1685371737–1685371799; 63 hàng | inject 1685373255, sau `time_end` 1,456 giây; 63 hàng trước inject | `inject_time`, số cột/hàng và min/max đều khớp metadata | `UNKNOWN`: metadata nói 63 normal, 0 faulty; không có nhãn hàng thô |
| `re2ob_productcatalogservice_loss_1` | 1705342110–1705343550; 1,441 hàng | 720 trước, 1 đúng inject, 720 sau | Toàn bộ count/range khớp metadata | `UNKNOWN`: không có nhãn hàng thô |
| `re2ss_orders_loss_2` | 1705746259–1705747699; 1,441 hàng | 720 trước, 1 đúng inject, 720 sau | Toàn bộ count/range khớp metadata | `UNKNOWN`: không có nhãn hàng thô |
| `re2tt_ts-auth-service_cpu_1` | 1705917385–1705918825; 1,441 hàng | 720 trước, 1 đúng inject, 720 sau | Toàn bộ count/range khớp metadata | `UNKNOWN`: không có nhãn hàng thô |
| `re3ss_carts_f1_1` | 1732242483–1732243923; 1,441 hàng | 720 trước, 1 đúng inject, 720 sau | Toàn bộ count/range khớp metadata | `UNKNOWN`: không có nhãn hàng thô |
| `re3tt_ts-route-service_f2_1` | 1733601694–1733603494; 1,801 hàng | 900 trước, 1 đúng inject, 900 sau | Toàn bộ count/range khớp metadata | `UNKNOWN`: không có nhãn hàng thô |

`VERIFIED CONTRADICTION`: trong `re1ob_productcatalogservice_cpu_3`, `inject_time.txt` khớp chính xác metadata (`1685373255`) nhưng lại nằm sau raw metric end (`1685371799`) 1,456 giây. Vì vậy, case này không có quan sát metrics sau inject timestamp. Việc metadata vẫn tự nhất quán về `time_start`, `time_end`, `n_timesteps`, `n_metrics`, `normal_timesteps + faulty_timesteps` không giải quyết được mâu thuẫn giữa injection timestamp và khoảng metrics.

Do đó không có cơ sở từ sáu raw metrics để gán nhãn normal/faulty từng hàng. Một quy tắc dùng `inject_time` để cắt trước/sau chỉ là `CANDIDATE` cho đánh giá sau này và phải loại trừ case RE1 nêu trên hoặc xử lý nó rõ ràng; quy tắc đó không được trở thành model input.

## 4. Missingness và data quality

| Case | Ô null / tổng ô metrics | Tỷ lệ null | Số cột có null | Số cột all-zero không null | Hàng trùng hoàn toàn |
|---|---:|---:|---:|---:|---:|
| `re1ob_productcatalogservice_cpu_3` | 0 / 3,654 | 0.0000% | 0 | 7 | 0 |
| `re2ob_productcatalogservice_loss_1` | 916 / 103,752 | 0.8829% | 6 | 3 | 0 |
| `re2ss_orders_loss_2` | 1,520 / 109,516 | 1.3879% | 5 | 2 | 0 |
| `re2tt_ts-auth-service_cpu_1` | 736 / 531,729 | 0.1384% | 30 | 17 | 0 |
| `re3ss_carts_f1_1` | 170 / 115,280 | 0.1475% | 4 | 3 | 0 |
| `re3tt_ts-route-service_f2_1` | 21,494 / 569,116 | 3.7767% | 56 | 4 | 0 |

`RAW SAMPLE FINDING`: không có cột all-null. Null tập trung rõ nhất ở một số series latency/error: ví dụ `productcatalogservice_error` có 816 null ở RE2-OB; `front-end_error` có 754 và `orders_error` có 760 null ở RE2-SS; RE3-TT có nhiều latency series thiếu tới hơn một nghìn hàng. Danh sách nguyên văn của toàn bộ cột missing và all-zero có trong JSON audit.

`UNKNOWN`: all-zero không tự chứng minh metric hỏng, vắng quan sát hay không có sự kiện. Bất kỳ imputation, bỏ cột hoặc coi zero là valid observation đều cần quy tắc thí nghiệm riêng và phải báo cáo.

## 5. Joinability với trace, log và graph

| Mục tiêu join | Evidence trong metrics thô | Phân loại | Giới hạn |
|---|---|---|---|
| Chỉ mục metric theo thời gian | Cột `time` `int64` trong mọi case | `DIRECT` trong chính bảng metrics | Chưa xác minh unit/timezone hay đồng hồ với modality khác |
| Metrics ↔ trace/log event | Không có trace/span/log ID; chỉ có `time` | `TIME-WINDOW APPROXIMATION` | Không được gọi đây là exact multimodal correlation cho tới khi B/E kiểm tra raw trace/log timestamp và clock alignment |
| Metrics ↔ service-like entity | Prefix của tên cột có thể tách bằng suffix explicit | `SERVICE-LEVEL ONLY` | Cần canonicalization; ví dụ `frontend`, `front-end`, `frontend-external` là token khác nhau trong raw data |
| Metrics ↔ operation | Không có operation ID/name riêng | `NOT SUPPORTED` | Không suy operation từ metric name |
| Metrics ↔ resource node | Không có typed resource ID/type | `NOT SUPPORTED` từ metrics đơn lẻ | Token có hậu tố `-db`, `-mongo`, `-mysql` không đủ để khẳng định resource type |
| Metrics ↔ trace/span hierarchy | Không có trace/span/parent field | `NOT SUPPORTED` | Không tạo edge hay propagation path từ metrics alone |

Kết quả này ràng buộc graph construction: metrics có thể cung cấp time-indexed signals trên raw entity tokens, nhưng không tự cung cấp operation nodes, resource types, trace edges hoặc causal propagation. Mọi edge vượt quá token/time phải được C kiểm chứng từ evidence khác và gắn rõ `DERIVABLE BY EXPLICIT RULE`, `REQUIRES EXTERNAL INFORMATION` hoặc `NOT SUPPORTED`.

## 6. Kết luận của Subagent D

1. `RAW SAMPLE FINDING`: sáu mẫu đều có metrics wide-format, 58–369 metric columns, 63–1,801 rows, `time` là trường thời gian duy nhất; toàn bộ cột khác là `double`.
2. `RAW SAMPLE FINDING`: không có raw per-row anomaly/fault/root-cause label, cũng không có direct trace/span/log key trong metrics.
3. `RAW SAMPLE FINDING`: entity-like identity chỉ xuất hiện trong tên cột; resource identity có kiểu là `UNKNOWN` nếu chỉ dùng metrics.
4. `VERIFIED CONTRADICTION`: case RE1 CPU có inject timestamp ngoài raw range; không thể dùng nó làm fault window sau injection.
5. `RAW SAMPLE FINDING`: missingness khác nhau mạnh giữa mẫu (0–3.7767% ô metrics) và có cột all-zero; chưa có lý do để tự sửa, drop hay impute.
6. `UNKNOWN`: sáu case không đủ để kết luận prevalence dataset-wide, semantics chính xác của metric identities, hay độ đồng bộ timestamp giữa telemetry modalities.

## 7. Đề nghị cross-review và điểm cần phản biện

- Với B (trace): kiểm tra xem trace timestamps có cùng số epoch/clock với `metrics.time`, và liệu tên service trong traces có thể khớp token metrics mà không làm mất distinction `frontend`/`front-end`/`frontend-external`.
- Với E (logs/multimodal): kiểm tra raw log timestamp granularity và bất kỳ direct ID nào; không nâng time-window approximation thành direct join nếu không có khóa chung.
- Với C (graph): không tạo operation/resource node hoặc CALLS edge từ metrics một mình; parse suffix chỉ đủ tạo metric series keyed by raw token.
- Với F (ground truth/leakage): giữ `inject_time`, metadata timing và các count normal/faulty ngoài model input. Case RE1 phải được nêu rõ trong bất kỳ protocol đánh giá nào.
- Với G (reproducibility): đối chiếu hash và manifest của sáu file metrics; audit này đã đối chiếu row/column/time count với metadata nhưng không thay kiểm chứng checksum.

Chưa có bất đồng reviewer trực tiếp tại thời điểm viết vì audit này được thực hiện độc lập. Các câu hỏi trên là `UNRESOLVED` cho matrix cross-review của main agent, không phải kết luận theo biểu quyết.
