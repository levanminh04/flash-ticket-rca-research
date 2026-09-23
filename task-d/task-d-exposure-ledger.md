# Task D — exposure ledger và kiểm tra nhỏ

- Ngày hoàn tất: 2026-09-23; kiểm tra phơi lộ ban đầu: 2026-09-22.
- Intent: `EXECUTE` trong phạm vi tài liệu và kiểm tra xác định nhỏ được giao. Tạo tác phương pháp mới là `FORMATION`; các quan sát về phơi lộ là `FACT`, không thay Task B/C hay phương pháp E1.
- Chủ sở hữu quyết định: Minh. Split bên dưới là `CANDIDATE` chờ rà soát giao thức chính; AI không phê duyệt split hay gate.
- `P = D:/Project/flash-ticket-platform`; `W = D:/Project/flash-ticket-rca-research`. W là nơi lưu bằng chứng được chỉ định cho Task D, không thay canonical P. Chỉ ghi `W/task-d/task-d-exposure-ledger.md` trong phần việc này.
- Đã đọc hiến pháp P, skill governance và capability summary B. Không tải dữ liệu, không cài thư viện, không chạy baseline/RCA, không mở raw telemetry Parquet. Kiểm tra mới chỉ đọc metadata Parquet có sẵn và JSON audit có sẵn, chạy Python đã cài trong bộ nhớ.

## 1. Phơi lộ đã biết và giới hạn

| Lớp bằng chứng | Trạng thái và phạm vi đã biết | Ràng buộc đối với diễn giải Task D |
|---|---|---|
| Schema | `FACT`: B đã kiểm 90 schema trace thống nhất; đã kiểm schema các mẫu raw được chọn. D đọc capability summary và machine summary, không quét lại raw | Không gọi schema là chưa thấy; không suy compatibility của toàn bộ 89 ca có log từ vài mẫu |
| Metadata, labels, distributions | `FACT`: metadata RE2-TT gồm 90 ca = 5 root × 6 fault × 3 repeat đã được đọc/phân tích trong B/C và đọc lại cho kiểm split D | Root/fault được dùng riêng phía evaluator để tạo split/nhóm báo cáo; không đưa vào features, tuning theo evaluation labels, candidate admission hay tie-break |
| Topology/candidates | `FACT`: full-trace audit đã xử lý 90 ca, 67.345.051 spans; C machine check đã đối chiếu tổng và candidate coverage. Union audit 27 services/161 service-operation pairs; full-case candidates 20–27, target hiện diện 90/90 | Đây là phơi lộ cấu trúc trên toàn tập. Không dùng union, full-case graph hay target presence để tạo vocabulary/candidates/graph của một cửa sổ giới hạn; không khẳng định prefix có cùng coverage |
| Selected raw cases | `FACT`: raw-sample plan chứa sáu ca, chỉ một ca RE2-TT là `re2tt_ts-auth-service_cpu_1`; B2B bổ sung `re2tt_ts-auth-service_cpu_2` với logs/metrics/traces. Xem danh sách chính xác bên dưới | Hai ca sample RE2-TT được chỉ định trong hai nguồn này đều ở scenario auth/cpu; đưa cả ba repeat vào dev theo rule ở §2. Điều này không xóa phơi lộ audit full traces của 90 ca |
| Historical baseline outputs/metrics | `FACT`: E1 §2.1 ghi 11 CSV/990 dòng kết quả, mỗi CSV có 90 ID duy nhất, cùng bộ ca/nhãn trong từng hệ; §3 đã phân tích kết quả Train Ticket và các nhóm root/fault. Đây là lịch sử đã xem baseline outputs và metrics của TT90 | Không được gọi 90 ca hoặc 60 ca proposed evaluation là dữ liệu chưa từng thấy, clean holdout hay xác nhận độc lập khỏi lịch sử. Task D không mở lại CSV, không tính lại RCA performance, không dùng số điểm E1 để chọn split/parameter |
| Historical run/parameter provenance | `FACT`: E1 §2.1 ghi `window=20`, `commit_hash=6018cde`, runtime/seed trống; §2.3 ghi thiếu lệnh chạy, manifest môi trường, dataset hash và patch của lượt chạy. E1 nói rõ kiểm định hậu nghiệm | Full historical parameter-selection history và mức tuning trên từng ca: `OPEN` — **NOT VERIFIED**. Không suy tham số chưa bị tác động bởi điểm lịch sử chỉ vì manifest không có |
| Task D parameter selection | `FACT`: split và swap check ở đây dùng quy tắc xác định đã giao, không tối ưu theo điểm hoặc label của prediction. Không có performance run mới | Quan hệ giữa toàn bộ lịch sử tham số của mọi người/agent và TT90: `OPEN` — **NOT VERIFIED**. Ledger không chứng nhận mù dữ liệu hồi tố |

