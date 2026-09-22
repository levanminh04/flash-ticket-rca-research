# Subagent G — Audit tính tái lập và chất lượng dữ liệu

**Trạng thái:** DRAFT — không quyết định phương pháp, dataset hay mô hình  
**Phạm vi:** chỉ metadata chính thức cases.parquet; không tải hoặc đọc telemetry thô theo case.  
**Cấp bằng chứng:** mọi số liệu về 735 case bên dưới là **DATASET-WIDE METADATA FACT** được đọc máy trực tiếp từ file Parquet đã ghim revision. Các nhận định về rủi ro là **INFERENCE**.

## Kết luận có thể dùng ngay

1. **VERIFIED — bản metadata cục bộ tái lập được.** Nó khớp byte, SHA-256, đường dẫn và 735 hàng với manifest; API chính thức của Hugging Face trả về đúng revision ghim.
2. **MAJOR — hai case có trường thời gian bất thường.** Không dùng inject_time của hai case này để tạo split/window hay làm feature cho đến khi đối chiếu raw case hoặc nguồn phát hành:

   | Case | Bằng chứng máy kiểm | Hệ quả |
   |---|---|---|
   | re1ob_currencyservice_loss_1 | inject_time=16933142 nằm trước [time_start=1693313863, time_end=1693314583]; normal_timesteps=0 | Timestamp injection không khớp cửa sổ metadata. |
   | re1ob_productcatalogservice_cpu_3 | inject_time=1685373255 nằm sau [time_start=1685371737, time_end=1685371799]; faulty_timesteps=0 | Case không có faulty timestep theo metadata, nên không phù hợp cho đánh giá detection/RCA theo cửa sổ lỗi. |

3. **MAJOR — script lấy metadata hiện tại tự chọn revision HEAD trước khi ghi manifest.** Artifact hiện có vẫn tái lập được qua revision trong manifest, nhưng chạy lại script hiện tại ở tương lai có thể lấy một revision khác. Mọi lần tải lại phải truyền/tái dùng revision afeacb11bcc94dadfd1c8f483ee4377b2b8b614e, không dùng HEAD mới.
4. **UNRESOLVED — chưa có manifest/hash cho raw samples.** Đây là trạng thái đúng ở trước bước chọn sáu case, không phải xác nhận rằng telemetry thô đầy đủ hay hợp lệ.

## Môi trường và điều kiện trước khi audit

| Kiểm tra | Kết quả |
|---|---|
| Working directory | D:/Project/flash-ticket-rca-research |
| Hệ điều hành | Windows 11, build 10.0.22631.0 |
| D:/Project | accessible |
| Research workspace | đã tồn tại |
| python --version | Python 3.9.13 — không được dùng |
| py -0p | Python 3.12 tại C:/Users/84583/AppData/Local/Programs/Python/Python312/python.exe; Python 3.9 cũng hiện diện |
| py -3.12 --version | Python 3.12.10 |
| Venv thực tế dùng | D:/Project/flash-ticket-rca-research/.venv/Scripts/python.exe, Python 3.12.10 |
| Base interpreter của venv | Python 3.12.10; include-system-site-packages = false |
| Mạng đến nguồn chính thức | VERIFIED: Hugging Face API xác nhận revision ghim và file metadata |

Không sửa, cài đặt, hay đọc repository D:/Project/flash-ticket-platform.

## Provenance và integrity

| Trường | Kết quả |
|---|---|
| Nguồn chính thức | https://huggingface.co/datasets/phamquiluan/RCAEval |
| Repository type | dataset |
| Revision ghim | afeacb11bcc94dadfd1c8f483ee4377b2b8b614e |
| File | cases.parquet |
| Bản cục bộ | D:/Project/flash-ticket-rca-research/datasets/rcaeval/metadata/cases.parquet |
| Kích thước manifest / thực tế | 29,500 / 29,500 bytes — match |
| SHA-256 manifest / thực tế | c49a288920dbba2e8e724679a14636d5c7eb2b45426bba14007ef79a6c0ab1bb — match |
| Download timestamp của manifest | 2026-09-20T02:10:08.349561+00:00 |
| API revision check | resolved_revision bằng revision ghi trong manifest |
| File metadata có ở revision đó | có |
| Số file remote do API trả về | 2,080; chỉ cases.parquet được tải cho audit này |

## Phiên bản runtime

| Thành phần | Phiên bản |
|---|---|
| Python | 3.12.10 |
| pandas | 3.0.6 |
| pyarrow | 25.0.1 |
| huggingface_hub | 1.32.0 |
| fsspec | 2026.9.0 |

Không tìm thấy file khóa dependency ở root workspace (requirements.txt, pyproject.toml, poetry.lock, Pipfile, uv.lock đều absent). Điều này không làm sai audit hiện tại vì phiên bản runtime đã được ghi, nhưng làm tái lập môi trường trong tương lai kém chắc chắn hơn.

## Kiểm tra metadata trực tiếp

| Kiểm tra | Kết quả |
|---|---|
| Hàng Parquet / pandas | 735 / 735 — match |
| Cột | 22 |
| Row group | 1 |
| Duplicate case ID | 0 |
| Duplicate full row | 0 |
| Null ở 22 cột | 0 |
| Case ID không khớp prefix suite + system | 0 |
| Case ID không khớp suffix fault + repetition | 0 |
| Empty, whitespace-only, hoặc leading/trailing whitespace ở các chuỗi kiểm tra | 0 |
| time_start >= time_end | 0 |
| normal_timesteps + faulty_timesteps != n_timesteps | 0 |
| time_end - time_start + 1 != n_timesteps | 0 |
| Non-positive metric count / negative log or trace count | 0 |
| has_logs != (n_logs > 0) | 0 |
| has_traces != (n_traces > 0) | 0 |
| inject_time trước start hoặc sau end | 2 — hai case nêu ở phần kết luận |
| inject_time - time_start != normal_timesteps | 2 — đúng hai case đó |

