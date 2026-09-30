# Báo cáo cá nhân — K4-L3B Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Chỉ cần 3 output text và 5 ảnh runtime; dùng đường dẫn tương đối, ví dụ `evidence/03-incident-trace.png`.

## 1. Thông tin học viên

- **Họ và tên:** Lâm Hải Dương
- **MSSV:** 2A202602676
- **Lớp:** K4-L3B
- **Repository URL:** https://github.com/ElysiaTheElysier/K4-L3-DAY13-LamHaiDuong-2A202602676-Monitoring-LLMOps
- **Commit SHA cuối:** 43ffb2b
- **Challenge ID:** day13-k4-l3b-monitoring-llmops-v1
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

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:** Project trên Langfuse Cloud mang tên `day13-k4-l3b-2A202602676` được xác thực bằng cặp key cá nhân `LANGFUSE_PUBLIC_KEY` và `LANGFUSE_SECRET_KEY` trong `.env`. Mọi trace và observation đều chứa metadata `correlation_id` khớp chính xác với mã theo dõi trong `data/logs.jsonl`.
- **Cấu trúc root/retrieval/generation observations:**
  - Root trace: `day13-agent-request` bao quát toàn bộ request.
  - Root observation: `lab-agent-run` (type `agent`) quản lý quy trình điều phối của LabAgent.
  - Child observation 1: `retrieval` (type `retriever`) đo lường thời gian vector store tìm kiếm văn bản với metadata `doc_count` và `query_preview`.
  - Child observation 2: `generation` (type `generation`) đại diện cho lượt gọi LLM, ghi nhận `model="claude-sonnet-4-5"`, `usage_details` (`input`, `output`, `total`), `cost_details`, `ttft_ms` và liên kết trực tiếp với prompt template từ Langfuse.
- **Cách nối trace với log:** Cả structured log JSON (`data/logs.jsonl`) và metadata của Trace trên Langfuse đều lưu cùng trường `correlation_id` (ví dụ `req-41c5450b`). Khi phát hiện dòng log bất thường, chỉ cần sao chép `correlation_id` này và tìm kiếm trên Langfuse UI để mở ngay trace tương ứng.
- **Prompt name:** `day13-chat`
- **Version/label baseline:** Version 1 mang nhãn `baseline` và `production` (template tiêu chuẩn: `Feature={{feature}}\nDocs={{docs}}\nQuestion={{message}}`).
- **Version/label candidate:** Version 2 mang nhãn `candidate` (bổ sung ràng buộc độ dài: `Use retrieved context and keep responses concise under 30 words.`).
- **Trace ID của mỗi version:**
  - Request dùng prompt v1: `req-805997d1`
  - Request dùng prompt v2: `req-77f711b3`
  - Request sau khi rollback về v1: `req-1d4b3064`
- **Cách promote và rollback `production`:**
  - Promote: Trên Langfuse UI (hoặc qua Langfuse SDK `update_prompt`), gán nhãn `production` sang Version 2. Hệ thống tự động nhận diện version mới cho label `production`.
  - Rollback: Chuyển nhãn `production` quay trở về Version 1. Nhờ cơ chế fetch prompt động theo nhãn (`LANGFUSE_PROMPT_LABEL=production`), ứng dụng rollback ngay lập tức mà không cần sửa đổi mã nguồn hay triển khai lại dịch vụ.

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:** Dựng dashboard 6 panel chuẩn hóa theo hợp đồng cấu hình tại `config/dashboard.yaml`:
  1. *Latency*: Phân vị độ trễ P50, P95, P99 và TTFT P95 từ `response_sent.latency_ms/ttft_ms` (ngưỡng: P95 <= 3000ms).
  2. *Traffic*: Tần suất request trên phút từ `request_received` (ngưỡng: >= 1 req/min).
  3. *Errors*: Tỷ lệ lỗi toàn hệ thống và tỷ lệ thành công của truy xuất thông tin (retrieval success rate) từ `request_received`, `request_failed` và `tool_success` (ngưỡng: error rate <= 2%).
  4. *Cost*: Chi phí tích lũy theo phút và tổng chi phí tiêu thụ từ `response_sent.cost_usd` (ngưỡng: total <= 2.5 USD).
  5. *Tokens*: Tổng số lượng tokens input và output từ `response_sent.tokens_in/tokens_out` (ngưỡng: <= 50,000 tokens).
  6. *Quality*: Điểm chất lượng trung bình theo heuristic proxy từ `response_sent.quality_score` (ngưỡng: >= 0.75).
- **SLO và lý do chọn:**
  - Mục tiêu: `99.5%` request thành công và phản hồi nhanh trong vòng $\le 3000$ms trong cửa sổ 28 ngày (`window: 28d`).
  - SLI: Số `good_event` (`event == "response_sent" and latency_ms <= 3000`) chia cho tổng `total_event` (`event == "request_received"`).
  - Lý do: Đảm bảo người dùng luôn nhận được trải nghiệm mượt mà, không cảm thấy gián đoạn hay phải chờ đợi quá 3 giây khi tương tác với trợ lý AI.
- **Cách tính error budget:**
  - Error budget = $100\% - 99.5\% = 0.5\%$.
  - Nếu hệ thống nhận 10,000 request trong chu kỳ 28 ngày, số lượng request tối đa được phép bị chậm hơn 3000ms hoặc bị lỗi (500) là: $10,000 \times 0.5\% = 50$ requests. Nếu vượt quá 50 request lỗi, error budget bị cạn kiệt và đội ngũ kỹ thuật phải đóng băng tính năng mới để tập trung vá lỗi hệ thống.
- **Ba alert và runbook tương ứng:**
  1. `HighLatencyP95`: P95 latency > 3000ms trong 5 phút (Warning) $\rightarrow$ Runbook: `docs/alerts.md#alert-1`.
  2. `HighErrorRate`: Error rate > 2% hoặc Retrieval success rate < 90% trong 5 phút (Critical) $\rightarrow$ Runbook: `docs/alerts.md#alert-2`.
  3. `HighCostSpike`: Total cost > 2.5 USD hoặc output tokens > 50,000 trong 5 phút (Warning) $\rightarrow$ Runbook: `docs/alerts.md#alert-3`.

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
