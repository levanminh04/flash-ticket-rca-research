# Subagent C — Kiểm toán khả năng dựng đồ thị từ raw trace

**Trạng thái:** DRAFT · **Vai trò:** Graph Constructability Auditor độc lập  
**Phạm vi chứng cứ:** chỉ sáu raw sample trong `raw-sample-plan.json`; không đọc báo cáo của Trace Auditor hay các auditor khác; không tải thêm dữ liệu.  
**Quy ước phạm vi:** mọi số liệu bên dưới là **RAW SAMPLE FINDING**, trừ khi được ghi rõ là `UNKNOWN`. Không có câu nào là kết luận cho toàn bộ RCAEval.

## 1. Kết luận kiểm toán

Từ ba sample có `traces.parquet`, dữ liệu cho phép dựng một **đồ thị phụ thuộc quan sát từ trace** ở mức service và ở mức cặp `(serviceName, operationName)`. Nó dựa trên quy tắc join xác định được giữa `traceID`, `spanID` và `parentSpanID`.

Điều đó **không** chứng minh một đồ thị `CALLS` mạng, đồ thị tài nguyên, đồ thị messaging, hay đường lan truyền nhân quả. Schema trace không có `spanKind`, thuộc tính HTTP/RPC/database/messaging, peer endpoint, resource attributes, process/deployment identity, hoặc resource ID. Mọi nỗ lực gọi một cạnh parent-child là RPC/HTTP/messaging hoặc nhân quả phải được xếp là `NOT_SUPPORTED` hoặc `UNKNOWN` trong phạm vi raw sample này.

| Thành phần đồ thị cần có | Kết luận nghiêm ngặt | Trạng thái |
|---|---|---|
| Nhãn service xuất hiện trên span | Có trường `serviceName` không null trong cả ba raw trace sample | `DIRECTLY_OBSERVED` |
| Node service chuẩn hoá | Dùng chuỗi `serviceName` nguyên văn, không gộp/đổi tên | `DERIVABLE_BY_EXPLICIT_RULE` |
| Node operation chuẩn hoá | Dùng khoá `(serviceName, operationName)` khi cả hai có mặt | `DERIVABLE_BY_EXPLICIT_RULE` |
| Quan hệ span cha–con | Join `(traceID, parentSpanID)` sang `(traceID, spanID)` khi parent có trong raw file | `DERIVABLE_BY_EXPLICIT_RULE` |
| Cạnh service → service suy ra từ span cha–con khác service | Gom `parent.serviceName → child.serviceName` từ join hợp lệ | `DERIVABLE_BY_EXPLICIT_RULE` |
| Cạnh `CALLS` đã xác nhận là remote HTTP/RPC | Không có kind, protocol, peer, endpoint hay attributes để khẳng định | `NOT_SUPPORTED` |
| Node resource (DB, queue, host, topic…) | Không có định danh resource có cấu trúc; cần mapping/config/telemetry ngoài trace | `REQUIRES_EXTERNAL_INFORMATION` |
| Cạnh `USES` service → resource | Không có resource node quan sát được hoặc khoá join resource | `REQUIRES_EXTERNAL_INFORMATION` |
| Quan hệ messaging | Không có evidence về producer/consumer, topic/queue hay messaging kind | `NOT_SUPPORTED` |
| Cạnh lan truyền nhân quả | Trace parent-child và thời gian không phải nhãn causal propagation | `NOT_SUPPORTED` |

## 2. Raw artifacts và phương pháp kiểm tra

**RAW SAMPLE FINDING.** Kịch bản dưới đây chỉ đọc các đường dẫn đã có trong `datasets/rcaeval/raw-samples/`.

| Case | Raw `traces.parquet` tại chỗ | Số span đã kiểm tra | Schema raw |
|---|---:|---:|---|
| `re2ob_productcatalogservice_loss_1` | Có | 254,889 | `time`, `traceID`, `spanID`, `serviceName`, `methodName`, `operationName`, `parentSpanID`, `startTimeMillis`, `startTime`, `duration`, `statusCode` |
| `re2tt_ts-auth-service_cpu_1` | Có | 1,143,435 | Cùng 11 trường trên |
| `re3tt_ts-route-service_f2_1` | Có | 183,623 | Cùng 11 trường trên |
| `re1ob_productcatalogservice_cpu_3` | Không có file trace trong thư mục raw sample đã tải | — | Không suy diễn thêm |
| `re2ss_orders_loss_2` | Không có file trace trong thư mục raw sample đã tải | — | Không suy diễn thêm |
| `re3ss_carts_f1_1` | Không có file trace trong thư mục raw sample đã tải | — | Không suy diễn thêm |

