# Task B — Subagent B: kiểm toán schema trace

**Trạng thái:** `RAW SAMPLE FINDING`  
**Vai trò:** Subagent B — Trace Schema Auditor  
**Phạm vi:** chỉ ba tệp `traces.parquet` có trong sáu mẫu đã được chọn trước. Không có kết luận nào dưới đây là tính chất của toàn bộ RCAEval.

## 1. Phạm vi, nguồn và cách tái lập

| Hạng mục | Giá trị kiểm toán |
|---|---|
| Dataset nguồn | `phamquiluan/RCAEval` trên Hugging Face |
| Revision đã khóa | `afeacb11bcc94dadfd1c8f483ee4377b2b8b614e` |
| Manifest đã đọc | `datasets/rcaeval/raw-samples/raw-download-manifest.json` |
| Kế hoạch sáu mẫu đã đọc | `audits/rcaeval/raw-sample-plan.json` |
| Raw trace đã kiểm | `re2ob_productcatalogservice_loss_1/traces.parquet`; `re2tt_ts-auth-service_cpu_1/traces.parquet`; `re3tt_ts-route-service_f2_1/traces.parquet` |
| Các sample không có `traces.parquet` trong manifest | `re1ob_productcatalogservice_cpu_3`, `re2ss_orders_loss_2`, `re3ss_carts_f1_1` |
| Không làm | Không tải thêm dữ liệu; không đọc repo sản phẩm; không suy diễn kiến trúc, graph hay quan hệ nhân quả |

Kiểm toán được tạo bằng script xác định [subagent_b_trace_schema.py](D:/Project/flash-ticket-rca-research/scripts/audit/subagent_b_trace_schema.py) với Python 3.12.10 và PyArrow 25.0.1:

```powershell
D:\Project\flash-ticket-rca-research\.venv\Scripts\python.exe -B D:\Project\flash-ticket-rca-research\scripts\audit\subagent_b_trace_schema.py
D:\Project\flash-ticket-rca-research\.venv\Scripts\python.exe -m json.tool D:\Project\flash-ticket-rca-research\results\subagent-b-trace-schema.json
```

Kết quả máy có thể kiểm lại được: [subagent-b-trace-schema.json](D:/Project/flash-ticket-rca-research/results/subagent-b-trace-schema.json). Script duyệt toàn bộ các hàng của ba file trace, không lấy mẫu dòng.

## 2. Kết quả tóm tắt ở mức mẫu thô

| Case | Hàng | `traceID` khác nhau | `spanID` khác nhau | `serviceName` khác nhau | `operationName` khác nhau | Cặp `(serviceName, operationName)` |
|---|---:|---:|---:|---:|---:|---:|
| `re2ob_productcatalogservice_loss_1` | 254,889 | 17,167 | 254,889 | 7 | 25 | 37 |
| `re2tt_ts-auth-service_cpu_1` | 1,143,435 | 6,707 | 1,143,435 | 27 | 122 | 152 |
| `re3tt_ts-route-service_f2_1` | 183,623 | 2,623 | 183,623 | 27 | 122 | 151 |

Trong từng file, `traceID`, `spanID`, `serviceName`, `operationName`, `startTimeMillis`, `startTime` và `duration` đều **có mặt trong schema và không có null/chuỗi rỗng**. `spanID` không trùng trong toàn bộ các hàng của từng file; cặp `(traceID, spanID)` cũng không trùng.

## 3. Schema quan sát được — `RAW SAMPLE FINDING`

Cả ba Parquet có cùng **đúng 11 cột** nullable sau; không có cột bổ sung hay cột dự kiến bị thiếu:

| Cột | Kiểu Arrow | Ý nghĩa có thể khẳng định từ dữ liệu thô |
|---|---|---|
| `time` | `large_string` | Chuỗi thời gian, ví dụ `18:08`, `09:56`, `20:01`; không phải một cấu trúc attribute |
| `traceID` | `large_string` | Định danh trace dạng chuỗi |
| `spanID` | `large_string` | Định danh span dạng chuỗi |
| `serviceName` | `large_string` | Tên dịch vụ dạng chuỗi |
| `methodName` | `large_string` | Chuỗi method, nhưng mức null khác nhau theo sample |
| `operationName` | `large_string` | Chuỗi operation tự do |
| `parentSpanID` | `large_string` | Định danh parent dạng chuỗi hoặc null |
| `startTimeMillis` | `int64` | Số nguyên thời gian |
| `startTime` | `int64` | Số nguyên thời gian |
| `duration` | `int64` | Số nguyên duration; đơn vị không được suy từ schema |
| `statusCode` | `int64` | Mã trạng thái dạng số nguyên hoặc null |

