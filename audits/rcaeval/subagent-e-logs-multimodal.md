# Subagent E — Audit log và khả năng nối đa modal của RCAEval

- Trạng thái: `DRAFT` · `RAW SAMPLE FINDING`
- Phạm vi: chỉ sáu thư mục mẫu đã được chọn trong `datasets/rcaeval/raw-samples/`; đây **không** là kết luận cho toàn bộ RCAEval.
- Nguồn và revision: `phamquiluan/RCAEval` trên Hugging Face, revision `afeacb11bcc94dadfd1c8f483ee4377b2b8b614e`, đối chiếu với `raw-download-manifest.json`.
- Độc lập: không đọc báo cáo của các reviewer Trace, Graph hay Metric; chỉ đọc raw-sample plan/manifest, Parquet đã tải và `root_cause.txt` duy nhất để kiểm soát leakage.

## Tạo tác tái lập

- Script xác định: `scripts/audit/audit_rcaeval_logs_multimodal.py`.
- Kết quả máy đọc được: `results/rcaeval-subagent-e-logs-multimodal.json`.
- Chạy lại bằng:

  ```powershell
  & .\.venv\Scripts\python.exe .\scripts\audit\audit_rcaeval_logs_multimodal.py
  ```

Script chỉ duyệt các thư mục con hiện có của `raw-samples`, không gọi mạng, không tải thêm dữ liệu. Nó ghi schema, row/null count, timestamp range, SHA-256 của mỗi raw Parquet, phép kiểm timestamp/ID và bảng join. `py_compile` đã đạt trước khi chạy.

## Kết luận có phạm vi mẫu

1. Bốn `logs.parquet` đã tải đều có **đúng ba cột**: `timestamp: int64`, `container_name: large_string`, `message: large_string`. Không có cột `traceID`, `spanID`, `operationName`, `resource`, `RPC`, `DB` hay `messaging` riêng trong log Parquet. Vì vậy, không được gọi log là có join span trực tiếp chỉ vì nội dung text đôi khi chứa mã hex hay chữ “trace”.
2. Logs và metrics có thể nối bằng khóa `(epoch-second timestamp, exact container/entity string)` trong cả bốn mẫu cùng có hai modal. Đây là `DIRECT KEY JOIN` ở **bin service/container một giây** sau khi unpivot metric wide table theo rule suffix rõ ràng. Nó không nối một event log với một metric cụ thể, không nối request và không chứng minh quan hệ nhân quả.
3. Mọi cặp trace–metric và trace–log có raw modal cùng tồn tại chỉ đạt `SERVICE + TIME WINDOW`, không phải `DIRECT KEY JOIN`. Trace dùng thời điểm vi mô/mili-giây; metrics/log dùng epoch-second. Không có ID trace/span trùng trực tiếp trong hai raw log+trace samples.
4. `container_name` là định danh container quan sát được, không tự là service/operation ground truth. Có các chuỗi khớp chính xác, nhưng cũng có mismatch thật: trong `re2ob_productcatalogservice_loss_1`, `frontend` ở log/metric khác `frontendservice` ở trace. Audit không tự normalize mismatch này.
5. Mẫu `re2ss_orders_loss_2` có 2.850 message theo hình `[text, 32-hex, 16-hex, boolean]`, một **candidate** trace/span context dạng text. Nhưng raw sample không có `traces.parquet`, nên không thể kiểm exact ID và không tạo được join; status vẫn là `NOT JOINABLE` cho log–trace.

## Định nghĩa phân loại join

| Nhãn | Điều kiện áp dụng trong audit này |
|---|---|
| `DIRECT KEY JOIN` | Có cùng raw epoch-second timestamp và định danh thực thể khớp string chính xác (metric column được chuyển wide→long bằng rule suffix được ghi trong script). |
| `SERVICE + TIME WINDOW` | Có tập tên thực thể/service khớp string và cùng epoch-second sau phép `floor(startTimeMillis / 1000)`, nhưng không có khóa request/span/event trực tiếp. |
| `TIME WINDOW ONLY` | Chỉ có overlap theo thời gian; không thấy định danh thực thể khớp. Không có cặp nào trong sáu mẫu rơi đúng nhãn này. |
| `NOT JOINABLE` | Thiếu ít nhất một raw artifact cần thiết, hoặc không có bằng chứng khóa hợp lệ. |

“Cùng giây” chỉ là cửa sổ gom nhóm. Nó không được diễn giải thành log đó do span đó tạo ra, trace edge đó là causal propagation, hay metric đó thuộc một request cụ thể.

## Schema và nội dung log thực tế