Các kiểm tra timestamp không chứng minh quan hệ nhân quả hoặc suitability của case cho mô hình. Chúng chỉ chứng minh consistency nội bộ của trường metadata.

## Script và checks tái lập

Script mới chỉ nằm trong workspace nghiên cứu:

- D:/Project/flash-ticket-rca-research/scripts/audit/audit_reproducibility.py
- Kết quả máy đọc: D:/Project/flash-ticket-rca-research/audits/rcaeval/subagent-g-reproducibility-evidence.json

Script đọc manifest + Parquet, tính SHA-256 cục bộ, kiểm schema/row count/duplicate/null/string/timestamp/count consistency, và dùng API chính thức chỉ để xác minh revision + file metadata. Nó không gọi download case telemetry.

Các lệnh đã chạy:

    python --version
    py -0p
    py -3.12 --version
    D:/Project/flash-ticket-rca-research/.venv/Scripts/python.exe -m py_compile D:/Project/flash-ticket-rca-research/scripts/audit/audit_reproducibility.py
    D:/Project/flash-ticket-rca-research/.venv/Scripts/python.exe D:/Project/flash-ticket-rca-research/scripts/audit/audit_reproducibility.py

Evidence JSON ghi hash của ba script audit tại lúc chạy để truy nguyên. Script lấy metadata hiện hữu có SHA-256 1f6794c2e04c19f55a5f035804c003249706e7359928fb60c3a45638ca0da382.

## Rủi ro và điều kiện không được suy diễn

| Mức | Phát hiện | Hành động bắt buộc |
|---|---|---|
| MAJOR | Hai bất thường inject_time/window | Exclude hai case khỏi selection mặc định; chỉ đưa lại sau một kiểm tra raw-file có chủ đích hoặc erratum chính thức. |
| MAJOR | fetch_metadata.py lấy HEAD rồi mới ghi revision | Tạo hoặc sửa thao tác tái tải để nhận revision ghim làm input; trong Task B hiện tại dùng đúng revision manifest. |
| MINOR | Không có dependency lock ở workspace root | Trước baseline reproduction, freeze môi trường audit và ghi hash/phiên bản; không cần thêm package ở Task B hiện tại. |
| UNRESOLVED | Raw sample manifest, kích thước/hash raw file, duplicate/timestamp/schema ở telemetry | Chỉ kiểm sau khi six-case plan được duyệt và tải chọn lọc. |
| UNRESOLVED | Ý nghĩa nghiệp vụ của inject_time, root-cause labels, và operation labels | Thuộc kiểm tra F và raw audit; không xem chúng là model input chỉ vì metadata có sẵn. |

## Đề xuất độc lập cho raw sample plan

Đây là **INFERENCE từ metadata**, không phải kết luận về schema/quality của raw telemetry. Sáu case bên dưới tránh hai metadata anomaly nêu trên và tạo coverage đa hệ thống, đa suite, resource/network/code-level fault, metrics-only, logs-only, và multimodal.

| Case | Suite / system | Fault / root target | Lý do và uncertainty cần test |
|---|---|---|---|
| re1ob_adservice_cpu_1 | RE1 / Online Boutique | CPU stress / adservice | Metrics-only; kiểm giới hạn graph và RCA khi không có logs/traces. |
| re1tt_ts-auth-service_loss_1 | RE1 / Train Ticket | packet loss / ts-auth-service | Metrics-only, network fault, đối chiếu schema giữa system. |
| re2ob_currencyservice_delay_1 | RE2 / Online Boutique | network delay / currencyservice | Logs + traces + metrics; kiểm join cross-modal và runtime relation. |
| re2ss_carts_socket_1 | RE2 / Sock Shop | socket exhaustion / carts | Logs + metrics, không traces; kiểm missing-modality có cấu trúc. |
| re2tt_ts-route-service_disk_1 | RE2 / Train Ticket | disk I/O stress / ts-route-service | Full multimodal; metadata báo 1,316,502 trace rows, nên kiểm tính thực tế của retrieval và schema. |
| re3ob_currencyservice_f1_1 | RE3 / Online Boutique | code-level F1 / currencyservice | Full multimodal, contrast với RE2 cùng root service và fault family khác. |

Tổng metadata count cho proposal là 586,518 log rows, 1,816,894 trace rows và 871 metric identities; đây không phải file size, không được dùng làm ước lượng dung lượng download. Main agent phải đối chiếu proposal này với A và F trước khi tạo raw sample plan cuối cùng.

## Cross-review cần chuyển cho main agent

- So với A: đối chiếu row count, suite/system distribution và metadata anomaly case IDs với audit metadata độc lập của A.
- So với F: bảo đảm inject_time và label/provenance không đi vào model input; hai anomalous timestamp không được dùng để tạo normal/fault boundary.
- So với B/C/D/E sau raw retrieval: hoàn thiện manifest cho từng file (exact path, bytes, SHA-256) trước khi dùng bất kỳ kết luận schema nào.

**Không có disagreement với reviewer khác được giải quyết trong report G này**, vì các output A–F chưa phải bằng chứng đầu vào của G tại thời điểm kiểm tra. Main agent phải thực hiện disagreement matrix và quay lại dữ liệu thô nếu có bất đồng.
