# C1 observed graph/PPR — post-hoc development mechanism analysis

**POST-HOC DEVELOPMENT DIAGNOSTIC**  
**NOT FINAL EFFICACY**  
**NOT PARAMETER SELECTION**

Owner nhận bàn giao: Minh. Phạm vi: đúng 30 RE2-TT development cases đã hoàn tất. Phân tích này chỉ đọc output sealed; không chạy lại prediction/model, không sửa TD/config/registry và không mở final60/F/G/H/I.

## Kết luận ngắn

**Hypothesis verdict: NOT SUPPORTED.** Trên development30, không có bằng chứng rằng PPR thường làm hại khi local evidence đã đủ chắc chắn theo dấu hiệu trực tiếp là root đứng rank 1. Cả 17/17 case local rank-1 đều giữ root ở rank 1 sau PPR; không có case nào tụt. Toàn bộ 6 HARM case đều bắt đầu với root không đứng đầu local. Vì vậy dữ liệu phù hợp hơn với cơ chế yếu hơn: PPR có thể làm xấu thêm các case local vốn mơ hồ/sai top-1, trong khi evidence mạnh đủ sức kháng lại phép lan truyền trong sample nhỏ này.

Evidence thuận cho phần *relative dilution*: 6/6 HARM case có thêm service vượt root sau PPR. Trong đó, dominant non-root mass giảm ở 6/6 case, phù hợp với việc mass của competitor mạnh bị trải ra nhiều node. Evidence chống phần *khi local đã mạnh*: 0 local-rank1 case bị tụt; HELP cũng chỉ xuất hiện ở case root chưa rank1. Đây là quan sát cơ chế hậu nghiệm, không là chứng minh nhân quả hay kết luận cho final/FlashTicket.

## Identity và validation

- Session bootstrap: P branch `codex/rca-research-program`, HEAD `576be4b6935c9a837e6f2bcc6356a89bfe61c6ac`, chỉ có README dirty sẵn từ trước (SHA-256 `3646cb1b6e8da832e8b9513fd8318d749f7f5f6788b5d3223eda7f5a9a662274`); W branch `main`, HEAD `664d7180f0af3fadc8f11d7747b9d75833aeca34`, clean trước phân tích.
- TD-v1.3 SHA-256: `34fd73f6a84dc6b45834bd7fd4cc7b86e19e54f1011de99735631f027ee18971` (khớp canonical).
- Run: `e27-033-c1-development-full`; exit code 0; L=0.744206, O=0.702405, O−L=-0.041801.
- `c1-results.json` SHA-256 `eeeb0a09f43281d1df649a1b74e352d484796263bd3fb921aadb1c634e1c1e3d`; `c1-sensitivity.json` SHA-256 `0e955b12ad6977a9b2ce7f7b80db211c6e3c87aebe45250bb673227befd3648b`; cả hai khớp identity đã ghi trong final scientific review/inventory.
- Recompute từ đúng 30/30 case khớp `c1-results.json` trong tolerance 1e-12; mọi tie interval/rank của L và O cũng khớp score sealed.
- Đã kiểm SHA-256 seal cho 30 local score artifacts, 30 observed-local6 artifacts và 60 temporal sensitivity artifacts (bin5/bin20). Đã đọc 30 uniform diagnostics; run không cung cấp per-file seal cho loại intermediate này nên báo cáo không bịa seal.
- Topology summary: 180/180 jobs COMPLETE; artifact ghi rõ `no_predictions=true`; không tái sinh graph.

## Q1 — Những case L đã đặt root rank 1

- Local rank1: **17/30**.
- Giữ rank1 sau PPR: **17/17**.
- Bị tụt: **0/17**; mức tụt = 0 case, 0 bậc, tổng ΔRR=0 trong nhóm này.
- Do đó giảm MRR không đến từ việc PPR phá các root local-top1 trong sample này.

## Q2–Q3 — HARM khác HELP như thế nào

Các số dưới đây là median [Q1, Q3]. Raw local score có thang theo từng case; so sánh median và Spearman chỉ là mô tả hậu nghiệm.