| Case | Raw log rows | Containers khác nhau | Timestamp raw (UTC) | Null/empty message | Dấu hiệu cấu trúc đã kiểm | Cảnh báo ID/exception |
|---|---:|---:|---|---:|---|---|
| `re2ob_productcatalogservice_loss_1` | 117.601 | 11 | 2024-01-15 18:08:30–18:32:28 | 0 | 28.031 rows có `key=value`; 0 JSON hợp lệ | 55 rows có `ERROR`/exception; 0 candidate 32/16-hex; 0 exact ID match với trace |
| `re2ss_orders_loss_2` | 87.652 | 10 | 2024-01-20 10:24:19–10:48:18 | 1.664 | 1.471 message là JSON hợp lệ; 14.448 có HTTP-style; 24.468 có `key=value` | 5.717 rows chứa error/exception; 2.850 bracket candidates nhưng không có trace file để đối chiếu |
| `re3ss_carts_f1_1` | 84.665 | 13 | 2024-11-22 02:28:03–02:52:03 | 1 | 1.581 JSON hợp lệ; 14.644 HTTP-style; 25.967 `key=value` | 5.599 rows chứa error/exception; 11.565 16-hex substrings, nhưng không có 32-hex context và không có trace file |
| `re3tt_ts-route-service_f2_1` | 74.449 | 48 | 2024-12-07 20:01:35–20:31:34 | 0 | 758 JSON hợp lệ; 2.603 HTTP-style; 19.283 `key=value` | 111 rows chứa error/exception; 0 candidate 32/16-hex; 0 exact ID match với trace |

Các count “error/exception”, HTTP-style, JSON hay `key=value` là pattern trong `message` text. Chúng không phải anomaly labels, operation ground truth hay một schema log thống nhất giữa hệ thống.

`re3tt` có 54 lần từ “trace” trong message. Kiểm tra trực tiếp cho thấy đó xuất hiện trong text stack trace Java, không phải trường trace ID. Điều này là ví dụ cụ thể vì sao keyword search không thể thay thế khóa join.

`re2ss` có pattern bốn phần nêu trên với 1.429 giá trị 32-hex và 1.429 giá trị 16-hex duy nhất. Raw evidence chỉ đủ để ghi nó là **candidate embedded context**; semantic “trace/span” và khả năng join vẫn `UNKNOWN` khi sample không có trace artifact đối chiếu.

## Timestamp và trace fields thực tế

Ba `traces.parquet` có cùng raw schema 11 cột:

`time`, `traceID`, `spanID`, `serviceName`, `methodName`, `operationName`, `parentSpanID`, `startTimeMillis`, `startTime`, `duration`, `statusCode`.

Trong từng row của ba samples, phép kiểm `startTime // 1000 == startTimeMillis` đạt toàn bộ: 254.889/254.889 (`re2ob`), 1.143.435/1.143.435 (`re2tt`) và 183.623/183.623 (`re3tt`). Đây là bằng chứng raw nhất quán rằng `startTime` có độ phân giải micro-giây và `startTimeMillis` là mili-giây. Cột `time` dạng `HH:MM` chỉ có 25–31 giá trị khác nhau mỗi sample và không được dùng làm join key.

Metrics có cột `time: int64` ở epoch-second; entity được suy ra một cách xác định từ tên metric wide-column theo rule:

```text
^(entity)_(cpu|mem|diskio|socket|workload|error)$
^(entity)_latency(-50|-90)?$
```

Rule này chỉ phục vụ unpivot/factual join audit; nó không thêm topology, operation hay causal edge.

## Bảng join cho từng sample

| Case | Logs ↔ metrics | Metrics ↔ traces | Logs ↔ traces | Bằng chứng raw quyết định |
|---|---|---|---|---|
| `re1ob_productcatalogservice_cpu_3` | `NOT JOINABLE` | `NOT JOINABLE` | `NOT JOINABLE` | Chỉ có `metrics.parquet`; 63 row, 59 cột. |
| `re2ob_productcatalogservice_loss_1` | `DIRECT KEY JOIN` | `SERVICE + TIME WINDOW` | `SERVICE + TIME WINDOW` | L–M: 117.601/117.601 log rows, 1.356/1.356 log seconds và 11 tên container khớp exact entity. M–T: 1.413/1.441 metric seconds, 6 entity/service exact. L–T: 1.350/1.356 log seconds, 117.578/117.601 rows, 6 tên exact; 0 traceID và 0 spanID match. |
| `re2ss_orders_loss_2` | `DIRECT KEY JOIN` | `NOT JOINABLE` | `NOT JOINABLE` | L–M: 87.652/87.652 log rows, 1.434/1.434 seconds và 10 tên exact. Không có `traces.parquet`. |
| `re2tt_ts-auth-service_cpu_1` | `NOT JOINABLE` | `SERVICE + TIME WINDOW` | `NOT JOINABLE` | Không có log. M–T: 1.425/1.441 metric seconds và 27 entity/service exact; không có trace key trong metric rows. |
| `re3ss_carts_f1_1` | `DIRECT KEY JOIN` | `NOT JOINABLE` | `NOT JOINABLE` | L–M: 84.665/84.665 log rows, 1.441/1.441 seconds và 13 tên exact. Không có `traces.parquet`. |
| `re3tt_ts-route-service_f2_1` | `DIRECT KEY JOIN` | `SERVICE + TIME WINDOW` | `SERVICE + TIME WINDOW` | L–M: 74.449/74.449 rows, 1.419/1.419 seconds và 48 tên exact. M–T: 1.355/1.801 seconds, 27 entity/service exact. L–T: 1.194/1.419 log seconds, 68.608/74.449 rows, 23 tên exact; 0 traceID/spanID match. |