**Disclosure của chính lượt kiểm tra:** một bộ lọc đọc hẹp E1 §3 ngày 2026-09-22 đã vô tình trả về cả vài phát biểu có độ lớn điểm lịch sử. Không chép lại các điểm đó ở đây, không dùng chúng để chọn split/parameter, và đã báo việc này cho agent chính. Vì vậy không khẳng định người kiểm ledger chưa từng thấy các số điểm. Chỉ giữ E1 làm bằng chứng về lịch sử phơi lộ; không mở lại thiết kế MyRCA ở E1 hay dùng nó làm nguồn chọn phương pháp D.

Sáu ca trong `raw-sample-plan.json`:

1. `re1ob_productcatalogservice_cpu_3`
2. `re2ob_productcatalogservice_loss_1`
3. `re2ss_orders_loss_2`
4. `re2tt_ts-auth-service_cpu_1`
5. `re3ss_carts_f1_1`
6. `re3tt_ts-route-service_f2_1`

B2B: `re2tt_ts-auth-service_cpu_2`. Manifest báo ba file khớp official LFS hashes. Đây là báo cáo của manifest có sẵn, không phải D hash lại raw. Full-trace B đọc range từ 89 đối tượng remote và dùng lại một local; không có full corpus 90 trace files được lưu tại W. Task D không bổ sung corpus.

## 2. Proposed evaluator-only split — `CANDIDATE`

Rule được kiểm trực tiếp trên metadata đã pin: lọc `dataset == RE2-TT`; sắp root label và fault label tăng dần lexical; root index `r` bắt đầu 0; dev nhận fault indices `(2*r) % 6` và `(2*r+1) % 6`. Một scenario là cặp `(root_cause_service, fault)`; cả ba repeats `1,2,3` đi cùng phía. Tất cả scenario còn lại là evaluation. Đây là một split cho thực nghiệm có khóa về sau trên dữ liệu đã có phơi lộ, không phải khôi phục một tập test chưa từng được xem.

Root order: `ts-auth-service`, `ts-order-service`, `ts-route-service`, `ts-train-service`, `ts-travel-service`.

Fault order: `cpu`, `delay`, `disk`, `loss`, `mem`, `socket`.

| r | Root | Dev scenarios — mỗi fault là một scenario, repeats 1/2/3 | Dev scenarios/cases | Evaluation scenarios/cases |
|---:|---|---|---:|---:|
| 0 | `ts-auth-service` | `cpu`, `delay` | 2 / 6 | 4 / 12 |
| 1 | `ts-order-service` | `disk`, `loss` | 2 / 6 | 4 / 12 |
| 2 | `ts-route-service` | `mem`, `socket` | 2 / 6 | 4 / 12 |
| 3 | `ts-train-service` | `cpu`, `delay` | 2 / 6 | 4 / 12 |
| 4 | `ts-travel-service` | `disk`, `loss` | 2 / 6 | 4 / 12 |
| Tổng | 5 roots | Chính xác 10 dev scenarios | **10 / 30** | **20 / 60** |

Mỗi scenario trong bảng tạo đúng ba case IDs theo dạng `re2tt_<root>_<fault>_<repeat>`, với `<repeat>` là 1, 2, 3. Các IDs có thật trong metadata đã được đối chiếu; không tạo thêm case. `re2tt_ts-auth-service_cpu_1`, `_2`, `_3` đều nằm dev.

| Fault | Dev scenarios | Dev cases | Evaluation scenarios | Evaluation cases |
|---|---:|---:|---:|---:|
| `cpu` | 2 | 6 | 3 | 9 |
| `delay` | 2 | 6 | 3 | 9 |
| `disk` | 2 | 6 | 3 | 9 |
| `loss` | 2 | 6 | 3 | 9 |
| `mem` | 1 | 3 | 4 | 12 |
| `socket` | 1 | 3 | 4 | 12 |