Script tái lập: `scripts/audit/subagent_c_graph_constructability.py`. Script chỉ lấy danh sách case từ `audits/rcaeval/raw-sample-plan.json`, quét ba file trace hiện hữu, rồi ghi evidence machine-readable tại `audits/rcaeval/subagent-c-graph-constructability-evidence.json`.

Quy tắc join duy nhất được sử dụng là:

```text
parent_span = spans[(child.traceID, child.parentSpanID)]
chỉ chấp nhận khi child.parentSpanID có giá trị và parent_span tồn tại
candidate_service_edge = parent_span.serviceName -> child.serviceName
chỉ tạo khi hai service không rỗng và khác nhau
operation_key = (serviceName, operationName)
```

Không có parser heuristic nào được dùng để tách database, topic, URL, hay operation từ nội dung tên span.

## 3. Kiểm tra xác định được trên ID và liên kết span

### 3.1 Tính toàn vẹn của định danh

**RAW SAMPLE FINDING.** Trong từng file trace, `traceID` luôn dài 32 ký tự hex, `spanID` và `parentSpanID` có giá trị luôn dài 16 ký tự hex. Không có dòng trùng khoá composite `(traceID, spanID)`, không có `spanID` trùng ở phạm vi toàn bộ file đang kiểm, và không có self-reference `parentSpanID = spanID`.

| Case | Trùng `(traceID, spanID)` | Trùng `spanID` toàn file | `parentSpanID` rỗng/null | Parent có mặt | Parent resolve cùng `traceID` | Parent không resolve cùng `traceID` |
|---|---:|---:|---:|---:|---:|---:|
| `re2ob_productcatalogservice_loss_1` | 0 | 0 | 17,108 | 237,781 | 237,492 (99.8785%) | 289 |
| `re2tt_ts-auth-service_cpu_1` | 0 | 0 | 6,704 | 1,136,731 | 1,136,552 (99.9843%) | 179 |
| `re3tt_ts-route-service_f2_1` | 0 | 0 | 2,623 | 181,000 | 181,000 (100.0000%) | 0 |

`parentSpanID` rỗng/null chỉ được gọi là “không có liên kết parent trong raw row”; không được tự gắn nghĩa root span, trace bị hỏng hay sampling mà không có evidence khác.

### 3.2 Kiểm tra tương thích số học của thời gian

**RAW SAMPLE FINDING.** Với parent đã resolve, script kiểm tra biểu thức số học `parent.startTime <= child.startTime` và `parent.startTime + parent.duration >= child.startTime + child.duration`. Đây là kiểm tra consistency của số raw, không giả định unit hay suy ra quan hệ nhân quả.

| Case | Parent resolve | Nằm gọn trong interval parent | Không nằm gọn | Tỷ lệ nằm gọn trên parent resolve |
|---|---:|---:|---:|---:|
| `re2ob_productcatalogservice_loss_1` | 237,492 | 237,492 | 0 | 100.0000% |
| `re2tt_ts-auth-service_cpu_1` | 1,136,552 | 1,118,430 | 18,122 | 98.4055% |
| `re3tt_ts-route-service_f2_1` | 181,000 | 172,602 | 8,398 | 95.3602% |

Vì 18,122 và 8,398 liên kết parent đã resolve không thoả interval containment, không được dùng containment thời gian làm điều kiện ngầm để gọi các link còn lại là causal propagation. Nguyên nhân của chênh lệch này là `UNKNOWN` trong audit này: có thể là cách ghi duration, precision, clock/instrumentation hoặc một nguyên nhân khác. Audit không sửa hoặc lọc các row đó.

## 4. Chứng cứ cho từng loại node

### 4.1 Service node

**RAW SAMPLE FINDING — `DIRECTLY_OBSERVED` cho nhãn service trên mỗi span; `DERIVABLE_BY_EXPLICIT_RULE` cho node unique.** `serviceName` không null trong cả ba raw trace sample. Quy tắc node duy nhất là lấy exact string không rỗng; không lowercase, alias, map deployment hay gộp service.

| Case | Số `serviceName` khác nhau | Ví dụ evidence raw |
|---|---:|---|
| `re2ob_productcatalogservice_loss_1` | 7 | `frontendservice`, `productcatalogservice`, `currencyservice`, `checkoutservice` |
| `re2tt_ts-auth-service_cpu_1` | 27 | `ts-seat-service`, `ts-route-service`, `ts-station-service`, `ts-auth-service` |
| `re3tt_ts-route-service_f2_1` | 27 | `ts-admin-basic-info-service`, `ts-price-service`, `ts-route-service` |

