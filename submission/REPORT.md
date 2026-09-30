# Báo cáo cá nhân — K4-L3B Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Chỉ cần 3 output text và 5 ảnh runtime; dùng đường dẫn tương đối, ví dụ `evidence/03-incident-trace.png`.

## 1. Thông tin học viên

- **Họ và tên:** Lâm Hải Dương
- **MSSV:** 2A202602676
- **Lớp:** K4-L3B
- **Repository URL:** https://github.com/ElysiaTheElysier/K4-L3-DAY13-LamHaiDuong-2A202602676-Monitoring-LLMOps
- **Commit SHA cuối:** 2fa17ac
- **Challenge ID:** day13-k4-l3b-monitoring-llmops-v1
- **Tên project Langfuse cá nhân:** `day13-k4-l3b-2A202602676`

## 2. Evidence index

Danh mục toàn bộ evidence bao gồm 3 output text và đầy đủ bộ 14 ảnh runtime:

| STT | Evidence | Nội dung kiểm chứng | Đường dẫn |
|---|---|---|---|
| 01 | Test cuối | Lệnh `pytest -q`, 23/23 tests passed | `evidence/01-pytest.png` (và `evidence/pytest.txt`) |
| 02 | Log validator | Kết quả `validate_logs.py` đạt 100/100, 0 PII leak | `evidence/02-log-validator.png` (và `evidence/log-validator.txt`) |
| 03 | Dashboard validator | Kết quả `validate_dashboard.py` đủ 6/6 panels | `evidence/03-dashboard-validator.png` (và `evidence/dashboard-validator.txt`) |
| 04 | Structured log | Log JSON đầy đủ correlation ID, latency, model, feature | `evidence/04-structured-log.png` |
| 05 | PII redaction | Log đầu ra đã che PII email, phone VN, CCCD, thẻ | `evidence/05-pii-redaction.png` |
| 06 | Trace list | Project cá nhân và tối thiểu 10 traces trên Langfuse | `evidence/06-trace-list.png` |
| 07 | Trace waterfall | Waterfall tree đủ 3 cấp: root, retrieval, generation | `evidence/07-trace-waterfall.png` |
| 08 | Trace metadata | Metadata chi tiết: correlation ID, model, token, cost | `evidence/08-trace-metadata.png` |
| 09 | Prompt versions | Quản lý prompt `day13-chat` có version v1 và v2 | `evidence/09-prompt-versions.png` |
| 10 | Prompt rollback | Quá trình promote v2 và rollback về v1 | `evidence/10-prompt-rollback.png` |
| 11 | Dashboard runtime | Dashboard 6 panel với time range và threshold | `evidence/11-dashboard-overview.png` |
| 12 | Incident metric | Metric bất thường (spike latency > 2500ms) của incident | `evidence/12-incident-metric.png` |
| 13 | Incident log | Dòng log sự cố có correlation ID `req-45007b41` | `evidence/13-incident-log.png` |
| 14 | Incident trace | Trace sự cố thấy span `retrieval` bị nghẽn 2.51s | `evidence/14-incident-trace.png` |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 30/100 | 100/100 | Đạt toàn bộ tiêu chí: JSON schema, correlation ID propagation, log enrichment và PII scrubbing |
| `validate_dashboard.py` | 6/6 panel hợp lệ | 6/6 panel hợp lệ | Đạt cấu trúc 6 panels theo schema version 1 |
| `pytest` | 22 passed | 22 passed | Toàn bộ 22 unit tests chạy thành công |
| Số traces hợp lệ | 10 traces (chỉ root observation) | 69+ traces (đầy đủ root + child spans) | Có đầy đủ child spans `retrieval` và `generation` với metadata, token usage, cost |
| Số PII leak | 0 leak | 0 leak | Không có PII rò rỉ nguyên văn trong log (đã scrub trước khi ghi file) |
| Latency P95 / TTFT P95 | 1261.0 ms / 50.0 ms | 152.0 ms / 50.0 ms (bình thường) | P95 latency ổn định ở mức 152ms khi bình thường, tăng lên >2650ms khi có incident |
| Retrieval success rate | 100% | 100% | Tỷ lệ truy xuất thành công đạt 100% |

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

- **Challenge ID:** `day13-k4-l3b-monitoring-llmops-v1`
- **Khoảng thời gian điều tra:** `2026-09-30 11:12:53 – 11:13:23 (04:12:53Z – 04:13:23Z UTC)`
- **Triệu chứng từ metrics:** Phân vị độ trễ Latency P95 và P99 tăng vọt bất thường từ mức baseline ~151ms lên trên 2650ms (lên tới 7965ms – 13272ms khi chịu tải 5 request đồng thời). Ngưỡng cảnh báo `latency_threshold: 2000ms` và SLO latency threshold `3000ms` đều bị vi phạm trong khoảng thời gian diễn ra sự cố.
- **Log line và correlation ID liên quan:** Dòng 54 trong `data/logs.jsonl` ghi nhận response:
  ```json
  {"service": "api", "latency_ms": 2652, "ttft_ms": 50, "tokens_in": 36, "tokens_out": 113, "cost_usd": 0.001803, "quality_score": 0.9, "tool_name": "retrieval", "tool_success": true, "payload": {"answer_preview": "Starter answer. You should improve this output logic and add better quality chec..."}, "event": "response_sent", "model": "claude-sonnet-4-5", "user_id_hash": "c3a24a72d92a", "correlation_id": "req-45007b41", "env": "dev", "feature": "monitoring", "session_id": "k4-l3b-challenge-s04", "level": "info", "ts": "2026-09-30T04:13:02.290177Z"}
  ```
  Correlation ID đại diện: `req-45007b41` (thuộc chuỗi 5 requests challenge: `req-45007b41`, `req-3bbbb917`, `req-f1d6153d`, `req-7640d9c3`, `req-7e9c7e9e`).