`FACT` của check: 90 case IDs; 30 scenarios; mỗi scenario có đúng repeats `[1,2,3]`; dev/evaluation rời nhau và phủ đủ 90; 30/60 cases. Không gọi đây là cân bằng tuyệt đối theo fault: mem/socket có ít dev scenarios hơn bốn fault còn lại.

**Opaque case handle — `CANDIDATE`:** `sha256(UTF8('TD-v1|' + caseID)).hexdigest()[:16]`, lowercase hex, 16 ký tự. Không thêm khoảng trắng hay normalize `caseID`. Kiểm 90 handles không collision. Evaluator giữ mapping handle↔caseID↔labels; handle dùng ghép kết quả và vận hành I/O. **Không bao giờ dùng handle làm scorer feature, fit/tuning input, seed thích ứng theo label, tie-break key hoặc cách chọn candidates.** Hash không phải bảo mật mật mã trước người biết bộ case IDs và không xóa phơi lộ cũ; nên scorer chỉ nhận telemetry/cấu trúc được contract cho phép, evaluator gắn handle ngoài phần tính điểm. Khi bổ sung corpus/đổi rule phải kiểm collision lại, không giả định 16 hex bảo đảm duy nhất vô hạn.

## 3. Feasibility của graph control — chỉ full-case audit

`FACT`, kiểm mới từ **per-case** `parent_resolution.observed_parent_to_child_service_edges` trong `re2tt-trace-full-subset-audit.json`; không dùng union graph, không mở Parquet trace. Giữ node set của từng ca từ `operation_representation.service_names`, kể cả isolates; bỏ self-loops; gộp hai hướng và mọi trọng số thành một cạnh vô hướng nhị phân.

Với mỗi cặp cạnh khác nhau `{a,b}`, `{c,d}` có bốn đầu mút khác nhau, xét cả hai hoán đổi `{{a,c},{b,d}}` và `{{a,d},{b,c}}`. Chỉ tính nếu không sinh cạnh đã có và partition connected components sau đổi **bằng chính xác partition trước đổi**, gồm cả membership của từng component. Hai phép thay hợp lệ của cùng cặp cạnh được tính riêng. Đây là số single-step swaps khả thi tại graph gốc, không phải số random graph samples, chuỗi swaps hay tuyên bố trộn đều.

| Đại lượng | Kết quả |
|---|---:|
| Full-case graphs đã kiểm | 90 |
| Số edges của simple undirected graph, min–max | 20–53 |
| Số connected components, min–max | 3–5 |
| Valid 2-edge swaps per graph, min–max | **154–1.176** |
| Graphs có 0 valid swaps | **0/90** |

Swap bảo toàn degree của từng node theo xây dựng (mỗi đầu mút mất một cạnh và nhận một cạnh); điều kiện partition bảo toàn cả component membership và kết nối bên trong. Node/edge count giữ nguyên. Kết quả không khẳng định graph có nghĩa nhân quả, không kiểm độ phủ topology thật, và không chứng minh control graph khác đủ mạnh ở mức xếp hạng.

**Giới hạn bắt buộc:** full-case edges có thể chứa dữ liệu sau reference window. Khả năng swap của **reference-only graph thực dùng cho scorer** là `OPEN` — **NOT VERIFIED**; tuyệt đối không nhập full-case edges để làm reference graph switchable. Cần kiểm lại trên graph đúng window khi bước thực thi được cho phép, giữ rõ ca không có valid swap. Không lấy kết quả 0/90 full-case làm bằng chứng rằng mọi reference graph sẽ switchable.

## 4. Rule/command và kiểm lại

Môi trường: Python có sẵn tại `C:/Users/84583/AppData/Local/Programs/Python/Python39/python.exe`; dùng stdlib và `pyarrow.parquet` đã có. Command dạng PowerShell `@' … '@ | python -`; không lưu script mới. Các bước được thực thi trong bộ nhớ:

```python
rows = [r for r in pq.read_table(METADATA).to_pylist()
        if r['dataset'] == 'RE2-TT']
roots = sorted({r['root_cause_service'] for r in rows})
faults = sorted({r['fault'] for r in rows})
dev = {(s, faults[j % 6]) for i, s in enumerate(roots)
       for j in (2*i, 2*i+1)}
# Verify each (root, fault) group has repeats [1,2,3]; partition by dev.
handles = {r['case']: hashlib.sha256(
    ('TD-v1|' + r['case']).encode('utf-8')).hexdigest()[:16] for r in rows}
assert len(rows) == 90 and len(dev) == 10
assert len(set(handles.values())) == 90

# Per case: V = service_names; E = sorted unordered non-self edge pairs.
before = components(V, E)  # canonical sorted tuple of sorted member tuples
valid = 0
for (a,b), (c,d) in itertools.combinations(sorted(E), 2):
    if len({a,b,c,d}) != 4:
        continue
    for proposed in (((a,c),(b,d)), ((a,d),(b,c))):
        added = {tuple(sorted(edge)) for edge in proposed}
        if E & added:
            continue
        changed = (E - {(a,b),(c,d)}) | added
        if components(V, changed) == before:
            valid += 1
```

