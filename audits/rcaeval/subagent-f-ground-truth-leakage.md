# Subagent F — Ground-truth và leakage audit

**Trạng thái:** `DRAFT — PRE-SAMPLE`  
**Phạm vi bằng chứng:** `DATASET-WIDE METADATA FACT` đối với `cases.parquet`; chưa tải hoặc đọc bất kỳ `metrics.parquet`, `logs.parquet`, `traces.parquet`, `inject_time.txt` hay `root_cause.txt` nào. Không có kết luận nào dưới đây là kết luận về schema telemetry thô.

## 1. Nguồn và khả năng tái lập

| Mục | Giá trị đã kiểm chứng |
|---|---|
| Nguồn chính thức | [Hugging Face dataset `phamquiluan/RCAEval`](https://huggingface.co/datasets/phamquiluan/RCAEval) |
| Revision | `afeacb11bcc94dadfd1c8f483ee4377b2b8b614e` |
| Metadata đã đọc | `D:\Project\flash-ticket-rca-research\datasets\rcaeval\metadata\cases.parquet` |
| SHA-256 metadata | `c49a288920dbba2e8e724679a14636d5c7eb2b45426bba14007ef79a6c0ab1bb` |
| Provenance cục bộ | `datasets\rcaeval\metadata\metadata-provenance.json` |
| Tài liệu chính thức đọc để diễn giải cột | [README tại đúng revision](https://huggingface.co/datasets/phamquiluan/RCAEval/resolve/afeacb11bcc94dadfd1c8f483ee4377b2b8b614e/README.md?download=true) |

Script xác định được dùng:

```text
D:\Project\flash-ticket-rca-research\.venv\Scripts\python.exe \
  D:\Project\flash-ticket-rca-research\scripts\audit\audit_ground_truth.py
```

Script chỉ đọc `cases.parquet` và sinh [machine-readable evidence](D:/Project/flash-ticket-rca-research/audits/rcaeval/subagent-f-ground-truth-leakage-data.json:1). Nó kiểm tra số hàng/cột, null, trùng case, regex tên thư mục, các quan hệ `inject_time` với cửa sổ, phân phối label, và danh sách case bất thường. Nó không liệt kê hoặc tải telemetry thô.

Các count quan trọng còn được cross-check độc lập bằng stdlib + PyArrow, không import pandas: [PyArrow cross-check](D:/Project/flash-ticket-rca-research/audits/rcaeval/subagent-f-ground-truth-pyarrow-crosscheck.json:1). Hai implementation đồng ý về 735 hàng, 735/735 case-name matches, 733/735 quan hệ injection-window, và 8 case có `root_cause.txt`.

## 2. Những gì metadata thực sự có và không có

**FACT — dataset-wide metadata:** bảng có 735 hàng, 22 cột, `case` duy nhất ở cả 735 hàng, và các cột đều không null. Có 18 giá trị `root_cause_service`, 11 mã `fault`, 9 dataset con, 3 suite và 3 system.

Các cột nguyên văn là:

```text
case, dataset, suite, system, system_name, root_cause_service, fault,
fault_description, repetition, inject_time, n_metrics, n_timesteps,
time_start, time_end, duration_minutes, normal_timesteps, faulty_timesteps,
has_logs, n_logs, has_traces, n_traces, has_root_cause_file
```

**FACT — metadata không có** cột `operation_label`, `resource_label`, `affected_node_label`, `propagation_path_label`, hay một trường injection target tách biệt với `root_cause_service`. Đây chỉ là nhận định về index metadata; schema telemetry có operation/resource hay không vẫn thuộc audit B/C sau khi có raw samples.

README chính thức định nghĩa `root_cause_service` là ground-truth root cause; `fault`/`fault_description` là nhãn injection; `inject_time` là thời điểm injection; và `has_root_cause_file` chỉ sự hiện diện của `root_cause.txt`. README cũng xác nhận tên thư mục có dạng `{suite}{system}_{service}_{fault}_{repetition}` và mã hoá service root cause cùng fault.

## 3. Phân loại tất cả metadata field cho thực nghiệm blind RCA

Quy ước: `EVALUATION ONLY` được dùng để chấm điểm hoặc phân tầng kết quả, không được encode làm feature. `FORBIDDEN MODEL INPUT` là trường không được vào pipeline, kể cả gián tiếp qua đường dẫn, manifest hoặc full-case aggregate. `MODEL INPUT CANDIDATE` chỉ là ứng viên có điều kiện, chưa phải quyết định thiết kế.

| Field | Phân loại | Bằng chứng và giới hạn sử dụng |
|---|---|---|
| `case` | `FORBIDDEN MODEL INPUT` | Regex đã kiểm chứng tái tạo chính xác suite, system, root-cause service, fault và repetition cho 735/735 case. Không truyền tên thư mục/đường dẫn vào loader, tokenizer, cache key hay feature. |
| `dataset` | `PROVENANCE ONLY` | Nhãn benchmark con; dùng để filter, báo cáo và split, không phải telemetry runtime. |
| `suite` | `PROVENANCE ONLY` | RE1/RE2/RE3 mô tả loại benchmark; dùng để stratify, không làm feature. |
| `system` | `PROVENANCE ONLY` | Mã `ob`/`ss`/`tt`; giữ để audit schema và system-disjoint split. |
| `system_name` | `PROVENANCE ONLY` | Tên hiển thị của `system`, không phải quan sát runtime. |
| `root_cause_service` | `EVALUATION ONLY` | Ground-truth target chính thức, 18 giá trị/735 hàng. Dùng cho hit@k/MRR/PR của RCA service-level; cấm làm feature hay dùng để dựng node label trước khi dự đoán. |
| `fault` | `EVALUATION ONLY` | Nhãn injection có 11 giá trị; chỉ stratify kết quả. Không có bằng chứng nó là tín hiệu quan sát tại runtime. |
| `fault_description` | `EVALUATION ONLY` | Bản diễn giải bằng chữ của `fault`; tuyệt đối không làm text feature. |
| `repetition` | `PROVENANCE ONLY` | Số repeat của cùng nhóm dataset–root service–fault; dùng group split, không làm feature. |
| `inject_time` | `FORBIDDEN MODEL INPUT` | Oracle thời điểm tiêm lỗi. Chỉ có thể phục vụ cắt cửa sổ đánh giá sau khi score đã sinh; không dùng để tạo feature, training label tại thời điểm runtime, chọn metric window, hay calibration. |
| `n_metrics` | `PROVENANCE ONLY` | Aggregate số metric của cả case; báo cáo coverage/schema audit, không làm feature shortcut. |
| `n_timesteps` | `FORBIDDEN MODEL INPUT` | Aggregate của toàn bộ case, có look-ahead. |
| `time_start` | `PROVENANCE ONLY` | Mốc case-level phục vụ audit; khác với timestamp từng observation dùng để sắp thứ tự/căn chỉnh sau này. |
| `time_end` | `FORBIDDEN MODEL INPUT` | Mốc kết thúc toàn bộ case, có look-ahead. |
| `duration_minutes` | `FORBIDDEN MODEL INPUT` | Aggregate toàn-case, suy ra từ schedule/khoảng thời gian đã hoàn tất. |
| `normal_timesteps` | `FORBIDDEN MODEL INPUT` | Số hàng được phân theo `inject_time`; là oracle segmentation. |
| `faulty_timesteps` | `FORBIDDEN MODEL INPUT` | Như trên; cho biết độ dài cửa sổ lỗi sau injection. |
| `has_logs` | `MODEL INPUT CANDIDATE` có điều kiện | Chỉ được dùng như availability mask nếu tính lại tại cutoff quan sát thực tế và áp cùng luật cho mọi case; metadata full-case không được dùng để suy luận root cause. |
| `n_logs` | `FORBIDDEN MODEL INPUT` | Tổng log của toàn case, bao gồm tương lai/fault period và là shortcut về kích thước case. |
| `has_traces` | `MODEL INPUT CANDIDATE` có điều kiện | Cùng điều kiện với `has_logs`; phải test system-disjoint để loại proxy của suite/system. |
| `n_traces` | `FORBIDDEN MODEL INPUT` | Tổng trace của toàn case, bao gồm tương lai/fault period. |
| `has_root_cause_file` | `FORBIDDEN MODEL INPUT` | Chỉ sự hiện diện của file chứa root-cause log line trong 8 case; mọi `root_cause.txt` phải bị loại khỏi input enumeration. |

## 4. Kết quả định lượng metadata và các đường leakage

### 4.1 Nhãn root cause và fault

**FACT — dataset-wide metadata:** phân phối fault là CPU 120, delay 120, disk 120, packet loss 120, memory 120, socket 45, F1 26, F2 13, F3 26, F4 19 và F5 6 case. Do RE3 không là lưới đều, không được suy diễn cân bằng class từ tổng 735 case.

**FACT — dataset-wide metadata:** root-cause service có 18 giá trị, không trùng chuỗi giữa ba system trong metadata. Số case mỗi target không cân bằng: nhỏ nhất `front-end` của Sock Shop có 9, lớn nhất `ts-auth-service` và `ts-route-service` của Train Ticket có 58. Vì vậy accuracy không đủ; kết quả RCA về sau phải báo cáo theo case và theo target/fault stratum, đồng thời công khai support mỗi stratum.

### 4.2 Tên thư mục là leakage trực tiếp

Query regex trong script là:

```text
^re(?P<suite_number>[123])(?P<system_code>ob|ss|tt)_(?P<service>.+)_(?P<fault>[^_]+)_(?P<repetition>[0-9]+)$
```

Nó match **735/735**, và các group `service`, `fault`, `repetition` khớp lần lượt với `root_cause_service`, `fault`, `repetition` trong metadata ở **735/735**. Đây là `CRITICAL LEAKAGE RISK`: bất kỳ mô hình nào nhận case ID, relative path, basename hoặc file-list manifest đều có thể đọc đáp án service-level trước khi nhìn telemetry.

Nhóm `(dataset, root_cause_service, fault)` có 3, 4, 5 hoặc 6 repetitions; có lần lượt 110, 6, 75 và 1 nhóm như vậy. Random row split qua các repetition **có thể** tạo evaluation leakage/correlation: cùng service và cùng fault configuration có thể xuất hiện ở train lẫn test. Yêu cầu tối thiểu là group-aware split; kiểu split cụ thể còn `OPEN` cho giai đoạn thiết kế.

### 4.3 Injection time không phải anomaly label và có hai bất thường metadata

| Kiểm tra máy | Kết quả |
|---|---:|
| `normal_timesteps + faulty_timesteps == n_timesteps` | 735/735 |
| `inject_time == time_start + normal_timesteps` | 733/735 |
| `time_start <= inject_time <= time_end` | 733/735 |

Hai case không phù hợp là:

| Case | Observed metadata | Hệ quả hiện tại |
|---|---|---|
| `re1ob_currencyservice_loss_1` | `inject_time=16933142`, nhưng range metric là `1693313863..1693314583`; `normal=0`, `faulty=721` | Không tự sửa hoặc đoán lại timestamp. `UNKNOWN` liệu index hay `inject_time.txt` thô là nguồn lệch; phải kiểm tra raw case nếu case được chọn. |
| `re1ob_productcatalogservice_cpu_3` | `inject_time=1685373255` sau `time_end=1685371799`; `normal=63`, `faulty=0` | Không có faulty timestep theo index. Không dùng case này để tuyên bố detector/RCA có hay không hiệu quả trước khi raw audit xác minh. |

`root_cause_service` là target root cause, không phải nhãn bất thường per-timestamp, không phải nhãn mọi node bị ảnh hưởng, và cũng không chứng minh service đó có một operation/resource telemetry có tên tương ứng. `inject_time` giúp benchmark phân tách normal/faulty, nhưng nó là oracle của campaign. Chính sách cấm nó làm input ở đây là mặc định cho blind RCA/detection; một giao thức được thông báo ngoài hệ thống chỉ có thể dùng alert time sau khi câu hỏi nghiên cứu và source của alert được xác định minh bạch. Vì vậy chưa thể rút metric point-level anomaly detection, operation-level RCA, resource-level RCA hoặc propagation-path accuracy chỉ từ metadata.

### 4.4 File root-cause và missing modality

**FACT — dataset-wide metadata + primary documentation:** 8 case RE3-SS có `has_root_cause_file=true`: `re3ss_carts_f1_{1,2}`, `re3ss_carts_f3_{1,2}`, `re3ss_front-end_f1_{1,2}`, `re3ss_front-end_f2_{1,2}`. README nói các file này giữ root-cause log line. Chúng là source evaluation/provenance duy nhất và phải loại khỏi model corpus.

**FACT — dataset-wide metadata:** có 1 case RE2-TT không có logs nhưng có 1,143,435 traces: `re2tt_ts-auth-service_cpu_1`. Các case có mặt modality theo suite/system là RE1: 375 metric-only; RE2-OB: 90 logs+traces; RE2-SS: 90 logs/no traces; RE2-TT: 89 logs+traces và 1 traces/no logs; RE3-OB: 30 logs+traces; RE3-SS: 30 logs/no traces; RE3-TT: 30 logs+traces. Không được silently impute modality thiếu hay gọi whole-case availability là feature có thể dùng không điều kiện.

## 5. Đề xuất độc lập cho Raw Sample Plan (chưa phải lựa chọn cuối)

Đây là đề xuất của Subagent F để kiểm tra leakage và label semantics. Nó chưa được đối chiếu với proposal của Subagent A và main agent, nên **không cho phép download chỉ từ bảng này**.

| Case | Suite/system | Fault / root target | Lý do liên quan F | Uncertainty cần kiểm tra bằng raw evidence |
|---|---|---|---|---|
| `re1ob_productcatalogservice_cpu_3` | RE1 / OB | CPU / `productcatalogservice` | Metric-only và metadata nói 0 faulty timestep | `inject_time.txt` và metric time range có đồng ý với index không; case có hợp lệ cho bất kỳ evaluation nào không. |
| `re2ob_checkoutservice_socket_1` | RE2 / OB | socket exhaustion / `checkoutservice` | Case tri-modal với fault không phải năm loại RE1 | Loader có giữ path/case name hay label metadata trong context không. |
| `re2ss_orders_loss_2` | RE2 / SS | packet loss / `orders` | Logs nhưng không traces; network-fault coverage | Missing trace là không tồn tại thật, schema difference hay artifact tải. |
| `re2tt_ts-auth-service_cpu_1` | RE2 / TT | CPU / `ts-auth-service` | Case duy nhất RE2-TT logs thiếu nhưng traces rất nhiều | `has_logs=false` khớp raw file absence/emptiness; cross-modal code có xử lý availability đúng không. |
| `re3ss_carts_f1_1` | RE3 / SS | F1 / `carts` | Có `root_cause.txt` theo metadata | File root-cause phải được loại triệt để; nội dung không được đi vào log corpus/model. |
| `re3tt_ts-route-service_f2_1` | RE3 / TT | F2 / `ts-route-service` | Tri-modal code-level và root target khác | Cách root cause service map (hoặc không map) vào service/operation/resource observables. |

## 6. Kết luận, rủi ro và câu hỏi mở

1. **VERIFIED:** metadata cung cấp service-level root-cause ground truth và fault/injection metadata, nhưng không cung cấp anomaly labels, affected-node labels, operation labels, resource labels hay propagation labels.
2. **VERIFIED:** case/directory name là đường leakage trực tiếp cho root-cause service, fault và repetition ở 735/735 case.
3. **VERIFIED:** `inject_time`, `normal_timesteps`, `faulty_timesteps`, whole-case counts và `root_cause.txt` là các input nguy hiểm; dùng chúng làm input sẽ làm sai câu hỏi nghiên cứu blind RCA/detection.
4. **PARTIALLY VERIFIED:** log/trace availability được metadata mô tả, nhưng tính chính xác của schema và content chỉ được xác minh sau selective raw retrieval.
5. **UNRESOLVED:** hai injection-window anomaly nêu trên; source of truth giữa index và raw `inject_time.txt`; sự tương ứng root-cause service với node thực quan sát; operation/resource/propagation targets; và mọi metric anomaly detection không dựa oracle.

Không có phương pháp, dataset hay research question nào được chốt bởi audit này.