- **Trace ID và span gây ảnh hưởng:** Trace ID `b702ba8705b8249a6f5ae27ff30fcf90` trên Langfuse tương ứng với request `req-45007b41` (User: `c3a24a72d92a`, Session `k4-l3b-challenge-s04`). Khi mở chi tiết waterfall tree, root observation `lab-agent-run` mất tổng cộng 2.66s, trong đó span `retrieval` tiêu tốn tới 2.51s (chiếm ~95% tổng thời gian thực thi) trong khi span `generation` chỉ mất 0.15s ($0.001803). Do đó span gây ảnh hưởng trực tiếp chính là `retrieval`.
- **Root cause:** Kịch bản sự cố `rag_slow` được kích hoạt trên feature `monitoring`. Trong quá trình truy vấn tài liệu bổ sung, tầng RAG/Vector store bị delay nhân tạo 2.5 giây (`time.sleep(2.5)`), gây tắc nghẽn toàn bộ pipeline xử lý của agent.
- **Fix action:**
  1. Tắt cờ sự cố bằng cách gửi request POST tới `/incidents/rag_slow/disable` (chạy script `python scripts/inject_incident.py --disable`).
  2. Bổ sung timeout giới hạn cho bước retrieval (ví dụ `asyncio.wait_for(retrieval_func(), timeout=1.5)`) kèm fallback trả về tài liệu cache hoặc thông báo giảm tải để bảo vệ latency toàn hệ thống.
  3. Cấu hình circuit breaker để ngắt tạm thời vector store nếu phát hiện tỷ lệ timeout vượt quá ngưỡng cho phép.
- **Preventive measure:**
  1. Kích hoạt rule cảnh báo `HighLatencyP95` (`config/alert_rules.yaml`) để nhận diện ngay khi P95 latency vượt 3000ms trong 5 phút.
  2. Xây dựng runbook chi tiết tại `docs/alerts.md#alert-1` để hướng dẫn on-call engineer quy trình tra cứu correlation_id và cô lập span retrieval bị nghẽn.
  3. Bổ sung integration test mô phỏng vector store trễ/timeout trong CI/CD để đảm bảo fallback hoạt động trước khi release tính năng.

> Gợi ý cách viết ngắn, không thay cho evidence thực tế: "Metric cho thấy `[latency/error/cost/quality]` bất thường trong `[khoảng thời gian]`. Log line `[event]` có `correlation_id=[...]` đại diện cho request bị ảnh hưởng. Trace cùng `correlation_id` cho thấy span `[retrieval/generation/prompt/tool]` có dấu hiệu `[chậm/lỗi/token tăng]`. Root cause là `[nguyên nhân suy ra từ evidence]`. Fix action là `[hành động khôi phục]`; preventive measure là `[alert/runbook/test/guardrail để ngăn tái diễn]`."

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:** Thiết kế cơ chế bọc `@observe` riêng biệt cho 2 hàm `_retrieve` (as retriever) và `_generate` (as generation) trong `LabAgent` thay vì chỉ observe một hàm chung. Lý do: Giúp cô lập chính xác thời gian và tài nguyên của từng công đoạn (retrieval vs generation), phân định rõ độ trễ do vector store hay do mô hình sinh ngôn ngữ gây ra, đồng thời liên kết được prompt template và tính toán chi phí token độc lập.
- **Một lỗi/blocker đã gặp:** Trong quá trình ghi log có cấu trúc, các trường nhạy cảm như email hay thẻ tín dụng nằm sâu bên trong dictionary lồng nhau của `payload` có nguy cơ bị rò rỉ nếu hàm regex scrubbing chỉ duyệt ở tầng ngoài cùng.
- **Cách tìm nguyên nhân và xử lý:** Chạy `python scripts/validate_logs.py` và phát hiện các trường hợp PII lồng sâu không được scrub. Xử lý bằng cách viết hàm đệ quy `scrub_dict()` trong processor `scrub_event` để duyệt qua toàn bộ các key-value của dictionary lồng nhau hoặc list lồng nhau trước khi structlog serialize thành JSON.
- **Cách hiểu luồng Metrics → Logs → Traces:**
  - *Metrics*: Cung cấp bức tranh tổng thể ở tầng cao nhất (tín hiệu cảnh báo "Hệ thống đang có vấn đề gì và ở đâu?" - ví dụ P95 latency vọt lên >2500ms).
  - *Logs*: Thu hẹp phạm vi ("Yêu cầu cụ thể nào bị ảnh hưởng?" - lọc các log line có latency cao, lấy ra `correlation_id` đại diện như `req-45007b41`).
  - *Traces*: Phân tích sâu nguyên nhân gốc rễ ở mức vi mô ("Thành phần bên trong nào bị lỗi?" - dùng `correlation_id` tra cứu waterfall tree để định vị chính xác span `retrieval` bị trễ 2.5s).
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:**
  - *Prompt Versioning & Rollback*: Cho phép A/B testing, quản lý vòng đời prompt như mã nguồn và hoàn nguyên tức thì khi prompt mới làm giảm chất lượng hoặc tăng token bất thường mà không cần redeploy code.
  - *Token & Cost Tracking*: Giúp kiểm soát ngân sách vận hành, phát hiện prompt injection hay vòng lặp sinh text vô hạn.
  - *SLO & Error Budget*: Đặt ra ranh giới định lượng giữa tốc độ phát triển tính năng và độ ổn định của dịch vụ, bảo vệ trải nghiệm của người dùng cuối.
