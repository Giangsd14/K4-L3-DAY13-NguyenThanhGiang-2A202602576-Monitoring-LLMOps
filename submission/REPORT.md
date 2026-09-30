# Báo cáo cá nhân — K4-L3B Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:** Nguyễn Thành Giang
- **MSSV:** 2A202602576
- **Lớp:** K4-L3B
- **Repository URL:** https://github.com/vinuin/K4-L3-DAY13-NguyenThanhGiang-2A202602576-Monitoring-LLMOps
- **Commit SHA cuối:** 29ddb22
- **Challenge ID:** `day13-k4-l3b-monitoring-llmops-v1`
- **Tên project Langfuse cá nhân:** `day13-k4-l3b-2A202602576`

## 2. Evidence index

Điền đúng đường dẫn tới evidence thực tế. Có thể đổi tên hoặc dùng nhiều ảnh nếu cần.

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | `evidence/01-pytest.png` |
| Log validator | `evidence/02-log-validator.png` |
| Dashboard validator | `evidence/03-dashboard-validator.png` |
| Structured log | `evidence/04-structured-log.png` |
| PII redaction | `evidence/05-pii-redaction.png` |
| Trace list | `evidence/06-trace-list.png` |
| Trace waterfall | `evidence/07-trace-waterfall.png` |
| Trace metadata | `evidence/08-trace-metadata.png` |
| Prompt versions | `evidence/09-prompt-versions.png` |
| Prompt rollback | `evidence/10-prompt-rollback.png` |
| Dashboard runtime | `evidence/11-dashboard-overview.png` |
| Incident metric | `evidence/12-incident-metric.png` |
| Incident log | `evidence/13-incident-log.png` |
| Incident trace | `evidence/14-incident-trace.png` |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 30/100 | 100/100 | Đạt điểm tuyệt đối, correlation ID truyền chuẩn, log enrichment đầy đủ |
| `validate_dashboard.py` | 6/6 | 6/6 | Đạt chuẩn 6/6 panel hợp đồng |
| `pytest` | 22 passed | 25 passed | Đã bổ sung unit tests cho CCCD, Credit Card, Passport |
| Số traces hợp lệ | 0 | 14+ | Tự sinh trên project Langfuse cá nhân `day13-k4-l3b-2A202602576` |
| Số PII leak | 0 | 0 | Scrubbing hoạt động hiệu quả trước khi ghi log/trace |
| Latency P95 / TTFT P95 | 1551ms / 50ms | 152ms / 50ms | Độ trễ ổn định dưới ngưỡng 3000ms |
| Retrieval success rate | 100% | 100% | Tỷ lệ trích xuất tài liệu thành công đạt 100% ở baseline |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** Trong `app/middleware.py`, tại đầu hàm `dispatch`, middleware gọi `clear_contextvars()` để xóa context cũ tránh rò rỉ giữa các request. Sau đó trích xuất `x-request-id` từ header; nếu không có thì sinh mã ngẫu nhiên dạng `req-<8-hex>` (`req-{uuid.uuid4().hex[:8]}`). ID này được bind vào contextvars qua `bind_contextvars(correlation_id=correlation_id)` và lưu vào `request.state.correlation_id`. Khi trả response, middleware bổ sung `x-request-id` và `x-response-time-ms` vào response headers.
- **Các metadata được ghi vào structured log:** Gồm `ts`, `level`, `service`, `event`, `correlation_id`, `user_id_hash` (băm sha256 12 ký tự), `session_id`, `feature`, `model`, `env`, cùng các trường metrics `latency_ms`, `ttft_ms`, `tokens_in`, `tokens_out`, `cost_usd`, `quality_score`, `tool_name`, `tool_success`.
- **Cách bảo đảm PII được scrub trước khi ghi:** Trong `app/logging_config.py`, bộ xử lý `scrub_event` đệ quy (`_scrub_value`) trên toàn bộ chuỗi ký tự trong `event_dict` bằng các regex pattern trong `app/pii.py` (email, phone VN, CCCD 12 số, credit card 16 số, passport). Processor này được đăng ký trong pipeline structlog ngay trước `JsonlFileProcessor` và `JSONRenderer`, bảo đảm dữ liệu nhạy cảm được thay thế thành `[REDACTED_...]` trước khi ghi file `data/logs.jsonl` hoặc xuất console.
- **Cách kiểm chứng kết quả:** Chạy `python scripts/validate_logs.py` đạt 100/100 điểm: không có PII leak, 0 missing required fields, 0 missing enrichment fields.

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:** Toàn bộ traces được gửi trực tiếp đến project cá nhân `day13-k4-l3b-2A202602576` (Org: `VinUni_AI2026_Lab13`) trên Langfuse Cloud (`https://cloud.langfuse.com`) qua cặp API keys được cấu hình trong `.env`.
- **Cấu trúc root/retrieval/generation observations:** Sử dụng Langfuse SDK v4 với cấu trúc cây phân cấp:
  - Root observation: `lab-agent-run` (type `agent`) ghi nhận toàn bộ vòng đời thực thi của agent.
  - Child observation 1: `retrieval` (type `span`) đo thời gian trích xuất tài liệu từ corpus.
  - Child observation 2: `generation` (type `generation`) đo thời gian gọi LLM, ghi nhận `model`, `prompt`, `usage_details` (`tokens_in`, `tokens_out`) và `cost_details`.