**Absent field, không phải present-but-null:** schema không có `span.kind`; không có `attributes` map; không có `events`/`links`; không có cột HTTP (method, URL, route, status, host), RPC (system/service/method), DB (system/operation/statement), messaging (system/destination/operation), peer, resource, container, pod hay process. Đây là kết luận từ danh sách 11 cột ở trên, không phải kết luận rằng các khái niệm đó không thể được ám chỉ bằng chuỗi tự do.

## 4. Trường identity, parent và tính toàn vẹn tham chiếu

`parentSpanID` được kiểm bằng lookup chính xác `(traceID, parentSpanID)` trong **cùng tệp raw**. Không dùng ID từ case khác, cũng không gán quan hệ parent–child là quan hệ gọi dịch vụ hay quan hệ nhân quả.

| Case | Hàng có `parentSpanID` không rỗng | Hàng `parentSpanID` null/rỗng | Parent khớp cùng `traceID` | Không khớp | Tỷ lệ khớp | Parent chỉ khớp ngoài `traceID` con | Self-parent |
|---|---:|---:|---:|---:|---:|---:|---:|
| `re2ob_productcatalogservice_loss_1` | 237,781 | 17,108 | 237,492 | 289 | 99.878460% | 0 | 0 |
| `re2tt_ts-auth-service_cpu_1` | 1,136,731 | 6,704 | 1,136,552 | 179 | 99.984253% | 0 | 0 |
| `re3tt_ts-route-service_f2_1` | 181,000 | 2,623 | 181,000 | 0 | 100.000000% | 0 | 0 |

`parentSpanID` là **present-but-null** ở các hàng không có parent ID: không có chuỗi rỗng nào. Các parent không khớp cũng không khớp với bất kỳ `spanID` nào khác trong chính raw file; nguyên nhân thiếu parent là `UNKNOWN` trong phạm vi audit này.

Trong các parent đã khớp, số hàng có `serviceName` của con khác `serviceName` của parent lần lượt là 103,059; 166,132; 42,048. Đây chỉ là đếm một thuộc tính gắn với quan hệ ID quan sát được, **không phải** bằng chứng về `CALLS`, topology hay propagation.

## 5. Timing và status — `RAW SAMPLE FINDING`

| Case | Duration âm | Duration bằng 0 | `floor(startTime / 1000) = startTimeMillis` | Cặp parent–child có thể so thời gian | Child bắt đầu trước parent | Child kết thúc sau parent |
|---|---:|---:|---:|---:|---:|---:|
| `re2ob_productcatalogservice_loss_1` | 0 | 0 | 254,889 / 254,889 | 237,492 | 0 | 0 |
| `re2tt_ts-auth-service_cpu_1` | 0 | 0 | 1,143,435 / 1,143,435 | 1,136,552 | 8 | 18,114 |
| `re3tt_ts-route-service_f2_1` | 0 | 0 | 183,623 / 183,623 | 181,000 | 160 | 8,239 |

Số học trên được báo nguyên trạng; audit không suy ra nguyên nhân cho các dòng thời gian không lồng nhau. Vì schema không mô tả đơn vị của `duration`, kết quả cũng không gán đơn vị cho trường này.

`statusCode` có mặt trong tất cả schema nhưng:

| Case | `statusCode` null | Giá trị khác null quan sát được |
|---|---:|---|
| `re2ob_productcatalogservice_loss_1` | 12,634 | `0`: 242,039; `14`: 198; `4`: 12; `2`: 4; `13`: 2 |
| `re2tt_ts-auth-service_cpu_1` | 1,143,435 | Không có |
| `re3tt_ts-route-service_f2_1` | 183,623 | Không có |

Do đó `statusCode` trong hai sample Train Ticket là **present-but-all-null**, không phải cột bị thiếu.

## 6. Service, operation và method

| Case | `methodName` null | Giá trị `methodName` khác null | `operationName` null | Giá trị `operationName` khác null |
|---|---:|---:|---:|---:|
| `re2ob_productcatalogservice_loss_1` | 12,634 | 16 | 0 | 25 |
| `re2tt_ts-auth-service_cpu_1` | 1,143,435 | 0 | 0 | 122 |
| `re3tt_ts-route-service_f2_1` | 183,623 | 0 | 0 | 122 |