## Những gì hiện có thể và không thể nói

### Có bằng chứng sample-level

- Có thể gom log và metric theo `(timestamp second, exact container/entity name)` cho bốn samples cùng có hai modal.
- Có thể gom trace với log/metric theo `(same second, exact service/entity name)` ở các samples có overlap được báo trong bảng.
- Trace có `traceID`, `spanID`, `parentSpanID`, `serviceName`, `operationName` và thời gian chi tiết; log Parquet không có những cột đó.
- Nhiều log message có cấu trúc nội tại khác nhau theo system; không có một parser chung được chứng minh bởi các raw fields này.

### Chưa được hỗ trợ / không được suy diễn

- **Direct log–span join:** `NOT SUPPORTED` ở hai samples có cả log và trace: zero exact ID match, zero explicit trace/span column.
- **Operation-level log join:** `NOT SUPPORTED`. Trace có `operationName`/`methodName`; log không có trường operation chuẩn. HTTP-looking message text không đủ thành operation ground truth.
- **Resource/DB/messaging semantic join từ log:** `NOT SUPPORTED`. Một số `container_name` trông như datastore/component nhưng raw schema không cung cấp type/relationship; không được tự gán vai trò kiến trúc.
- **Causal propagation:** `NOT SUPPORTED`. Sự trùng service+giây chỉ cho phép aggregate time-window, không chứng minh cạnh trace là đường lan truyền nhân quả.
- **Dataset-wide modality prevalence hay joinability:** `UNKNOWN`; sáu samples không thể đại diện toàn bộ suite.

## Leakage và kiểm soát đầu vào

- `re3ss_carts_f1_1/root_cause.txt` tồn tại, 288 bytes, một dòng không rỗng. Nội dung không được trích hay dùng làm evidence mô hình trong audit này. Phân loại: `FORBIDDEN MODEL INPUT`; chỉ dành cho evaluation/provenance theo kiểm soát của Ground-truth Auditor.
- Case/directory identifiers có token dễ đọc về fault/target. Chúng là provenance, không được đưa vào tokenizer, feature, column, graph node attribute hay đường dẫn model input.
- `inject_time.txt` không được dùng trong audit log/multimodal này để chọn window hay xây feature. Việc dùng nó làm model input phải bị chặn bởi audit leakage riêng.

## Điểm cần cross-review với các reviewer khác

| Câu hỏi | Kết quả độc lập của Subagent E | Evidence cần đối chiếu |
|---|---|---|
| B/C có thể nói log–trace là direct join không? | Không: tối đa `SERVICE + TIME WINDOW` cho `re2ob`/`re3tt`; exact ID matches = 0. | Schema logs, regex ID scan, counts trong JSON. |
| D có thể gọi metric–trace là direct không? | Không: metric row không có trace/span key; chỉ service + second-bin. | `metrics_to_traces` JSON, raw `time` và trace `startTimeMillis`. |
| Có thể normalize `frontend` ↔ `frontendservice` tự động không? | Không ở Task B; đây là mismatch raw, cần explicit rule được đánh giá riêng. | Sets of raw strings trong `re2ob`. |
| Có phải Sock Shop có trace join vì message có 32/16-hex? | Chưa: nó chỉ là candidate embedded context; raw sample không có `traces.parquet` để verify. | 2.850 bracket-context rows; absent artifact. |

## Mở và giới hạn

1. Không biết tại sample scope liệu trace absence của Sock Shop là thuộc tính toàn suite hay chỉ case selection; không suy rộng.
2. Không có raw proof rằng JSON trong message có schema ổn định hoặc chứa correlation IDs hữu ích; cần parser audit riêng trước khi dùng structured payload.
3. Cần Main Agent so sánh kết luận này với Trace/Graph/Metric/Ground-truth audits trong disagreement matrix. Nếu có ai kết luận direct log-span or direct metric-span, raw script này phải là điểm quay lại kiểm tra.
4. Không yêu cầu tải thêm case từ findings của E: các kết luận trên được giới hạn đúng sáu case. Bất kỳ claim prevalence rộng hơn phải đi qua Task B2 đã được phê duyệt.
