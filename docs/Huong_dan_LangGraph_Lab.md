# Hướng Dẫn Tối Ưu Giải Quyết Bài Lab: LangGraph Agentic Orchestration

Chào bạn, để đạt được điểm tối đa (90-100 điểm) cho bài Lab này, chúng ta cần hoàn thành các bước một cách tuần tự, đảm bảo đúng kiến trúc, quản lý state chính xác, và tránh các lỗi phổ biến (pitfalls) đã được đề cập trong tài liệu. 

Dưới đây là hướng dẫn từng bước chi tiết (step-by-step).

---

## Bước 1: Khởi tạo và thiết lập môi trường

Trước tiên, hãy đảm bảo môi trường phát triển của bạn đã được cài đặt đúng các dependencies:
```bash
# Sử dụng venv
python -m venv .venv
source .venv/Scripts/activate  # trên Windows hoặc Mac/Linux

# Hoặc dùng conda
# conda activate ai-lab

# Cài đặt project với dev dependencies
pip install -e '.[dev]'

# Chạy test kiểm tra ban đầu (lúc này test có thể fail ở một số chỗ do chưa code)
make test
```

---

## Bước 2: Hoàn thiện Phase 1 - Core Graph (45 điểm)

Mục tiêu là xây dựng và hoàn thành logic của các **Node** và **Router** để xử lý đúng 5 loại luồng: `simple`, `tool`, `missing_info`, `risky`, `error`.

### 1. `src/langgraph_agent_lab/state.py`
Cấu trúc state hiện tại đã khá tốt vì đã sử dụng `Annotated[list, add]` cho các trường cần lưu lịch sử (như `messages`, `tool_results`, `events`, `errors`). 
- Đảm bảo trường `evaluation_result` (kiểu `str | None`) đã có mặt trong schema để làm checkpoint cho retry loop (Đã được định nghĩa sẵn, không cần thêm sửa gì).

### 2. `src/langgraph_agent_lab/nodes.py`
Bạn cần điền logic vào các vị trí `TODO(student)`. Đặc biệt chú ý:

*   **`classify_node`**: Đây là node quan trọng nhất. Cần tránh các xung đột từ khóa (ví dụ "Check order status" vừa có "check" vừa có "order").
    *Lưu ý: Ưu tiên keyword theo thứ tự: Risky -> Tool -> Missing Info -> Error.*
*   **`ask_clarification_node`**: Hãy tạo câu hỏi yêu cầu cụ thể (ví dụ: "Can you provide the missing context or item ID?").
*   **`tool_node`**: Cập nhật logic tăng số đếm attempt khi gọi vào tool để xử lý fallback/retry.
*   **`evaluate_node`**: Là nút check điều kiện "done?". Kiểm tra phần tử cuối của mảng `state.get("tool_results")`. Nếu có chữ `"ERROR"` thì set `evaluation_result = "needs_retry"`, ngược lại là `"success"`.
*   **`retry_or_fallback_node`**: Đếm số attempt hiện tại (được truyền trong biến `attempt`) và ghi nhận vào `errors`.

### 3. `src/langgraph_agent_lab/routing.py`
Đảm bảo định tuyến chính xác theo state:

*   **`route_after_classify`**: Map các `Route` sang đúng các node: `"simple"` -> `"answer"`, `"tool"` -> `"tool"`, `"missing_info"` -> `"clarify"`, `"risky"` -> `"risky_action"`, `"error"` -> `"retry"`.
*   **`route_after_retry`**: Nếu `state["attempt"] >= state["max_attempts"]`, trả về `"dead_letter"`, ngược lại trả về `"tool"`.
*   **`route_after_evaluate`**: Nếu `state["evaluation_result"] == "needs_retry"`, trả về `"retry"`, ngược lại trả về `"answer"`.
*   **`route_after_approval`**: Trả về `"tool"` nếu được approval, nếu không thì `"clarify"`.

### 4. `src/langgraph_agent_lab/graph.py`
Code kiến trúc trong file `graph.py` cơ bản đã được nối chính xác theo mô hình trong `README.md`. Hãy kiểm tra lại để chắc chắn các edge và node đều đã được thêm bằng `graph.add_node` và `graph.add_edge` / `graph.add_conditional_edges`. 

