# Subagent A — Kiểm toán metadata chính thức của RCAEval

**Trạng thái:** hoàn thành độc lập · **Phạm vi bằng chứng:** chỉ metadata · **Ngày:** 2026-09-20  
**Phân loại công việc:** `DATASET-WIDE METADATA FACT` khi kết luận được suy ra trực tiếp từ toàn bộ 735 dòng của `cases.parquet` tại revision đã khóa. Không có telemetry thô nào được mở, liệt kê hoặc tải bởi subagent này.

## 1. Đầu vào đã kiểm toán và khả năng tái lập

| Mục | Giá trị đã kiểm chứng |
|---|---|
| Tệp đọc | `D:\Project\flash-ticket-rca-research\datasets\rcaeval\metadata\cases.parquet` |
| Số dòng | 735 |
| Kích thước | 29,500 bytes |
| SHA-256 | `c49a288920dbba2e8e724679a14636d5c7eb2b45426bba14007ef79a6c0ab1bb` |
| Nguồn ghi trong provenance | Hugging Face dataset `phamquiluan/RCAEval` — `https://huggingface.co/datasets/phamquiluan/RCAEval` |
| Revision khóa | `afeacb11bcc94dadfd1c8f483ee4377b2b8b614e` |
| Thời điểm metadata được tải theo provenance | `2026-09-20T02:10:08.349561+00:00` |
| Interpreter | `D:\Project\flash-ticket-rca-research\.venv\Scripts\python.exe`, Python 3.12.10 |
| Thư viện dùng | pandas 3.0.6; pyarrow 25.0.1 |

**Lưu ý về phạm vi:** `metadata-provenance.json` và cache Hugging Face cùng ghi revision/hash khớp với tệp cục bộ. Đây xác minh provenance của *metadata snapshot*, không xác minh nội dung của bất kỳ parquet telemetry nào.

### Lệnh và script đã dùng

Script tái lập: [`D:\Project\flash-ticket-rca-research\scripts\audit\audit_rcaeval_metadata.py`](../../scripts/audit/audit_rcaeval_metadata.py). Script chỉ đọc `cases.parquet` và `metadata-provenance.json`; không có đường dẫn tới `raw-samples`.

```powershell
& 'D:\Project\flash-ticket-rca-research\.venv\Scripts\python.exe' `
  'D:\Project\flash-ticket-rca-research\scripts\audit\audit_rcaeval_metadata.py'

& 'D:\Project\flash-ticket-rca-research\.venv\Scripts\python.exe' `
  'D:\Project\flash-ticket-rca-research\scripts\audit\audit_rcaeval_metadata.py' --json

Get-FileHash -LiteralPath `
  'D:\Project\flash-ticket-rca-research\datasets\rcaeval\metadata\cases.parquet' `
  -Algorithm SHA256

& 'D:\Project\flash-ticket-rca-research\.venv\Scripts\python.exe' -c `
  "import pyarrow.parquet as pq; print(pq.read_schema(r'D:\Project\flash-ticket-rca-research\datasets\rcaeval\metadata\cases.parquet'))"
