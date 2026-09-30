# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert mẫu để tham khảo

Ví dụ dưới đây minh họa mức độ cụ thể cần có. Học viên không cần copy nguyên, nhưng ba alert trong bài nộp nên rõ ràng tương tự: điều kiện là gì, kéo dài bao lâu, ảnh hưởng tới user ra sao và người trực cần kiểm tra gì trước.

- Tên: `HighLatencyP95`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: latency P95 của `response_sent.latency_ms`
- Điều kiện và thời gian duy trì: `p95(latency_ms) > 3000ms` trong 5 phút
- Ảnh hưởng tới người dùng: người dùng phải chờ lâu hơn trước khi nhận câu trả lời
- Ba bước kiểm tra đầu tiên:
  1. Mở dashboard latency để xác nhận P95/P99 và khoảng thời gian tăng.
  2. Lọc `data/logs.jsonl` trong khoảng đó, lấy một `correlation_id` có `latency_ms` cao.
  3. Mở trace cùng `correlation_id` trên Langfuse, so sánh các span chính để xác định bước nào bất thường.
- Mitigation tạm thời: dựa trên evidence thực tế để rollback prompt, khôi phục cấu hình liên quan, tắt practice scenario hoặc giảm tải khi demo.
- Owner: `student-2A202602676`

<a id="alert-1"></a>
## Alert 1: HighLatencyP95

- Tên: `HighLatencyP95`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: Primary SLO `fast_successful_requests` (ngưỡng latency <= 3000ms, target 99.5%)
- Điều kiện và thời gian duy trì: `p95(latency_ms) > 3000ms` duy trì liên tục trong 5 phút
- Ảnh hưởng tới người dùng: Trải nghiệm tương tác bị chậm trễ, thời gian chờ phản hồi vượt quá 3 giây gây gián đoạn công việc của người dùng
- Ba bước kiểm tra đầu tiên:
  1. Mở Panel 1 (Latency) trên Dashboard để đối chiếu P50/P95/P99 và xác định thời điểm bắt đầu tăng vọt.
  2. Mở file `data/logs.jsonl`, lọc các log `response_sent` có `latency_ms > 2500` và trích xuất `correlation_id` đại diện.
  3. Tìm kiếm `correlation_id` trên Langfuse Traces để mở waterfall view; kiểm tra xem độ trễ phát sinh ở span `retrieval` (vector store nghẽn/timeout) hay span `generation` (LLM quá tải/sinh dài).
- Mitigation tạm thời:
  1. Nếu sự cố do RAG/retrieval (như kịch bản `rag_slow`), kích hoạt fallback retrieval từ cache hoặc tạm thời tắt retrieval phụ.
  2. Nếu do prompt mới làm LLM sinh dài dòng, rollback prompt production về version ổn định trước đó trên Langfuse.
- Owner: `student-2A202602676`

<a id="alert-2"></a>
## Alert 2: HighErrorRate

- Tên: `HighErrorRate`
- Severity: `critical`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: Guardrail `error_rate_pct_max: 2%` và `retrieval_success_rate_pct_min: 90%`
- Điều kiện và thời gian duy trì: Tỷ lệ lỗi toàn hệ thống `error_rate > 2%` hoặc `retrieval_success_rate < 90%` kéo dài trong 5 phút
- Ảnh hưởng tới người dùng: Người dùng nhận thông báo lỗi 500 hoặc câu trả lời không đầy đủ do truy xuất thất bại
- Ba bước kiểm tra đầu tiên:
  1. Mở Panel 3 (Errors) trên Dashboard để xem tỷ lệ lỗi và breakdown theo `error_type` (HTTP 500, tool failure, timeout).
  2. Tra cứu `data/logs.jsonl` tìm các event `request_failed` hoặc log có `level="error"` / `tool_success=false` để lấy stack trace và `correlation_id`.
  3. Mở Trace trên Langfuse kiểm tra span báo lỗi đỏ (ví dụ span `retrieval` bị ngoại lệ kết nối hoặc `tool_fail`).
- Mitigation tạm thời:
  1. Kích hoạt circuit breaker để ngắt phụ thuộc ngoài đang bị lỗi.
  2. Nếu lỗi phát sinh sau đợt cập nhật code/cấu hình, rollback ngay về bản release hoặc commit ổn định gần nhất.
- Owner: `student-2A202602676`

<a id="alert-3"></a>
## Alert 3: HighCostSpike

- Tên: `HighCostSpike`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: Guardrail `daily_cost_usd_max: 2.5` và giới hạn tokens output trong cửa sổ 5 phút
- Điều kiện và thời gian duy trì: `sum(cost_usd) > 2.50 USD` hoặc `sum(tokens_out) > 50,000` trong 5 phút
- Ảnh hưởng tới người dùng: Ngân sách tài khoản LLM có nguy cơ cạn kiệt, dẫn đến dịch vụ bị nhà cung cấp cắt quota đột ngột
- Ba bước kiểm tra đầu tiên:
  1. Mở Panel 4 (Cost) và Panel 5 (Tokens) trên Dashboard để xác định model nào đang tiêu tốn nhiều chi phí nhất.
  2. Kiểm tra `data/logs.jsonl` tìm các request có `tokens_out` hoặc `cost_usd` tăng đột biến; kiểm tra xem có hiện tượng lặp lại prompt injection hay prompt template bị phình to.
  3. Mở Trace trên Langfuse kiểm tra prompt version đang chạy ở `generation` span; đối chiếu prompt labels.
- Mitigation tạm thời:
  1. Giảm `max_tokens` của model hoặc kích hoạt rate limiting tạm thời cho các user có tần suất gọi cao.
  2. Rollback prompt về version ngắn gọn có giới hạn từ ngữ (ví dụ v1 hoặc prompt có conciseness constraint).
- Owner: `student-2A202602676`