| Nhóm | n | Local rank1 | Root margin | Global top1−top2 | Root undirected degree | Reachability fraction | Parent resolution | Root PPR mass Δ | Uniform-PPR root rank |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| HELP | 2 | 0 | -246.409346 [-252.586769, -240.231923] | 207.608113 [198.613068, 216.603159] | 8.000000 [8.000000, 8.000000] | 0.888889 [0.888889, 0.888889] | 0.999975 [0.999966, 0.999984] | 0.098309 [0.097675, 0.098943] | 3.000000 [3.000000, 3.000000] |
| HARM | 6 | 0 | -5.527500e+09 [-9.343525e+11, -2.512500e+08] | 5.527500e+09 [2.512500e+08, 9.343525e+11] | 0 [0, 2.250000] | 0.037037 [0.037037, 0.675926] | 1.000000 [0.999946, 1.000000] | 1.040834e-17 [1.734723e-18, 0.003456] | 12.000000 [12.000000, 18.000000] |
| UNCHANGED | 22 | 17 | 388.602446 [24.193779, 76586.679395] | 623.758560 [125.970414, 76586.679395] | 3.000000 [2.250000, 4.500000] | 0.888889 [0.650000, 0.888889] | 0.999963 [0.999928, 1.000000] | -0.226811 [-0.417093, -0.122745] | 12.000000 [9.750000, 20.000000] |

- HARM: root distribution `ts-auth-service:4, ts-route-service:1, ts-train-service:1`; fault distribution `cpu:2, delay:3, mem:1`; cell distribution `ts-auth-service × cpu:1, ts-auth-service × delay:3, ts-route-service × mem:1, ts-train-service × cpu:1`.
- HELP: root distribution `ts-travel-service:2`; fault distribution `loss:2`; cell distribution `ts-travel-service × loss:2`.
- Local: HARM bắt đầu ở ranks 2,2,4,3,2,2; HELP bắt đầu ở ranks 7 và 10. Cả hai nhóm đều có root margin âm; raw margin có thang theo case nên không đặt một threshold hậu nghiệm.
- Root visibility không giải thích khác biệt: 30/30 root hiện diện trong candidate set. Nhưng topology có pattern rõ: 4/6 HARM roots là isolate, so với 0/2 HELP roots; exact per-case fields nằm trong CSV.
- Hai HELP roots đều degree 8, cách strongest local competitor 1 hop và có cạnh raw competitor→root. Trong HARM, bốn isolate không reach competitor; hai root còn lại degree 3, cách competitor 2 hops và không có direct edge.
- Global graph size không tách nhóm: 8/8 changed cases đều có 27 nodes/55 edges. Khác biệt nằm ở vị trí root, không phải kích thước graph.
- Parent resolution không tạo common pattern: một HARM case là 0.835500, năm HARM còn lại gần/đúng 1; hai HELP gần 1. Trong 8 changed cases, root reference trace visible=8/8, max query-only count=0, max conflicted metric-channel count=0. Đây là field thật từ loader audit, không phải proxy.
- Literal root-mass dilution không xuất hiện: chỉ 0/6 HARM root giảm absolute mass. Bốn auth roots là isolate nên root mass được self-loop giữ nguyên; dominant mass ở component còn lại bị lan ra, khiến nhiều node vượt root. Ngược lại 2/2 HELP roots tăng mass và đều có undirected degree 8. Đây là cơ chế gần của operator/topology, không chứng minh topology là nguyên nhân nhân quả đúng/sai.

## Q4 — Mức độ chi phối theo root/fault/cell

Tổng negative contribution trước bù trừ là 2.011176 RR; tổng positive contribution là 0.757143. `ts-auth-service` tạo 1.136667 (56.52%) tổng độ lớn âm. Vì vậy O−L âm bị chi phối đáng kể bởi auth, nhưng không chỉ bởi một case: route/mem và train/cpu cũng âm. Ngược lại, travel/loss là cell dương duy nhất và bù một phần đáng kể.

### Theo root

