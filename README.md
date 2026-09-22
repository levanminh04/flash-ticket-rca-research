# FlashTicket RCA — Execution workspace

**This workspace is execution/storage, not the authority for final project decisions.**

Chủ sở hữu: Minh. Binding hiện tại: `D:/Project/flash-ticket-rca-research`. Nơi này giữ dữ liệu, môi trường, audit scripts, reviewer chi tiết và đầu ra thực nghiệm. Tri thức/quyết định/contract/handoff bền vững nằm trong repository `D:/Project/flash-ticket-platform/docs/research-rca`.

- Bắt đầu phiên: [SESSION-BOOTSTRAP](D:/Project/flash-ticket-platform/docs/research-rca/SESSION-BOOTSTRAP.md).
- Trạng thái và bước chính xác tiếp theo: [CURRENT-STATE](D:/Project/flash-ticket-platform/docs/research-rca/CURRENT-STATE.md).
- Lộ trình duy nhất: [MASTER-RESEARCH-PROGRAM](D:/Project/flash-ticket-platform/docs/research-rca/MASTER-RESEARCH-PROGRAM.md).
- Định vị/quyền nguồn giữa hai root: [ARTIFACT-MAP](D:/Project/flash-ticket-platform/docs/research-rca/ARTIFACT-MAP.md).
- Quyết định con người: [RESEARCH-DECISIONS](D:/Project/flash-ticket-platform/docs/research-rca/RESEARCH-DECISIONS.md).

`datasets/rcaeval/` chứa metadata và raw samples theo manifest; audit full traces bằng range-read không có nghĩa toàn bộ corpus còn lưu local. `audits/rcaeval/` và `dataset-audit/` giữ bằng chứng Task B; `scripts/audit/` giữ code. `task-c/` là evidence/gates/review/checkpoint lịch sử của Task C. `program-review/` giữ independent workflow review và validation gói điều phối. `.venv/` là môi trường local, không tự là portable backup.

Không đọc checkpoint lịch sử để ghi đè CURRENT-STATE. Không tải/cài/chạy task mới chỉ vì thư mục đã có. Raw evidence phân xử sự thật dữ liệu; quyết định dự án phải lưu ở canonical repository. README này không duy trì roadmap/trạng thái task thứ hai.