- **Cách nối trace với log:** Sử dụng chung trường `correlation_id`. Khi middleware sinh `req-<8-hex>`, ID này được truyền vào `agent.run(..., correlation_id=...)` và gán vào metadata của trace qua `propagate_attributes(metadata={"correlation_id": correlation_id, ...})`.
- **Prompt name:** `day13-chat`
- **Version/label baseline:** Version 1 (labels: `baseline`, `production`)
- **Version/label candidate:** Version 2 (labels: `candidate`)
- **Trace ID của mỗi version:**
  - Version 1 (`baseline`/`production`): `609e3f0b69c890a94f25bfb59022e596` (và `66a586c4466a9712b7e55510b51bb53e` sau rollback)
  - Version 2 (`candidate`/`promoted`): `094cc2e05639ff29fafe4e0bd49c5a07` (và `745ebad94d44ef361f1712a11ffe6cc1` khi promoted)
- **Cách promote và rollback `production`:**
  - Để promote Version 2 lên Production: Gọi `lf.update_prompt(name="day13-chat", version=2, new_labels=["candidate", "production"])`.
  - Để rollback về Version 1: Gọi `lf.update_prompt(name="day13-chat", version=1, new_labels=["baseline", "production"])`. Ứng dụng tự động nhận diện version mới của label `production` từ Langfuse mà không cần sửa code.

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:** Dựng Web Dashboard tại route `/dashboard` và API `/api/dashboard` (đọc trực tiếp từ `data/logs.jsonl` trong cửa sổ 60 phút, tự refresh mỗi 30s), bao gồm 6 panel:
  1. *Latency & TTFT*: P50, P95, P99 và TTFT P95 (đơn vị: ms, threshold P95 <= 3000ms).
  2. *Traffic*: Request count và rate per minute (đơn vị: requests_per_minute, threshold >= 1.0).
  3. *Errors & Retrieval*: Error rate % và Retrieval success rate % (đơn vị: percent, threshold <= 2% và >= 90%).
  4. *Cost Over Time*: Tổng chi phí USD tích lũy (đơn vị: usd, threshold <= $2.50).
  5. *Input & Output Tokens*: Tổng token in và token out (đơn vị: tokens, threshold <= 50,000).
  6. *Quality Proxy*: Điểm chất lượng trung bình (đơn vị: score_0_to_1, threshold >= 0.75).
