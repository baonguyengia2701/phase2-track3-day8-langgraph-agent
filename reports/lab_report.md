# Báo cáo Lab Ngày 08 - Điều phối Agent với LangGraph

## 1. Thành viên / Sinh viên

- Tên: [Nguyễn Gia Bảo - 2A202600156]
- Repo/commit: main
- Ngày: 2026-05-11

## 2. Kiến trúc (Architecture)

Hệ thống sử dụng kiến trúc đồ thị (graph) của LangGraph để điều phối luồng xử lý ticket hỗ trợ:
- **Các Node**: 
    - `intake`: Chuẩn hóa câu hỏi từ người dùng.
    - `classify`: Phân loại câu hỏi dựa trên từ khóa (keywords).
    - `tool`: Mô phỏng gọi API hoặc công cụ bên ngoài.
    - `evaluate`: Node kiểm tra kết quả từ tool để quyết định có cần thử lại (retry) hay không.
    - `risky_action`: Chuẩn bị các hành động nhạy cảm cần phê duyệt.
    - `approval`: Node dừng luồng để chờ con người phê duyệt (HITL).
    - `retry`: Quản lý bộ đếm số lần thử lại và ghi nhận lỗi.
    - `dead_letter`: Xử lý các trường hợp thất bại hoàn toàn sau khi hết số lần thử.
- **Các Cạnh (Edges)**: Sử dụng các cạnh có điều kiện (conditional edges) từ `classify`, `evaluate`, `retry`, và `approval` để điều hướng linh hoạt.

## 3. Lược đồ trạng thái (State schema)

`AgentState` kết hợp giữa các trường ghi đè và các trường chỉ cho phép thêm (append-only) để đảm bảo tính minh bạch và truy vết.

| Trường | Reducer | Tại sao |
|---|---|---|
| messages | append | Lưu lịch sử hội thoại và dấu vết các node đã đi qua |
| tool_results | append | Lưu lịch sử kết quả của tool để phục vụ việc đánh giá |
| errors | append | Theo dõi các lỗi tạm thời để phân tích retry |
| events | append | Nhật ký kiểm thử tất cả các bước chuyển đổi node |
| route | overwrite | Lưu trữ phân loại luồng hiện tại |
| attempt | overwrite | Theo dõi số lần thử lại để giới hạn vòng lặp |
| evaluation_result| overwrite | Xác định xem vòng lặp retry nên tiếp tục hay dừng |

## 4. Kết quả các kịch bản (Scenario results)

Dữ liệu được trích xuất từ file `outputs/metrics.json`.

| Scenario | Expected route | Actual route | Success | Retries | Interrupts |
|---|---|---|---:|---:|---:|
| S01_simple | simple | simple | Có | 0 | 0 |
| S02_tool | tool | tool | Có | 0 | 0 |
| S03_missing | missing_info | missing_info | Có | 0 | 0 |
| S04_risky | risky | risky | Có | 0 | 1 |
| S05_error | error | error | Có | 2 | 0 |
| S06_delete | risky | risky | Có | 0 | 1 |
| S07_dead_letter | error | error | Có | 1 | 0 |

## 5. Phân tích lỗi (Failure analysis)

1. **Lỗi công cụ / Thử lại (S05_error)**: Tool mô phỏng lỗi trong 2 lần thử đầu tiên. Node `evaluate` phát hiện chuỗi "ERROR" và điều hướng về `retry`. Ở lần thử thứ 3, tool thành công và hệ thống chuyển đến node `answer`.
2. **Hành động nhạy cảm (S04_risky)**: Các câu hỏi chứa từ khóa "refund" được đưa vào luồng `risky_action`. Sau đó, đồ thị dừng lại ở node `approval`. Trong thực tế, điều này sử dụng hàm `interrupt()`, tạm dừng thực thi cho đến khi nhận được tín hiệu phê duyệt từ bên ngoài.

## 6. Minh chứng về Tính bền vững / Khôi phục (Persistence)

Hệ thống triển khai `SqliteSaver` để lưu trữ trạng thái bền vững. Mỗi lần chạy sử dụng một `thread_id` duy nhất dựa trên ID của kịch bản. Điều này cho phép đồ thị khôi phục lại trạng thái ngay cả khi tiến trình bị khởi động lại và cho phép "du hành thời gian" (Time Travel) qua lịch sử trạng thái.

## 7. Các phần mở rộng (Extension work)

- **SQLite Checkpointer**: Triển khai thành công cơ sở dữ liệu SQLite với chế độ WAL để hỗ trợ truy cập đồng thời.
- **Human-in-the-loop (HITL)**: Tích hợp logic `interrupt()` trong node phê duyệt, cho phép đồ thị tạm dừng và chờ đợi đầu vào từ con người.

## 8. Kế hoạch cải thiện (Improvement plan)

Nếu có thêm một ngày, tôi sẽ thực hiện:
1. **Phân loại dựa trên LLM**: Thay thế việc phân loại dựa trên từ khóa trong `classify_node` bằng một lời gọi LLM có cấu trúc để xử lý các câu hỏi phức tạp và đa ý định chính xác hơn.
2. **Giao diện thời gian thực**: Xây dựng một bảng điều khiển (dashboard) bằng Streamlit để trực quan hóa trạng thái đồ thị và cung cấp giao diện cho người quản trị phê duyệt các hành động nhạy cảm.