Giới hạn: raw field chứng minh một label service đã được ghi trên span; nó không chứng minh pod, instance, version, namespace, deployment, ownership, hay danh tính service chuẩn của hệ thống ngoài raw sample.

### 4.2 Operation node

**RAW SAMPLE FINDING — `DERIVABLE_BY_EXPLICIT_RULE`.** `operationName` không null trong cả ba trace sample. Để tránh đồng nhất các label chung như `GET` giữa nhiều service, node được phép dựng duy nhất theo khoá `(serviceName, operationName)` nguyên văn. `methodName` không phải fallback an toàn: nó null 12,634/254,889 row trong sample Online Boutique và null 100% ở hai sample Train Ticket.

| Case | `operationName` khác nhau | Cặp `(serviceName, operationName)` khác nhau | Tên operation xuất hiện ở >1 service |
|---|---:|---:|---:|
| `re2ob_productcatalogservice_loss_1` | 25 | 37 | 10 |
| `re2tt_ts-auth-service_cpu_1` | 122 | 152 | 11 |
| `re3tt_ts-route-service_f2_1` | 122 | 151 | 10 |

Ví dụ phản chứng cho việc dùng raw name làm stable operation ground truth:

- Trong `re2tt_ts-auth-service_cpu_1`, raw `operationName = GET` xuất hiện ở 13 `serviceName`; `POST` xuất hiện ở 10 `serviceName`.
- Trong cùng sample, `TripRepository.findByTripId` xuất hiện ở cả `ts-travel-service` và `ts-travel2-service`; các string `find ts.orders`, `find ts.payment`, `find ts.trip` cũng nằm ở nhiều service.
- Trong `re2ob_productcatalogservice_loss_1`, `hipstershop.ProductCatalogService/GetProduct` xuất hiện với `checkoutservice`, `frontendservice` và `productcatalogservice`.

Do đó, một label operation đơn lẻ không phải node operation ổn định. Khoá cặp nêu trên là một quy tắc tái lập cho raw graph, không phải xác nhận semantic operation hoặc ground truth ở mức operation.

### 4.3 Resource node

**RAW SAMPLE FINDING — `REQUIRES_EXTERNAL_INFORMATION`.** Không có cột resource identity, database name có cấu trúc, host, peer endpoint, DB system, table/collection field, topic hay queue trong schema trace của ba sample. Một vài `operationName` có string gợi ý như `find ts.orders` hoặc chứa `mongo` (4,160 raw row trong sample `re2tt...`, 1,462 trong `re3tt...`), nhưng đó là text operation không có schema chứng minh resource ID, relationship, hay cardinality.

Không được trích `orders`, `payment`, Mongo hoặc bất kỳ token nào từ tên operation để tạo resource node bằng heuristic. Để có node resource cần nguồn ngoài trace được version/provenance rõ ràng, ví dụ một mapping được kiểm toán hoặc một modality khác có resource key. Nguồn đó chưa được dùng trong báo cáo này.

## 5. Chứng cứ cho từng loại cạnh

### 5.1 Span-parent edge

**RAW SAMPLE FINDING — `DERIVABLE_BY_EXPLICIT_RULE`.** Các parent reference được join bằng composite key trong mục 2. Điều này cho phép cạnh kỹ thuật `SPAN_PARENT_OF` hoặc `PARENT_SPAN → CHILD_SPAN` đối với parent resolve được. Nó không có nghĩa cạnh causal hoặc network.

### 5.2 Cạnh service → service suy ra từ trace

**RAW SAMPLE FINDING — `DERIVABLE_BY_EXPLICIT_RULE`, với nhãn chính xác là “trace-derived candidate invocation dependency”.** Nếu một parent span và child span đã resolve cùng trace, có service khác nhau, gom cạnh `parent.serviceName → child.serviceName`. Kết quả:

| Case | Parent-child cùng service | Parent-child khác service | Cặp service có hướng khác nhau | Ví dụ hướng có evidence raw |
|---|---:|---:|---:|---|
| `re2ob_productcatalogservice_loss_1` | 134,433 | 103,059 | 9 | `frontendservice → productcatalogservice` (47,402 pair), `frontendservice → currencyservice` (36,123 pair) |
| `re2tt_ts-auth-service_cpu_1` | 970,420 | 166,132 | 55 | `ts-basic-service → ts-station-service` (33,802 pair), `ts-ticketinfo-service → ts-basic-service` (23,894 pair) |
| `re3tt_ts-route-service_f2_1` | 138,952 | 42,048 | 55 | `ts-basic-service → ts-station-service` (7,195 pair), `ts-ticketinfo-service → ts-basic-service` (5,074 pair) |