| Nhóm | n | Mean O−L | Leave-group O−L | HELP | HARM | UNCHANGED |
|---|---:|---:|---:|---:|---:|---:|
| ts-auth-service | 6 | -0.189444 | -0.004890 | 0 | 4 | 2 |
| ts-order-service | 6 | 0 | -0.052251 | 0 | 0 | 6 |
| ts-route-service | 6 | -0.072222 | -0.034196 | 0 | 1 | 5 |
| ts-train-service | 6 | -0.073529 | -0.033869 | 0 | 1 | 5 |
| ts-travel-service | 6 | 0.126190 | -0.083799 | 2 | 0 | 4 |

### Theo fault

| Nhóm | n | Mean O−L | Leave-group O−L | HELP | HARM | UNCHANGED |
|---|---:|---:|---:|---:|---:|---:|
| cpu | 6 | -0.150196 | -0.014702 | 0 | 2 | 4 |
| delay | 6 | -0.112778 | -0.024057 | 0 | 3 | 3 |
| disk | 6 | 0 | -0.052251 | 0 | 0 | 6 |
| loss | 6 | 0.126190 | -0.083799 | 2 | 0 | 4 |
| mem | 3 | -0.144444 | -0.030396 | 0 | 1 | 2 |
| socket | 3 | 0 | -0.046446 | 0 | 0 | 3 |

### Theo cell

| Nhóm | n | Mean O−L | Leave-group O−L | HELP | HARM | UNCHANGED |
|---|---:|---:|---:|---:|---:|---:|
| ts-auth-service × cpu | 3 | -0.153333 | -0.029409 | 0 | 1 | 2 |
| ts-auth-service × delay | 3 | -0.225556 | -0.021384 | 0 | 3 | 0 |
| ts-order-service × disk | 3 | 0 | -0.046446 | 0 | 0 | 3 |
| ts-order-service × loss | 3 | 0 | -0.046446 | 0 | 0 | 3 |
| ts-route-service × mem | 3 | -0.144444 | -0.030396 | 0 | 1 | 2 |
| ts-route-service × socket | 3 | 0 | -0.046446 | 0 | 0 | 3 |
| ts-train-service × cpu | 3 | -0.147059 | -0.030106 | 0 | 1 | 2 |
| ts-train-service × delay | 3 | 0 | -0.046446 | 0 | 0 | 3 |
| ts-travel-service × disk | 3 | 0 | -0.046446 | 0 | 0 | 3 |
| ts-travel-service × loss | 3 | 0.252381 | -0.074488 | 2 | 0 | 1 |

Các mean và leave-group ở trên được recompute từ 30 case và assert khớp toàn bộ saved subgroup/leave-group results trong `c1-results.json` ở tolerance 1e-12.

## Q5 — Temporal sensitivity bin5 / primary-bin10 / bin20

| Bin setting | L MRR | O MRR | O−L | HELP | HARM | UNCHANGED | Local rank1 | Rank1 giữ | Rank1 tụt | Root-margin↔ΔRR Spearman ρ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| bin5 | 0.498343 | 0.337060 | -0.161283 | 1 | 19 | 10 | 7 | 7 | 0 | 0.455328 |
| primary/bin10 | 0.744206 | 0.702405 | -0.041801 | 2 | 6 | 22 | 17 | 17 | 0 | 0.384444 |
| bin20 | 0.752963 | 0.754206 | 0.001243 | 3 | 4 | 23 | 18 | 18 | 0 | 0.102639 |

Pattern thay đổi theo độ phân giải thời gian: bin5 làm local yếu hơn và số HARM tăng; bin20 gần trung hòa về mean nhưng vẫn có cả HELP lẫn HARM. Ở cả ba setting, không có local-rank1 case nào bị PPR đẩy khỏi rank1. Quan sát này chống hypothesis local-strong→harm, nhưng cũng cho thấy mechanism rất nhạy với binning. Không dùng bảng này để chọn bin tốt nhất.

## Q6 — Hypothesis adjudication

**Verdict: NOT SUPPORTED.**

Evidence thuận:

- 6/6 HARM case có thêm node vượt root sau PPR; 6/6 đồng thời có best non-root mass giảm, phù hợp với mass mạnh bị trải ra nhiều node và làm root tụt tương đối.
- O−L thay đổi theo graph/topology và temporal binning; harm không phải lỗi số học vì score/rank/seal và aggregate đều khớp artifact đã audit.

Evidence chống:

- 17/17 local-rank1 case giữ rank1; 0 bị hại. HARM chỉ xảy ra khi root đã không là local top1.
- Chỉ 0/6 HARM root giảm absolute PPR mass; do đó dữ liệu không hỗ trợ cách hiểu literal rằng PPR lấy bớt mass khỏi root mạnh.
- Khi temporal resolution chuyển từ bin5 sang bin20, local rank1 tăng và mean harm giảm từ âm mạnh về gần 0; pattern đi ngược dự đoán rằng local mạnh hơn sẽ bị PPR làm hại thường xuyên hơn.
- HELP tập trung ở travel/loss; HARM tập trung ở auth/cpu-delay, route/mem và train/cpu. Root×fault confounding và chỉ 10 cells khiến không thể gán cơ chế riêng cho margin, degree hay trace quality.
- Không có comparator 'gated propagation' hay can thiệp topology theo mechanism; do đó từ `O−L` không thể chứng minh chữ *indiscriminate* là nguyên nhân nhân quả.

Hypothesis yếu hơn được development evidence gợi ý ở mức CANDIDATE: PPR có thể làm xấu thêm các case mà local ranking đã mơ hồ/sai top1, tùy topology và binning. Đây không phải method change hay đề xuất graph gate.

## Correlation — EXPLORATORY / POST-HOC / NOT CAUSAL

| Feature | Spearman ρ với ΔRR | p (descriptive) |
|---|---:|---:|
| root local margin | 0.384444 | 0.035941 |
| root undirected degree | 0.568637 | 0.001043 |
| root reachability fraction | 0.422468 | 0.020034 |
| parent-resolution rate | -0.115347 | 0.543871 |
| uniform-PPR root rank | -0.243853 | 0.194085 |

p-value chỉ được ghi để mô tả phép tính; không phải confirmatory test, không sửa multiple comparisons, và 30 cases/10 cells không độc lập theo nghĩa population.

Cross-check sau raw recomputation: `final-numerical-review.md` xác nhận toàn bộ 540 L/O sensitivity case metrics và headline means; `final-scientific-review.md` ghi cùng 2 HELP/6 HARM/22 UNCHANGED, travel/loss dương, auth/delay âm và sign flip nhỏ ở bin20. Review prose chỉ dùng để đối chiếu, không thay raw artifacts.

## Bảng 30 case — bản compact

Bản đầy đủ với local scores, graph degree/reachability/relation và input-quality fields nằm ở `case-table.csv`. `UNKNOWN` chỉ được dùng khi field không tồn tại.