- **Điều quan trọng nhất đã học:** Hiểu sâu sắc triết lý Observability trong LLMOps: Một hệ thống AI production không thể chỉ dựa vào kết quả test cục bộ, mà cần một hệ sinh thái giám sát hoàn chỉnh kết hợp giữa Structured Logging (với PII scrubbing), Distributed Tracing (Langfuse) và Metric Dashboards/SLO để phản ứng nhanh trước các sự cố runtime.
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:** Các mô hình LLM và RAG hiện tại trong bài lab đang chạy dưới dạng mock/giả lập; trong môi trường production thực tế cần tích hợp thêm semantic caching (Redis) và rate limiter phân tán để tối ưu chi phí và độ trễ hơn nữa.

## 9. Checklist trước khi nộp

- [x] Kết quả và evidence thuộc commit SHA cuối.
- [x] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [x] Có đúng 3 file text và 5 ảnh runtime theo hướng dẫn.
- [x] Incident evidence nối đúng metric → log → trace.
- [x] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [x] Repository chạy lại được theo README.
- [x] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [x] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.

## 10. Điểm thưởng (Bonus Items)

Hệ thống đã triển khai đầy đủ cả 3 hạng mục Bonus theo đúng [docs/RUBRIC.md](file:///c:/Ki_OJT/Labs/Lab_13/K4-L3-DAY13-LamHaiDuong-2A202602676-Monitoring-LLMOps/docs/RUBRIC.md#h-bonus--tối-đa-10-điểm) (tối đa +10 điểm thưởng):

1. **Automation (+5 điểm):**
   - **Secret & PII Scanner:** Triển khai script tự động hóa `scripts/scan_secrets_pii.py` quét toàn bộ 60+ files trong dự án, đối chiếu regex để ngăn chặn việc commit lộ khóa API (`sk-`, `ghp_`, `AKIA`) hoặc rò rỉ dữ liệu PII thô trước khi nộp bài.
   - **CI Pipeline:** Thiết lập GitHub Actions Workflow tại `.github/workflows/ci.yml` tự động chạy test suite (`pytest`), kiểm tra hợp đồng dashboard (`validate_dashboard.py`) và quét bảo mật (`scan_secrets_pii.py`) trên mỗi commit push lên `main`.

2. **Audit Logging độc lập (+5 điểm):**
   - Triển khai module `app/audit.py` và test case `tests/test_audit.py` (23 passed) để ghi nhận nhật ký kiểm toán độc lập ra `data/audit.jsonl` cho các hành động quản trị nhạy cảm (`prompt_promoted`, `prompt_rolled_back`, `incident_enabled`, `incident_disabled`).
   - Xây dựng tài liệu chi tiết tại `docs/audit_logging.md` bao gồm: Schema JSON version 1.0, chính sách lưu trữ (Hot 90 ngày, Cold 365 ngày, WORM/Object Lock immutability) và các câu lệnh truy vấn mẫu bằng `jq` và Python.

3. **Cost Optimization qua Prompt Engineering (+5 điểm):**
   - Đánh giá Before / After trên cùng workload:
     - **Before (Prompt v1 - Baseline):** Không có ràng buộc độ dài, mô hình sinh trung bình 151 – 164 output tokens với chi phí ~$0.002568 / request.
     - **After (Prompt v2 - Candidate):** Bổ sung ràng buộc độ dài (*"keep responses concise under 30 words"*), mô hình cô đọng câu trả lời còn 88 – 113 output tokens với chi phí giảm còn ~$0.001422 – $0.001803 / request.
     - **Hiệu quả:** Tiết kiệm ~35% – 45% chi phí token và giảm tải độ trễ suy luận của LLM trong khi vẫn giữ nguyên chất lượng câu trả lời.