```

Các truy vấn đếm, kiểm tra null/duplicate, nhất quán thời gian và cờ modality nằm nguyên văn trong script trên. Chạy lại script với `--json` tạo output cấu trúc để đối chiếu từng số bên dưới.

## 2. Schema thực tế của `cases.parquet`

**`DATASET-WIDE METADATA FACT`.** Schema parquet có 22 cột; không có cột `root_cause_indicator`, `operation`, `resource`, `affected_node`, hay `propagation_path`.

| Nhóm | Cột metadata thực tế | Kiểu parquet |
|---|---|---|
| Định danh/phân tầng | `case`, `dataset`, `suite`, `system`, `system_name` | `large_string` |
| Nhãn gốc/fault | `root_cause_service`, `fault`, `fault_description`, `repetition` | `large_string`, `large_string`, `large_string`, `int64` |
| Thời gian | `inject_time`, `time_start`, `time_end`, `duration_minutes`, `n_timesteps`, `normal_timesteps`, `faulty_timesteps` | `int64` trừ `duration_minutes: double` |
| Metrics | `n_metrics` | `int64` |
| Logs | `has_logs`, `n_logs` | `bool`, `int64` |
| Traces | `has_traces`, `n_traces` | `bool`, `int64` |
| Tệp root-cause | `has_root_cause_file` | `bool` |

Hệ quả có giới hạn: metadata cho nhãn ở mức `root_cause_service`, nhưng **không cho một `root_cause_indicator` distribution**. Việc có hay không có nhãn operation/resource/affected-node trong *tệp thô* là `UNKNOWN`, cần Subagent F kiểm tra trực tiếp sau khi chọn mẫu.

## 3. Quy mô suite, dataset và hệ thống

**`DATASET-WIDE METADATA FACT`.** Chín mã `dataset` tạo thành đủ ma trận 3 suite × 3 hệ thống; mỗi mã dataset ánh xạ duy nhất tới một `suite` và một `system` trong metadata.

| Dataset | Suite | System | Tên hệ thống | Số case |
|---|---|---|---|---:|
| RE1-OB | RE1 | ob | Online Boutique | 125 |
| RE1-SS | RE1 | ss | Sock Shop | 125 |
| RE1-TT | RE1 | tt | Train Ticket | 125 |
| RE2-OB | RE2 | ob | Online Boutique | 90 |
| RE2-SS | RE2 | ss | Sock Shop | 90 |
| RE2-TT | RE2 | tt | Train Ticket | 90 |
| RE3-OB | RE3 | ob | Online Boutique | 30 |
| RE3-SS | RE3 | ss | Sock Shop | 30 |
| RE3-TT | RE3 | tt | Train Ticket | 30 |
| **Tổng** |  |  |  | **735** |

| Phân phối | Số case |
|---|---:|
| RE1 | 375 |
| RE2 | 270 |
| RE3 | 90 |
| Online Boutique (`ob`) | 245 |
| Sock Shop (`ss`) | 245 |
| Train Ticket (`tt`) | 245 |

Kiểm tra bổ sung: `system → system_name` không có ánh xạ mâu thuẫn; `fault → fault_description` không có ánh xạ mâu thuẫn; numeric suffix của `case` khớp `repetition` ở 735/735 dòng. Đây là kiểm tra tự nhất quán của metadata, không chứng minh semantics của tên case.

## 4. Khả dụng modality được metadata khai báo

**`DATASET-WIDE METADATA FACT` (chỉ là metadata declaration).** `n_metrics > 0` ở 735/735 dòng (min 49, max 376). Không có cờ `has_metrics`; do đó điều này **không** kiểm chứng rằng tệp metrics thô tồn tại, đọc được, hay có schema thống nhất.

| Tổ hợp cờ metadata | Số case | Khoảng `n_metrics` | Khoảng `n_logs` | Khoảng `n_traces` |
|---|---:|---:|---:|---:|
| Không logs, không traces, không root-cause file | 375 | 49–238 | 0 | 0 |
| Có logs, có traces, không root-cause file | 239 | 68–376 | 17,025–314,211 | 36,374–1,535,674 |
| Có logs, không traces, không root-cause file | 112 | 74–107 | 41,777–92,962 | 0 |
| Có logs, không traces, có root-cause file | 8 | 80–81 | 84,162–86,678 | 0 |
| Không logs, có traces, không root-cause file | 1 | 369 | 0 | 1,143,435 |

Tổng theo cờ: `has_logs=True` 359, `has_logs=False` 376; `has_traces=True` 240, `has_traces=False` 495; `has_root_cause_file=True` 8, `False` 727.

| Dataset | Modality được khai báo | Số case | Diễn giải có giới hạn |
|---|---|---:|---|
| RE1-OB / RE1-SS / RE1-TT | M | 125 mỗi dataset | Metadata không khai logs/traces |
| RE2-OB | M + L + T | 90 | Case tri-modal theo cờ metadata |
| RE2-SS | M + L | 90 | Không khai trace |
| RE2-TT | M + L + T | 89 | Case tri-modal theo cờ metadata |
| RE2-TT | M + T | 1 | `re2tt_ts-auth-service_cpu_1`, không khai log |
| RE3-OB | M + L + T | 30 | Case tri-modal theo cờ metadata |
| RE3-SS | M + L | 30 | Không khai trace; 8 case có cờ root-cause file |
| RE3-TT | M + L + T | 30 | Case tri-modal theo cờ metadata |

**`UNKNOWN`:** join key thực tế, chất lượng timestamps, schema logs/traces/metrics, và việc `n_logs`/`n_traces` có đúng bằng số record thô. Các câu hỏi này phải được đánh giá từ parquet thô; không được suy ra từ bảng trên.

## 5. Phân phối nhãn `root_cause_service`

**`DATASET-WIDE METADATA FACT`.** Có 18 giá trị `root_cause_service`, không null và không rỗng. Các số sau là phân phối của **nhãn metadata**; chúng không chứng minh injection target, root-cause operation hay node quan sát được.

| System | `root_cause_service` | Case |
|---|---|---:|
| ob | currencyservice | 46 |
| ob | checkoutservice | 43 |
| ob | productcatalogservice | 43 |
| ob | adservice | 34 |
| ob | emailservice | 33 |
| ob | cartservice | 28 |
| ob | recommendationservice | 18 |
| ss | carts | 55 |
| ss | orders | 52 |
| ss | catalogue | 43 |
| ss | payment | 43 |
| ss | user | 43 |
| ss | front-end | 9 |
| tt | ts-auth-service | 58 |
| tt | ts-route-service | 58 |
| tt | ts-order-service | 43 |
| tt | ts-train-service | 43 |
| tt | ts-travel-service | 43 |

`root_cause_indicator` không nằm trong schema, vì vậy mọi phát biểu về phân phối indicator là `UNKNOWN` tại Task B metadata stage.

## 6. Phân phối `fault`

**`DATASET-WIDE METADATA FACT`.** Có 11 mã `fault`; mỗi mã ánh xạ tới đúng một `fault_description` trong metadata snapshot.

| Fault | `fault_description` nguyên văn | Case |
|---|---|---:|
| cpu | CPU stress | 120 |
| delay | network delay | 120 |
| disk | disk I/O stress | 120 |
| loss | network packet loss | 120 |
| mem | memory stress | 120 |
| socket | socket exhaustion | 45 |
| f1 | code-level fault F1 | 26 |
| f3 | code-level fault F3 | 26 |
| f4 | code-level fault F4 | 19 |
| f2 | code-level fault F2 | 13 |
| f5 | code-level fault F5 | 6 |

Theo chính chuỗi mô tả metadata, `delay`/`loss` là network-labeled; `cpu`/`mem`/`disk`/`socket` là resource-or-runtime-labeled; `f1`–`f5` là code-level-labeled. **`UNKNOWN`:** cơ chế injection, entity bị tác động thật, và khả năng quan sát trong telemetry. Không dùng các nhãn này để dựng cạnh đồ thị hoặc làm input mô hình trước kiểm toán raw data.

## 7. Kiểm tra chất lượng và nhất quán metadata

### 7.1 Các kiểm tra đạt

**`DATASET-WIDE METADATA FACT`.** Các cột backing từng kiểm tra được nêu trong bảng.

| Kiểm tra | Kết quả | Cột backing |
|---|---:|---|
| Case ID trùng | 0 dòng trùng | `case` |
| Toàn bộ dòng trùng | 0 dòng trùng | tất cả 22 cột |
| Null ở mọi cột | 0 | tất cả 22 cột |
| Chuỗi rỗng/blank trong 8 cột chuỗi bắt buộc | 0 | `case`, `dataset`, `suite`, `system`, `system_name`, `root_cause_service`, `fault`, `fault_description` |
| Giá trị âm trong 11 cột số | 0 | `repetition`, thời gian, các count và duration |
| `has_logs=True` nhưng `n_logs=0` | 0 | `has_logs`, `n_logs` |
| `has_logs=False` nhưng `n_logs!=0` | 0 | `has_logs`, `n_logs` |
| `has_traces=True` nhưng `n_traces=0` | 0 | `has_traces`, `n_traces` |
| `has_traces=False` nhưng `n_traces!=0` | 0 | `has_traces`, `n_traces` |
| `n_metrics=0` | 0 | `n_metrics` |
| `time_end <= time_start` | 0 | `time_start`, `time_end` |
| `n_timesteps != time_end - time_start + 1` | 0 | `n_timesteps`, `time_start`, `time_end` |
| `normal_timesteps + faulty_timesteps != n_timesteps` | 0 | `normal_timesteps`, `faulty_timesteps`, `n_timesteps` |
| `duration_minutes` khớp elapsed minutes sau làm tròn 1 chữ số thập phân | 735/735 | `duration_minutes`, `time_start`, `time_end` |

Sáu dòng không khớp bằng số thực tuyệt đối với `(time_end-time_start)/60`, nhưng cả 735/735 dòng khớp sau làm tròn một chữ số thập phân. Do đó năm dòng chỉ có khác biệt rounding được phân loại là **không phải lỗi đã chứng minh**.

### 7.2 Hai bản ghi có timestamp injection không nằm trong cửa sổ

**`DATASET-WIDE METADATA FACT` về việc vi phạm bất đẳng thức.** Không suy đoán nguyên nhân chỉnh sửa dữ liệu nếu chưa có raw data/provenance upstream.

| Case | `inject_time` | `time_start` | `time_end` | `normal_timesteps` | `faulty_timesteps` | Nhận định giới hạn |
|---|---:|---:|---:|---:|---:|---|
| `re1ob_currencyservice_loss_1` | 16,933,142 | 1,693,313,863 | 1,693,314,583 | 0 | 721 | Injection time nằm trước window rất xa; nhãn normal/fault không thể được tái suy ra từ `inject_time` theo metadata này. |
| `re1ob_productcatalogservice_cpu_3` | 1,685,373,255 | 1,685,371,737 | 1,685,371,799 | 63 | 0 | Injection time nằm sau window; case không có faulty timestep theo metadata. |

Hai dòng này cũng là đúng hai vi phạm của `normal_timesteps == inject_time - time_start`. Chúng là **cờ chất lượng dữ liệu nghiêm trọng cho các phân tích sử dụng `inject_time`**, không phải bằng chứng rằng raw telemetry bị lỗi.

Năm case chỉ có rounding duration (không vi phạm injection window) là:

`re1ob_checkoutservice_cpu_4`, `re1ss_catalogue_disk_3`, `re1tt_ts-order-service_mem_3`, `re2ob_checkoutservice_cpu_2`, `re2ob_checkoutservice_mem_2`.

## 8. Những điều metadata không cho phép kết luận

| Câu hỏi | Trạng thái | Lý do |
|---|---|---|
| Một `root_cause_service` có trùng injection target thật không? | `UNKNOWN` | Chỉ có nhãn metadata; chưa kiểm tra fault injection/raw artifact. |
| Có root-cause nhãn ở mức operation, metric, resource, span hay affected node không? | `UNKNOWN` | Schema metadata không có các cột này; raw files chưa được mở. |
| Có thể nối log–trace–metric bằng ID hay timestamp chính xác không? | `UNKNOWN` | Count/cờ modality không thể chứng minh join schema. |
| `has_root_cause_file=True` chứa gì và có leakage không? | `UNKNOWN` | Chỉ có boolean; 8 file chưa được truy cập. |
| Các cạnh trace là dependency hay causal propagation không? | `UNKNOWN` | Metadata không chứa edge/runtime relation. |
| Có thể dùng `inject_time` làm model input không? | `UNKNOWN` cho chính sách; **có rủi ro đã xác minh** | Đây là metadata của quá trình tạo fault, và có hai giá trị không nhất quán với window. Subagent F phải phân loại leakage. |

## 9. Đề xuất độc lập cho kế hoạch raw sample ban đầu — không phải quyết định

Các case dưới đây là **đề xuất riêng của Subagent A**, chỉ dựa trên metadata sau khi hoàn tất toàn bộ 735 dòng. Chúng chưa được tải, chưa được chọn chính thức và không thay thế đề xuất độc lập của Subagent F và Main Agent.

| Case đề xuất | Suite / system | Fault metadata | Nhãn root target | Modality metadata | Lý do và bất định cần kiểm |
|---|---|---|---|---|---|
| `re1ob_adservice_cpu_1` | RE1 / Online Boutique | `cpu` — CPU stress | `adservice` | M (49 metrics; 0 logs; 0 traces) | Đại diện metric-only, resource-labeled; kiểm giới hạn khi không có L/T. |
| `re2ob_productcatalogservice_loss_1` | RE2 / Online Boutique | `loss` — network packet loss | `productcatalogservice` | M+L+T (72; 117,601; 254,889) | Tri-modal, network-labeled; một phía của so sánh trace schema cross-system. |
| `re2tt_ts-order-service_disk_2` | RE2 / Train Ticket | `disk` — disk I/O stress | `ts-order-service` | M+L+T (340; 58,890; 125,465) | Tri-modal, resource-labeled, volume trace tương đối thấp; phía thứ hai của so sánh cross-system. |
| `re2tt_ts-auth-service_cpu_1` | RE2 / Train Ticket | `cpu` — CPU stress | `ts-auth-service` | M+T (369; 0; 1,143,435) | Case trace-only duy nhất theo metadata; kiểm missing log và graph construction khi thiếu modality. |
| `re3ss_carts_f1_1` | RE3 / Sock Shop | `f1` — code-level fault F1 | `carts` | M+L (80; 84,665; 0), root-cause-file=True | Kiểm logs-only, khác system/schema và nội dung/risks của cờ root-cause file. |
| `re3ob_adservice_f5_1` | RE3 / Online Boutique | `f5` — code-level fault F5 | `adservice` | M+L+T (69; 69,134; 162,900) | Tri-modal code-level fault hiếm (`f5` chỉ có 6 case metadata), kiểm khác suite/fault family. |

Phạm vi bao phủ đề xuất: năm mã fault (`cpu`, `loss`, `disk`, `f1`, `f5`), ba hệ thống, metric-only/logs-only/trace-only/tri-modal, và ít nhất một so sánh trace giữa Online Boutique–Train Ticket. Không có claim prevalence nào được suy ra từ sáu case đó.

`re1ob_currencyservice_loss_1` và `re1ob_productcatalogservice_cpu_3` **không** được đề xuất làm case đại diện đầu tiên vì metadata timestamp bất thường; chúng có thể trở thành mẫu kiểm toán chất lượng có mục đích sau nếu Main Agent/Subagent F thấy cần.

## 10. Handoff cho cross-review

1. Subagent B/C/D/E chỉ được dùng “has/count metadata” như danh sách case ứng viên, không được coi đó là schema hoặc topology.
2. Subagent F cần coi `root_cause_service`, `fault`, `fault_description`, `inject_time`, cờ root-cause-file và case/folder names là các trường cần leakage review; Subagent A không phân loại chúng làm input/label.
3. Subagent G cần đối chiếu SHA-256, revision và tổng 735 dòng với manifest cuối cùng; nếu raw downloader báo revision khác thì metadata snapshot này không còn đồng revision và mọi so sánh phải dừng.
4. Case có `inject_time` bất thường cần được ghi rõ trong manifest và không được dùng để sinh normal/fault split chỉ bằng công thức từ metadata.

## Kết luận A

Metadata snapshot chính thức tại revision khóa có 735 case, cấu trúc nhất quán về ID/count/cờ modality và có sự khác biệt modality mạnh theo suite–system. Tuy nhiên, metadata không đủ để chứng minh schema thô, join cross-modal, graph constructability, operation identity, ground truth detail hoặc leakage. Hai `inject_time` ngoài time window là finding dữ liệu đã xác minh, cần được mang vào red-team review.
