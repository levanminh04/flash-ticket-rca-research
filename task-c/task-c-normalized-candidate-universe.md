# Task C — Normalized candidate universe

Trạng thái: DRAFT. Ngày: 2026-09-20. Tất cả hướng là CANDIDATE / TASK-C INFERENCE. Không có thứ tự ưu tiên.

## Hàng rào độc lập

A/B/C đã nộp từ phiên recovery, D/E/F nộp ở phiên tiếp tục. Main đã đọc trọn sáu báo cáo, xác nhận phần kết và hợp đồng. Chỉ sau thời điểm này mới thực hiện gộp. Mỗi reviewer sinh hai hướng: 12 đề xuất thô, không phải 12 câu hỏi khác nhau. Sáu reviewer dùng chung bằng chứng A/B; độc lập về diễn giải và không xem đề xuất của nhau trước khi nộp. Main không nhận là mù với hội thoại cũ.

## Ánh xạ đầy đủ

| ID trung tính | Đề xuất gốc | Câu hỏi/estimand sau chuẩn hóa | Vì sao gộp và khác biệt được giữ |
|---|---|---|---|
| C1 | CA-01, CB-01, CD-01 | Giá trị thông tin tăng thêm của quan hệ service quan sát được đối với root-service ranking, giữ bằng chứng cục bộ cố định | Cùng hiệu ứng đối chứng quan hệ đúng/không quan hệ/quan hệ đối chứng. CB nhấn mạnh grouped scenario testing; CD pairing và uncertainty; CA contribution/falsification. Giữ cả ba như yêu cầu validity, không biến split thành novelty. |
| C2 | CA-02, CB-02, CC-01, CD-02, CE-01, CF-02 | Giá trị của graph trong xếp hạng theo ngân sách bằng chứng event-time sau incident boundary đã biết | Cùng đường chất lượng theo cutoff, có controls cùng input và candidate set. Giữ stability là mô tả hồi cứu; coverage là một phần kết quả; CE thêm chi phí I/O/preprocessing; CF nhấn mạnh không lấy ranking thay detector. Không đồng nhất evidence horizon với ingestion latency. |
| C3 | CC-02 | Giá trị giữ danh tính operation như biểu diễn trung gian đối với root-service ranking | Chưa gộp C1: biến đổi chính là granularity của biểu diễn, không đơn thuần cấu trúc giữa service. Không có operation GT; kiểm ở output service. |
| C4 | CE-02 | Vị trí graph trong contextual scoring so với graph chỉ sau local scoring, chấm bằng service ranking qua scenario held-out | Không gộp C1 vì C1 cố định local evidence còn C4 thay score. Không gộp C5 vì C4 không có endpoint detection. Có thể trở thành ablation phụ, không tự coi là RQ đủ mạnh. |
| C5 | CF-01 | Giá trị graph ở detector so với ranker, với endpoint detection-regime và diagnosis tách biệt | Không gộp C4: thêm endpoint detector và lỗi nối tiếp; cần nhãn và controls khác. Không nhập một bảng MRR thành bằng chứng anomaly detection. |

## Quy tắc không làm mất khác biệt

Không gộp vì cùng nói graph, không bỏ ý phản bác của reviewer thiểu số. C1 hỏi quan hệ thêm thông tin gì ở budget chung; C2 hỏi đường giá trị theo budget; C3 hỏi representation; C4 hỏi stage of graph context; C5 hỏi detector–ranker system. Nếu các hướng bị hạ thành phụ ở gate sau, đó là loại/hạ vai trò có lý do, không phải gộp ngầm.

## Nguồn và hiệu chỉnh trước gate

Sáu file nguyên bản ở `phase-1-independent-candidates/` được đóng băng. Ledger là chỉ mục evidence; Task B §12 CLOSED có hiệu lực cao hơn lịch sử. Bốn kiểm hẹp trong `task-c-targeted-verification.md` xác nhận prior về graph ablation, unseen units, boundary sensitivity và trace-volume/cost. MicroRank không chứng minh bắt buộc đợi năm phút sau alert; bỏ diễn giải đó. Sai attribution thư 22/08 được C-F phát hiện: dùng Task C §5 + DT18 cho yêu cầu hiện hành, không gán tên thuật toán/metric là nguyên văn thư.

## Trạng thái bàn giao gate

Năm câu hỏi đã chuẩn hóa, chưa có winner. Gate dữ liệu, literature, feasibility và red team phải áp vào từng câu hỏi; không mặc định giữ đủ 2–4 hướng.

## Gate reconciliation — 2026-09-21, trước Red Team

Main đã đọc toàn bộ hai gate hoàn chỉnh và evidence cross-review. Giảm universe để Red Team thử bác bỏ: **C1, C2** giữ ở mức restricted empirical candidates; **C3/C4** hạ thành optional secondary experiments; **C5** hoãn primary. Đây không là lựa chọn winner hay phê duyệt nghiên cứu. Data gate cho C3 vẫn sống với service output; lý do hạ là literature/contribution, không thiếu operation GT. C5 chỉ còn injection-regime evaluation, không operational anomaly truth. Xem các bảng đầy đủ ở feasibility-gate và literature-positioning.

C2 được main làm rõ sau evidence crosscheck: H1 là biến thiên có ý nghĩa thực dụng của incremental graph value theo budget; gain dương nhưng phẳng không đủ chứng minh interaction. Không yêu cầu đổi dấu; kết quả âm hoặc phẳng vẫn phải báo. C1 kiểm relational main effect tại budget chung. Không coi hai hướng là hai nhiệm vụ phải cùng thực hiện.

Red Team chỉ được bắt đầu sau bản giảm này; có quyền loại cả C1/C2. Shortlist cuối chưa được khóa tại thời điểm ghi mục này.

## Kết quả cuối Phase 1 — 2026-09-21, sau Red Team

Mục này có hiệu lực hiện hành; các mốc trước giữ nguyên để bảo toàn lịch sử. Red Team hoàn tất 18 mục áp riêng cho C1/C2 và kiểm độc lập bản sửa RT-08. **C1/C2 SURVIVE WITH RESTRICTED CLAIM** như hai lựa chọn thay thế, không phải hai nhiệm vụ đã chọn. Utility chỉ thuộc pipeline/controls/budgets được kiểm; C2 đòi budget dependence, không chỉ main effect dương phẳng. Không FATAL còn mở trong claim hẹp; RT-17 vẫn MAJOR về sức đóng góp luận văn, sáu MODERATE là ràng buộc thực thi/tái lập chưa thể nhận là đã kiểm nghiệm. Không hướng nào đạt STRONG POSITIONING.

**C3/C4:** optional secondary experiments, không RQ chính vì contribution/literature gate, không vì thiếu operation GT khi output là service. **C5:** hoãn RQ chính vì prior và giới hạn nhãn detector; không bỏ nhiệm vụ detection của đề tài.

**TASK C PHASE 1: COMPLETE.** Shortlist hoàn tất ở trạng thái CANDIDATE, không winner/thuật toán/decision lock. Hợp đồng cuối và lựa chọn con người ở [báo cáo canonical](D:/Project/flash-ticket-platform/docs/research-rca/task-c-independent-research-shortlist.md). Bước tiếp theo là C Phase 2 sau lựa chọn rõ ràng của Minh; không tự mở Task D/E.