- **SLO và lý do chọn:** SLO `fast_successful_requests` với mục tiêu 99.5% trong cửa sổ 28 ngày (`target_percent: 99.5`, điều kiện: `response_sent` có `latency_ms <= 3000`). Lý do chọn: Đảm bảo người dùng cuối nhận được phản hồi nhanh và chính xác trong hơn 99.5% trường hợp, phản ánh đúng tail latency của hệ thống.
- **Cách tính error budget:** Với target 99.5%, error budget là `100% - 99.5% = 0.5%`. Nếu hệ thống nhận 10,000 request trong 28 ngày, tối đa chỉ được phép có `10,000 * 0.5% = 50` request bị lỗi hoặc có độ trễ vượt quá 3000ms.
- **Ba alert và runbook tương ứng:** Cấu hình trong `config/alert_rules.yaml` và `docs/alerts.md`:
  1. `HighLatencyP95`: Cảnh báo khi P95 latency > 3000ms kéo dài 5 phút (Warning).
  2. `HighErrorRate`: Cảnh báo khi error rate > 2% kéo dài 5 phút (Critical).
  3. `LowRetrievalSuccessRate`: Cảnh báo khi tỷ lệ retrieval thành công < 90% kéo dài 5 phút (Warning).

## 7. Điều tra challenge

- **Challenge ID:** `day13-k4-l3b-monitoring-llmops-v1`
- **Khoảng thời gian điều tra:** `14:02:00 - 14:05:00 UTC+7 (07:02:00 - 07:05:00 UTC) ngày 30/09/2026`
- **Triệu chứng từ metrics:** Trên Panel Latency của Dashboard, P95 latency tăng đột biến từ mức bình thường (~150ms) vọt lên **2684ms**, vượt qua ngưỡng cảnh báo `latency_threshold_ms: 2000` của challenge và kích hoạt badge `ALERT`. Trong khi đó, TTFT P95 vẫn ở mức tối ưu **52ms**, chứng minh mô hình AI không bị nghẽn ở bước sinh token đầu tiên.
- **Log line và correlation ID liên quan:**
  - `correlation_id`: `req-4b837db8` (thuộc session `k4-l3b-challenge-s04`, user `k4-l3b-u04`, feature `monitoring`).
  - Dòng log hoàn chỉnh:
    `{"service": "api", "latency_ms": 2684, "ttft_ms": 52, "tokens_in": 36, "tokens_out": 98, "cost_usd": 0.001578, "quality_score": 0.9, "tool_name": "retrieval", "tool_success": true, "payload": {"answer_preview": "Starter answer. You should improve this output logic and add better quality chec..."}, "event": "response_sent", "env": "dev", "session_id": "k4-l3b-challenge-s04", "user_id_hash": "c3a24a72d92a", "feature": "monitoring", "model": "claude-sonnet-4-5", "correlation_id": "req-4b837db8", "level": "info", "ts": "2026-09-30T07:02:25.865703Z"}`
- **Trace ID và span gây ảnh hưởng:**
  - `trace_id`: `3fbb1efdef406d9c3cf3d3259cea8e4b` trên Langfuse Cloud (project `day13-k4-l3b-2A202602576`).
  - Cây quan sát chỉ ra span **`retrieval`** kéo dài bất thường tới **2.50s (2500ms)** chiếm 94.2% tổng thời gian thực thi (2.654s) của trace. Trong khi đó, span **`generation`** chỉ mất **0.15s** (hoạt động bình thường).