Các số trên nói rằng parent-child span liên kết các `serviceName` đó trong raw file. Chúng không nói rằng đây là dependency toàn hệ thống, edge tĩnh, nguồn gây lỗi, hướng lan truyền, hay một RPC network được xác minh.

### 5.3 `CALLS` network/protocol, `USES`, và messaging

**RAW SAMPLE FINDING — `NOT_SUPPORTED` hoặc `REQUIRES_EXTERNAL_INFORMATION`.** Trong schema chỉ có 11 trường đã liệt kê; không có field `spanKind`, `http.*`, `rpc.*`, `db.*`, `messaging.*`, peer service, peer address, resource attributes hay link producer/consumer.

| Quan hệ được yêu cầu | Classification | Lý do không thể nâng mức kết luận |
|---|---|---|
| `CALLS` nghĩa là HTTP/RPC remote đã xác nhận | `NOT_SUPPORTED` | Parent-child không cho biết kind, protocol hay endpoint. Một child có thể là local/in-process instrumentation. |
| `USES` nghĩa là service dùng database/cache/queue cụ thể | `REQUIRES_EXTERNAL_INFORMATION` | Không có resource ID hoặc resource edge trong trace schema. |
| producer → topic/queue → consumer | `NOT_SUPPORTED` | Không có entity messaging, topic, queue, producer/consumer hoặc correlation key. |
| service → operation “thực thi span mang nhãn operation” | `DERIVABLE_BY_EXPLICIT_RULE` | Có thể tạo edge từ exact `(serviceName, operationName)` trong cùng row; semantic operation vẫn `UNKNOWN`. |
| temporal order / overlap | `DERIVABLE_BY_EXPLICIT_RULE` | Có `startTime`, `duration`; nó chỉ là quan hệ thời gian ghi nhận, không phải causal relation. |
| fault propagation | `NOT_SUPPORTED` | Không có propagation-path/affected-node labels trong raw trace schema; trace hierarchy không là nhãn nhân quả. |

## 6. Những điều không được suy ra từ evidence này

**RAW SAMPLE FINDING / UNKNOWN.** Các giới hạn dưới đây là ràng buộc cho mọi graph về sau được tạo từ raw trace này:

1. `parentSpanID` resolve không chứng minh parent gây ra child, cũng không xác định observed root cause.
2. Một cạnh service khác nhau từ trace không chứng minh service này gọi service kia qua network; chỉ chứng minh một parent-child span relation mang hai service label khác nhau.
3. `operationName` có thể là route, method, generic `GET`/`POST`, client label, server label hoặc chuỗi nội bộ. Dữ liệu raw sample không xác nhận loại nào cho từng row.
4. String `mongo`, repository name, `find ts.*`, URL path hay `grpc` không đủ để tạo resource/messaging node hoặc `USES` edge.
5. Không có trace file ở ba thư mục raw sample không được diễn đạt thành tính chất của suite, hệ thống, hay toàn dataset.
6. Các tỷ lệ resolve và cardinality chỉ mô tả ba file đã kiểm; không đại diện cho RCAEval-wide prevalence.
7. Bất kỳ mapping đến service implementation, topology triển khai, resource, injection target hay root-cause label đều nằm ngoài chứng cứ trace này và phải đi qua audit có raw evidence tương ứng.

## 7. Kết luận dùng được cho cross-review

**RAW SAMPLE FINDING.** Một candidate graph tối thiểu có thể tái lập từ trace-bearing sample là:

```text
ServiceNode(serviceName)
OperationNode(serviceName, operationName)
ParentSpanEdge((traceID, parentSpanID) -> (traceID, spanID))
CandidateServiceDependency(parent.serviceName -> child.serviceName)
```

Node resource, `USES` edge, messaging relation, confirmed RPC/HTTP `CALLS`, causal propagation edge, stable semantic operation identity và dataset-wide graph claims vẫn cần evidence khác hoặc phải giữ `UNKNOWN`. Khi cross-review với các auditor khác, mọi đề xuất mạnh hơn mức trên cần chỉ ra raw field, exact rule và case cụ thể; không được thay evidence bằng suy luận kiến trúc.
