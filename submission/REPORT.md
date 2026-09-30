# Báo cáo cá nhân — K4-L3B Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Chỉ cần 3 output text và 5 ảnh runtime; dùng đường dẫn tương đối, ví dụ `evidence/03-incident-trace.png`.

## 1. Thông tin học viên

- **Họ và tên:** Lâm Hải Dương
- **MSSV:** 2A202602676
- **Lớp:** K4-L3B
- **Repository URL:** https://github.com/ElysiaTheElysier/K4-L3-DAY13-LamHaiDuong-2A202602676-Monitoring-LLMOps
- **Commit SHA cuối:** 61a34f827748393ced851ea7c9b412dd53dced23
- **Challenge ID:** Đang chờ release từ Lab Coach (CP3)
- **Tên project Langfuse cá nhân:** `day13-k4-l3b-2A202602676`

## 2. Evidence index

Giữ đúng ba output text và năm ảnh dưới đây. Không tách thêm ảnh; nếu cần giải thích, ghi bằng chữ trong các mục sau.

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | `evidence/pytest.txt` |
| Log validator | `evidence/log-validator.txt` |
| Dashboard validator | `evidence/dashboard-validator.txt` |
| Structured log + incident log | `evidence/01-incident-log.png` |
| Trace list | `evidence/02-trace-list.png` |
| Trace waterfall + metadata + incident trace | `evidence/03-incident-trace.png` |
| Prompt versions + promote/rollback | `evidence/04-prompt-versioning.png` |
| Dashboard + incident metric | `evidence/05-dashboard-incident.png` |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 30/100 | 100/100 | Đạt toàn bộ tiêu chí: JSON schema, correlation ID propagation, log enrichment và PII scrubbing |
| `validate_dashboard.py` | 6/6 panel hợp lệ | | Đạt cấu trúc 6 panels theo schema version 1 |
| `pytest` | 22 passed | | Toàn bộ 22 unit tests baseline chạy thành công |
| Số traces hợp lệ | 10 traces (chỉ root observation) | | Mới có root observation `lab-agent-run`, chưa có child span |
| Số PII leak | 0 leak | 0 leak | Không có PII rò rỉ nguyên văn trong log (đã scrub trước khi ghi file) |
| Latency P95 / TTFT P95 | 1261.0 ms / 50.0 ms | | Độ trễ baseline với FakeLLM và RAG giả lập |
| Retrieval success rate | 100% | | Chưa có lỗi tool hay timeout trong retrieval |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** Trong `CorrelationIdMiddleware` (`app/middleware.py`), trước mỗi request gọi `clear_contextvars()` để xóa context cũ tránh rò rỉ giữa các request. Kiểm tra header `x-request-id` từ client, nếu có thì giữ nguyên, nếu không thì sinh mã ngẫu nhiên theo định dạng `req-<8-hex>` (`f"req-{uuid.uuid4().hex[:8]}"`). Sau đó gọi `bind_contextvars(correlation_id=correlation_id)` và gán vào `request.state.correlation_id`. Khi trả response, gắn `x-request-id` và `x-response-time-ms` vào headers.
- **Các metadata được ghi vào structured log:** Các trường chung bao gồm `ts` (ISO UTC), `level`, `service`, `event`, `correlation_id`. Ngữ cảnh nghiệp vụ được enrich tại `app/main.py` gồm `user_id_hash` (băm sha256 12 ký tự hex từ user_id), `session_id`, `feature`, `model`, `env`. Các trường đo lường khi hoàn tất gồm `latency_ms`, `ttft_ms`, `tokens_in`, `tokens_out`, `cost_usd`, `quality_score`, `tool_name`, `tool_success` và payload đã scrub (`message_preview`, `answer_preview`).
- **Cách bảo đảm PII được scrub trước khi ghi:** Đăng ký processor `scrub_event` trong danh sách processors của `structlog.configure()` ngay trước `JsonlFileProcessor()` và `JSONRenderer()`. Khi ghi log, processor duyệt qua payload và các trường text, áp dụng các regex pattern trong `PII_PATTERNS` (`app/pii.py`) để che các định dạng nhạy cảm (Email, Phone VN, CCCD 12 số, Credit card) thành dạng `[REDACTED_<TYPE>]` trước khi dữ liệu được serialize thành JSON và ghi xuống file `data/logs.jsonl`.
- **Cách kiểm chứng kết quả:** Chạy `python scripts/load_test.py` với tập dữ liệu mẫu chứa email, số điện thoại, thẻ tín dụng trong `data/sample_queries.jsonl`. Sau đó chạy `python scripts/validate_logs.py` đạt điểm tuyệt đối 100/100: 0 records missing required fields, 0 records missing enrichment, 10 unique correlation IDs, 0 potential PII leaks. Đồng thời chạy toàn bộ test suite `pytest` vượt qua 22/22 tests.

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:**
- **Cấu trúc root/retrieval/generation observations:**
- **Cách nối trace với log:**
- **Prompt name:**
- **Version/label baseline:**
- **Version/label candidate:**
- **Trace ID của mỗi version:**
- **Cách promote và rollback `production`:**

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:**
- **SLO và lý do chọn:**
- **Cách tính error budget:**
- **Ba alert và runbook tương ứng:**

> Ví dụ cách viết error budget: "SLO 99.5% trong 28 ngày nghĩa là error budget 0.5%. Nếu workload có 10,000 request thì tối đa 50 request được phép lỗi hoặc chậm hơn ngưỡng SLO."

## 7. Điều tra challenge

- **Challenge ID:**
- **Khoảng thời gian điều tra:**
- **Triệu chứng từ metrics:**
- **Log line và correlation ID liên quan:**
- **Trace ID và span gây ảnh hưởng:**
- **Root cause:**
- **Fix action:**
- **Preventive measure:**

> Gợi ý cách viết ngắn, không thay cho evidence thực tế: "Metric cho thấy `[latency/error/cost/quality]` bất thường trong `[khoảng thời gian]`. Log line `[event]` có `correlation_id=[...]` đại diện cho request bị ảnh hưởng. Trace cùng `correlation_id` cho thấy span `[retrieval/generation/prompt/tool]` có dấu hiệu `[chậm/lỗi/token tăng]`. Root cause là `[nguyên nhân suy ra từ evidence]`. Fix action là `[hành động khôi phục]`; preventive measure là `[alert/runbook/test/guardrail để ngăn tái diễn]`."

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:**
- **Một lỗi/blocker đã gặp:**
- **Cách tìm nguyên nhân và xử lý:**
- **Cách hiểu luồng Metrics → Logs → Traces:**
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:**
- **Điều quan trọng nhất đã học:**
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:**

## 9. Checklist trước khi nộp

- [ ] Kết quả và evidence thuộc commit SHA cuối.
- [ ] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [ ] Có đúng 3 file text và 5 ảnh runtime theo hướng dẫn.
- [ ] Incident evidence nối đúng metric → log → trace.
- [ ] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [ ] Repository chạy lại được theo README.
- [ ] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [ ] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