| Case | Cell | L RR/rank | O RR/rank | ΔRR | Outcome | Root margin | Degree in/out/u | Reach | Strongest competitor (distance) |
|---|---|---:|---:|---:|---|---:|---:|---:|---|
| re2tt_ts-auth-service_cpu_1 | ts-auth-service × cpu | 1.000000/1-1 | 1.000000/1-1 | 0 | UNCHANGED | 7.653470 | 0/0/0 | 1/27 | ts-contacts-service (UNREACHABLE) |
| re2tt_ts-auth-service_cpu_2 | ts-auth-service × cpu | 0.500000/2-2 | 0.040000/25-25 | -0.460000 | HARM | -1.242453e+12 | 0/0/0 | 1/27 | ts-preserve-other-service (UNREACHABLE) |
| re2tt_ts-auth-service_cpu_3 | ts-auth-service × cpu | 0.500000/2-2 | 0.500000/2-2 | 0 | UNCHANGED | -13.767199 | 0/0/0 | 1/27 | ts-consign-service (UNREACHABLE) |
| re2tt_ts-auth-service_delay_1 | ts-auth-service × delay | 0.500000/2-2 | 0.040000/25-25 | -0.460000 | HARM | -1.005000e+09 | 0/0/0 | 1/27 | ts-inside-payment-service (UNREACHABLE) |
| re2tt_ts-auth-service_delay_2 | ts-auth-service × delay | 0.250000/4-4 | 0.200000/5-5 | -0.050000 | HARM | -7.752012 | 0/0/0 | 1/27 | ts-user-service (UNREACHABLE) |
| re2tt_ts-auth-service_delay_3 | ts-auth-service × delay | 0.333333/3-3 | 0.166667/6-6 | -0.166667 | HARM | -37.808061 | 0/0/0 | 1/27 | ts-payment-service (UNREACHABLE) |
| re2tt_ts-order-service_disk_1 | ts-order-service × disk | 1.000000/1-1 | 1.000000/1-1 | 0 | UNCHANGED | 76722.939697 | 5/1/6 | 24/27 | ts-preserve-service (1) |
| re2tt_ts-order-service_disk_2 | ts-order-service × disk | 1.000000/1-1 | 1.000000/1-1 | 0 | UNCHANGED | 108673.363706 | 1/1/2 | 13/20 | ts-assurance-service (UNREACHABLE) |
| re2tt_ts-order-service_disk_3 | ts-order-service × disk | 1.000000/1-1 | 1.000000/1-1 | 0 | UNCHANGED | 114227.361826 | 1/1/2 | 13/20 | ts-inside-payment-service (1) |
| re2tt_ts-order-service_loss_1 | ts-order-service × loss | 0.500000/2-2 | 0.500000/2-2 | 0 | UNCHANGED | -22.537462 | 5/1/6 | 24/27 | ts-preserve-service (1) |
| re2tt_ts-order-service_loss_2 | ts-order-service × loss | 0.500000/2-2 | 0.500000/2-2 | 0 | UNCHANGED | -33.376195 | 1/1/2 | 13/20 | ts-inside-payment-service (1) |
| re2tt_ts-order-service_loss_3 | ts-order-service × loss | 0.500000/2-2 | 0.500000/2-2 | 0 | UNCHANGED | -938.358322 | 1/1/2 | 13/20 | ts-inside-payment-service (1) |
| re2tt_ts-route-service_mem_1 | ts-route-service × mem | 0.500000/2-2 | 0.066667/15-15 | -0.433333 | HARM | -1.005000e+10 | 3/0/3 | 24/27 | ts-seat-service (2) |
| re2tt_ts-route-service_mem_2 | ts-route-service × mem | 1.000000/1-1 | 1.000000/1-1 | 0 | UNCHANGED | 246.623512 | 3/0/3 | 24/27 | ts-user-service (3) |
| re2tt_ts-route-service_mem_3 | ts-route-service × mem | 1.000000/1-1 | 1.000000/1-1 | 0 | UNCHANGED | 716.935740 | 3/0/3 | 24/27 | ts-admin-travel-service (2) |
| re2tt_ts-route-service_socket_1 | ts-route-service × socket | 0.500000/2-2 | 0.500000/2-2 | 0 | UNCHANGED | -171.506375 | 3/0/3 | 24/27 | ts-admin-travel-service (2) |
| re2tt_ts-route-service_socket_2 | ts-route-service × socket | 1.000000/1-1 | 1.000000/1-1 | 0 | UNCHANGED | 73.814708 | 3/0/3 | 24/27 | ts-admin-travel-service (2) |
| re2tt_ts-route-service_socket_3 | ts-route-service × socket | 1.000000/1-1 | 1.000000/1-1 | 0 | UNCHANGED | 153.859776 | 3/0/3 | 24/27 | ts-admin-travel-service (2) |
| re2tt_ts-train-service_cpu_1 | ts-train-service × cpu | 1.000000/1-1 | 1.000000/1-1 | 0 | UNCHANGED | 123.352838 | 3/0/3 | 24/27 | ts-admin-travel-service (2) |
| re2tt_ts-train-service_cpu_2 | ts-train-service × cpu | 1.000000/1-1 | 1.000000/1-1 | 0 | UNCHANGED | 133.823143 | 3/0/3 | 24/27 | ts-admin-travel-service (2) |
| re2tt_ts-train-service_cpu_3 | ts-train-service × cpu | 0.500000/2-2 | 0.058824/17-17 | -0.441176 | HARM | -1.246455e+12 | 3/0/3 | 24/27 | ts-preserve-other-service (2) |
| re2tt_ts-train-service_delay_1 | ts-train-service × delay | 1.000000/1-1 | 1.000000/1-1 | 0 | UNCHANGED | 1523.480500 | 3/0/3 | 24/27 | ts-admin-travel-service (2) |
| re2tt_ts-train-service_delay_2 | ts-train-service × delay | 1.000000/1-1 | 1.000000/1-1 | 0 | UNCHANGED | 530.581381 | 3/0/3 | 24/27 | ts-admin-travel-service (2) |
| re2tt_ts-train-service_delay_3 | ts-train-service × delay | 1.000000/1-1 | 1.000000/1-1 | 0 | UNCHANGED | 1653.033664 | 3/0/3 | 24/27 | ts-travel2-service (1) |
| re2tt_ts-travel-service_disk_1 | ts-travel-service × disk | 1.000000/1-1 | 1.000000/1-1 | 0 | UNCHANGED | 76177.898491 | 4/5/8 | 24/27 | ts-security-service (2) |
| re2tt_ts-travel-service_disk_2 | ts-travel-service × disk | 1.000000/1-1 | 1.000000/1-1 | 0 | UNCHANGED | 107390.732644 | 2/3/5 | 13/20 | ts-admin-travel-service (1) |
| re2tt_ts-travel-service_disk_3 | ts-travel-service × disk | 1.000000/1-1 | 1.000000/1-1 | 0 | UNCHANGED | 84474.418143 | 2/3/5 | 13/20 | ts-inside-payment-service (4) |
| re2tt_ts-travel-service_loss_1 | ts-travel-service × loss | 0.142857/7-7 | 0.500000/2-2 | 0.357143 | HELP | -234.054500 | 4/5/8 | 24/27 | ts-admin-travel-service (1) |
| re2tt_ts-travel-service_loss_2 | ts-travel-service × loss | 0.100000/10-10 | 0.500000/2-2 | 0.400000 | HELP | -258.764192 | 4/5/8 | 24/27 | ts-admin-travel-service (1) |
| re2tt_ts-travel-service_loss_3 | ts-travel-service × loss | 1.000000/1-1 | 1.000000/1-1 | 0 | UNCHANGED | 6.201000e+10 | 4/5/8 | 24/27 | ts-admin-travel-service (1) |