- **Root cause:** Sự cố nằm ở tầng trích xuất tài liệu tri thức (Vector Store / RAG retrieval latency degradation) do kịch bản `rag_slow` gây ra độ trễ 2.5s trong bước `retrieve()`, khiến toàn bộ request bị chậm nghiêm trọng dù mô hình sinh câu trả lời vẫn xử lý rất nhanh.
- **Fix action:** Đã thực hiện vô hiệu hóa sự cố bằng lệnh `python scripts/inject_incident.py --disable`, đưa API server về trạng thái vận hành ổn định (`latency_ms` quay về ~150ms).
- **Preventive measure:**
  1. Áp dụng timeout giới hạn nghiêm ngặt (ví dụ `timeout = 1.5s`) cho hàm truy xuất tài liệu vector database, kết hợp circuit breaker chuyển sang fallback response khi vector database bị chậm.
  2. Giám sát cảnh báo `HighLatencyP95` (P95 > 3000ms trong 5m) qua Slack `#k4-l3b-alerts` để can thiệp kịp thời.
  3. Cài đặt bộ đệm (Semantic Cache / In-memory caching) cho các câu hỏi phổ biến để giảm thiểu các truy vấn trùng lặp tới vector store.

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:** Thiết kế middleware tự động bind correlation ID ngay từ tầng HTTP và inject vào cả 2 kênh giám sát song song (Structured Structlog và Langfuse Trace Metadata). Quyết định này giúp kết nối liền mạch giữa log và trace, cho phép điều tra sự cố tức thì từ log line tìm ra đúng trace waterfall mà không cần phụ thuộc vào một công cụ đơn lẻ.
- **Một lỗi/blocker đã gặp:** Gặp lỗi 401 Unauthorized khi kết nối Langfuse Cloud ban đầu do cấu hình nhầm `LANGFUSE_BASE_URL` trỏ về region US (`https://us.cloud.langfuse.com`) và có dấu ngoặc kép bọc chuỗi, trong khi project thực tế nằm tại region EU (`https://cloud.langfuse.com`).
- **Cách tìm nguyên nhân và xử lý:** Dùng script Python gửi request trực tiếp đến endpoint `/api/public/projects` của cả hai host, phát hiện host EU trả về HTTP 200 kèm project ID chính xác. Sau đó chuẩn hóa lại biến môi trường trong `.env` và khởi động lại API server.
- **Cách hiểu luồng Metrics → Logs → Traces:**
  - *Metrics*: Cung cấp bức tranh tổng thể ở tầng cao (Dashboard) để phát hiện triệu chứng (suy giảm chất lượng, tăng độ trễ, tăng tỷ lệ lỗi) và khoanh vùng thời điểm sự cố.
  - *Logs*: Thu hẹp phạm vi vào các request cụ thể bị ảnh hưởng trong khung giờ đó, cung cấp context chi tiết và mã `correlation_id`.
  - *Traces*: Dùng `correlation_id` mở cây waterfall chi tiết của request để xác định chính xác span nào (retrieval hay generation) và câu lệnh nào gây ra nghẽn/lỗi.
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:**
  - Prompt versioning cho phép quản lý sự thay đổi của prompt như mã nguồn phần mềm, gán nhãn `production`/`candidate` để deploy an toàn.
  - Rollback tức thì mà không cần rebuild/re-deploy mã nguồn khi prompt mới gây hồi quy chất lượng hoặc tăng vọt chi phí.
  - Giám sát token & cost giúp phát hiện sớm các cuộc tấn công prompt injection hoặc vòng lặp vô tận làm cạn kiệt ngân sách.
- **Điều quan trọng nhất đã học:** Hiểu sâu sắc triết lý Observability trong hệ thống LLM: không chỉ giám sát tài nguyên máy chủ truyền thống mà cần giám sát chất lượng suy luận, số lượng token, chi phí và truy vết phân tán giữa RAG và LLM.
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:** Cần tiếp tục theo dõi khi tải thực tế biến động lớn và bổ sung thêm các bộ đánh giá tự động (LLM-as-a-judge) nâng cao.

## 9. Checklist trước khi nộp

- [ ] Kết quả và evidence thuộc commit SHA cuối.
- [ ] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [ ] Incident evidence nối đúng metric → log → trace.
- [ ] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [ ] Repository chạy lại được theo README.
- [ ] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [ ] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