`components` dùng traversal adjacency trên toàn `V`, kể cả isolates, trả partition chuẩn hóa như chú thích. Nguồn và hash bên dưới đủ định vị chính xác tập input; check không dùng số điểm baseline. Không sinh graph-control artifact dùng cho thực nghiệm, không chạy RCA performance.

## 5. Source hashes — SHA-256

Hash tính trực tiếp trên bytes file hiện có; với E1, hashing toàn file chỉ định danh nguồn, không đọc thêm nội dung để chọn phương pháp. Các đường dẫn P/W theo định nghĩa đầu tài liệu.

| Source | SHA-256 |
|---|---|
| `P/docs/research-rca/task-b-dataset-capability-summary.md` | `18a71ea34e0d3f5d5e11bbdeae3439536bd80d6aaa7f22172b4ab0ee0ef3a45b` |
| `P/docs/research-rca/E1-kiem-dinh-rcaeval-va-kha-thi-myrca.md` — chỉ §2–3 cho phơi lộ | `5ffde6f2403e5beccb05cd5b927758ab358f33509e4b9c839c00a2a705a323bd` |
| `W/datasets/rcaeval/metadata/cases.parquet` | `c49a288920dbba2e8e724679a14636d5c7eb2b45426bba14007ef79a6c0ab1bb` |
| `W/audits/rcaeval/raw-sample-plan.json` | `d5a13a0ae865fc63e0eb3b3d5638cb65b75ca89affe142091eeb39f4f101becf` |
| `W/audits/rcaeval/b2b-re2tt-multimodal-download-manifest.json` | `6e5e9a680bb884b6448a5f2b93ea1dd5fe1ba6f58e14656f9f9408ced54f1365` |
| `W/audits/rcaeval/re2tt-trace-full-subset-audit.json` | `e91877f8b28658bb4f7bff31074c42dc0955dfde839b3aad13df5b31707b1570` |
| `W/task-c/task-c-machine-evidence-check.json` | `357a0ba2bcb6eda4d81348bc22c47e53e1ee702f3217338d3b169282ed417aaf` |
| `W/task-c/task-c-input-inventory.json` | `42334961e3225df4f4db2d9e56f0337616d5b054dba0ab31b310307c88c49147` |

Pinned dataset revision: `afeacb11bcc94dadfd1c8f483ee4377b2b8b614e`. C machine check xác nhận lại tổng từ bằng chứng lưu sẵn, không phải một đợt raw độc lập. C input inventory cho biết nguồn đã có trong C, không chứng minh từng byte đã được mọi người xem hoặc chưa xem.

## 6. Handoff

- Không đổi quyết định đã duyệt; split/handles ở `CANDIDATE`; full-case check là `FACT`. Agent chính sở hữu kết luận giao thức và split adjudication, Minh sở hữu phê duyệt của con người.
- `OPEN`: mức độ chọn/tune tham số lịch sử; reference-only graph switchability; khả năng tổng quát hóa ngoài tập này. Không điền thiếu đầu vào bằng suy đoán.
- Giả định kiểm: metadata labels dùng nguyên văn; scenario là root×fault với ba repeats; graph control theo projection vô hướng nhị phân đã mô tả. Không suy candidate services từ năm root labels.
- Validation: đã đọc lại toàn ledger sau ghi, đối chiếu kết quả split/handles/swaps với output và hash của các source. Chỉ tạo file ledger này trong phần việc được giao. Audit governance của P chạy ngày 2026-09-23: `PASS`, 0 warnings; audit này kiểm canonical P, không tự chứng nhận phương pháp hoặc nội dung W.
- Báo cáo chính thức cần nêu phơi lộ metadata/structure/historical outputs, tính thăm dò của bộ dữ liệu này, rule split nguyên cụm, và giới hạn full-case so với reference-only graph. Không đưa score-history thành hiệu quả mới của D.