## Evidence state, limitations và việc nên kiểm tiếp

- `FACT`: identity/hashes, 30-case metrics, sealed scores, graph/input fields và các recomputation trong báo cáo.
- `CANDIDATE`: diễn giải mechanism, verdict hypothesis và hypothesis yếu hơn nêu trên.
- `OPEN`: human method approval/freeze, final efficacy, external generalization và FlashTicket validation.
- Sample chỉ 30 incidents/10 cells; root và fault không crossed đầy đủ; local scores không có một thang tuyệt đối chung giữa cases; correlation không causal.
- Reachability/distance được tính trực tiếp trên adjacency sealed sau khi đối xứng hóa đúng selected PPR (`undirected`, damping 0.5); không phải proxy từ tên service.
- Evidence tiếp theo nên kiểm: trên campaign được cấp quyền riêng, kiểm xem pattern `local non-top1 + topology redistribution → HARM` có lặp lại trên cells/dataset độc lập và FlashTicket hay không, với cùng frozen method và planned denominators. Không thay operator/config từ kết quả development này.

## Artifact và execution boundary

Tạo đúng ba artifact:

- `analysis.py` — script chỉ đọc sealed outputs và tự kiểm invariants/hashes.
- `case-table.csv` — bảng đúng 30 case, đầy đủ field được yêu cầu.
- `report.md` — báo cáo này.

Xác nhận: **0 model/prediction rerun; 0 RCD/C5 run; 0 graph regeneration; 0 TD/config/registry mutation; final60/F/G/H/I untouched; 0 commit/push.**

PHASE 1 COMPLETE — WAITING FOR MINH.  
PHASE 2 NOT STARTED.