Ví dụ raw `methodName` phổ biến trong Online Boutique: `GetProduct` (103,183 hàng), `Convert` (54,938), `GetSupportedCurrencies` (20,324). Hai sample Train Ticket có cột `methodName` nhưng toàn bộ giá trị null.

`operationName` không phải một vocabulary đồng nhất giữa ba sample:

| Case | Pattern chuỗi thô | Số hàng khớp | Ví dụ raw phổ biến |
|---|---|---:|---|
| Online Boutique | có literal `grpc` | 40,202 | `grpc.hipstershop.CurrencyService/Convert` (27,470); `grpc.hipstershop.CurrencyService/GetSupportedCurrencies` (10,163) |
| Train Ticket CPU | HTTP verb ở đầu chuỗi | 166,133 | `GET` (145,306); `POST` (20,827) |
| Train Ticket CPU | literal kiểu DB trong chuỗi | 404,766 | `StationRepository.findById` (264,653); `StationRepository.findByName` (35,180) |
| Train Ticket F2 | HTTP verb ở đầu chuỗi | 42,082 | `GET` (37,629); `POST` (4,453) |
| Train Ticket F2 | literal kiểu DB trong chuỗi | 48,445 | `TrainTypeRepository.findById` (12,128); `StationRepository.findById` (9,596) |

Các pattern trên là regex trên **chuỗi `operationName`**, không phải attribute HTTP/RPC/DB được chuẩn hóa. Không có literal kiểu messaging (`kafka`, `rabbit`, `queue`, `topic`, `publish`, `consume`, `produce`) trong `operationName` của ba sample này; điều đó không chứng minh messaging không tồn tại trong hệ thống hay dataset.

Trong mỗi sample, các exact `operationName` được dùng bởi nhiều `serviceName`: 10 giá trị ở Online Boutique, 11 ở mỗi sample Train Ticket. Ví dụ gồm `GET`, `POST`, `find ts.orders`, `TripRepository.findById`, và ở Online Boutique là `hipstershop.ProductCatalogService/GetProduct`. Vì vậy, `operationName` độc lập không phải ID operation duy nhất theo service trong raw sample này.

## 7. Đánh giá ứng viên về operation identity

**Kết luận giới hạn:** cặp exact `(serviceName, operationName)` có thể được dựng máy móc từ hai trường luôn có giá trị ở ba sample và có 37 / 152 / 151 giá trị khác nhau. Đây chỉ là một **MODEL INPUT CANDIDATE** cho các thí nghiệm sau, chưa phải stable operation identity đã được xác minh.

Lý do chưa xác minh ổn định:

- `methodName` không nhất quán: có dữ liệu một phần ở Online Boutique và all-null ở hai Train Ticket samples.
- Cùng `operationName` xuất hiện dưới nhiều `serviceName`.
- Chuỗi operation khác kiểu giữa hệ thống (gRPC-like, HTTP verb/route-like, repository/DB-like), nhưng raw schema không lưu `span.kind`, protocol hay semantic attributes để phân loại chắc chắn.
- Audit chỉ có ba case trace-bearing; không đo được tính ổn định xuyên toàn bộ suite hay qua các revision.

Không suy ra graph, topology, operation ground truth, injection target hay causal propagation từ nhận định này. Các vấn đề đó thuộc kiểm toán graph, ground truth và cross-review độc lập.

## 8. Các giới hạn và câu hỏi chuyển giao

1. Ba sample có trace chỉ là một phần của sáu sample được chọn có mục đích; không đại diện thống kê cho RCAEval.
2. Ba sample còn lại không có tệp trace trong manifest raw đã tải, nhưng không được diễn đạt thành “RCAEval không có trace” hoặc “suite không có trace”.
3. `parentSpanID` resolution cao cho thấy tham chiếu ID có thể lookup trong raw sample; nó không xác minh loại span, chiều gọi RPC, graph `CALLS`, hoặc đường lan truyền nhân quả.
4. Các rows có parent nhưng timestamp không lồng nhau ở hai samples Train Ticket cần được giữ nguyên khi downstream dùng temporal constraint. Bất kỳ bộ lọc “sửa” những hàng này cần quy tắc rõ ràng và audit riêng.
5. Không có join key log/metric nào được đánh giá ở đây. Subagent D/E cần kiểm chứng độc lập trước khi nói về multimodal correlation.