*(Graph hiện tại của bạn đã nối đúng các luồng này, không cần phải sửa đổi trừ khi bạn làm thêm tính năng nâng cao).*

---

## Bước 3: Hoàn thiện Phase 2 - Persistence (15 điểm)

**Pitfall cần tránh**: Trong `README` đã nhắc rất kỹ, API của bản `langgraph-checkpoint-sqlite` v3 không dùng `from_conn_string` mà dùng kết nối trực tiếp.
Bạn cần sửa file `src/langgraph_agent_lab/persistence.py`:

```python
# Thay vì dùng:
# return SqliteSaver.from_conn_string(database_url or "checkpoints.db")

# Hãy dùng cách chuẩn sau cho SQLite:
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver

# check_same_thread=False rất quan trọng với Langgraph
conn = sqlite3.connect(database_url or "checkpoints.db", check_same_thread=False)
return SqliteSaver(conn)
```

---

## Bước 4: Chạy Đánh giá, Lấy Metrics và Báo cáo (35 điểm)

1. **Chạy kịch bản (Scenarios)**
   Chạy lệnh sau để bot tự kiểm tra trên 7 scenarios ở `data/sample/scenarios.jsonl`:
   ```bash
   make run-scenarios
   ```
   Nếu thành công, file `outputs/metrics.json` sẽ được tạo ra.

2. **Kiểm tra tính hợp lệ của Metrics**
   ```bash
   make grade-local
   ```
   Lệnh này xác thực schema của JSON xem bạn có đủ điểm chuẩn chưa.

3. **Viết Báo cáo**
   Mở file `reports/lab_report.md` và viết tài liệu bao gồm:
   - Kiến trúc bạn đã thiết kế (tóm tắt quá trình đi từ Intake -> Classify -> Các nodes).
   - Metrics phân tích (tỷ lệ thành công, các route đã đi qua).
   - Phân tích Failure: Giải thích node `dead_letter` hoặc HITL (Human In The Loop) hoạt động ra sao.
   - Các phương án tối ưu (ví dụ: dùng LLM Classifier thay cho keyword matcher).

---

## Bước 5: Bonus Extensions (Để ăn điểm 90+)

Chọn 1 hoặc 2 tính năng sau để được cộng điểm:

1. **Crash Recovery (Dễ làm nhất):**
   - Bạn đã làm ở bước 3 (SqliteSaver). Bằng việc chứng minh file `checkpoints.db` lưu trữ trạng thái, bạn đã đạt một bonus. Ghi rõ phần này vào Report.

2. **Real HITL (Human-in-the-loop):**
   - Mở terminal và export biến môi trường:
     - Linux/Mac: `export LANGGRAPH_INTERRUPT=true`
     - Windows (Powershell): `$env:LANGGRAPH_INTERRUPT="true"`
   - Lúc này code ở `approval_node` sẽ kích hoạt hàm `interrupt()`. Nếu bạn show cho giảng viên trong lúc Demo cách hệ thống dừng lại chờ bạn input, bạn sẽ có điểm tuyệt đối!

3. **Vẽ biểu đồ Mermaid:**
   - Tạo một script python nhỏ (ví dụ `draw_graph.py`), gọi `build_graph()` và xuất ra ảnh:
     ```python
     from langgraph_agent_lab.graph import build_graph
     graph = build_graph()
     print(graph.get_graph().draw_mermaid())
     ```
   - Copy nội dung xuất ra vào file markdown report của bạn.

---

### Chú Ý Cuối Cùng
1. **Kiểm tra kỹ Keyword Regex:** Hãy chắc chắn `"can you fix it?"` match vào `missing_info` do có từ `"it"`. Dùng thao tác tách chữ theo khoảng trắng (word boundaries).
2. **Luôn Finalize:** Tất cả mọi luồng (kể cả error, dead_letter) đều **bắt buộc phải chạy về `finalize` node** trước khi end. Nếu quên nối về finalize, agent sẽ treo vô hạn.

Chúc bạn hoàn thành bài Lab với điểm tuyệt đối! Nếu bạn muốn tôi trực tiếp chỉnh sửa các file mã nguồn (như `nodes.py` hay `routing.py`), hãy báo cho tôi nhé!
