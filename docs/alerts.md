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
- Owner: `student-2A202602576`

## Alert 1

- Tên: `HighLatencyP95`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: `fast_successful_requests` (P95 của `response_sent.latency_ms` <= 3000ms)
- Điều kiện và thời gian duy trì: `p95(latency_ms) > 3000ms` kéo dài liên tục trong 5 phút
- Ảnh hưởng tới người dùng: Trải nghiệm phản hồi chậm, người dùng phải chờ lâu hơn 3 giây để nhận được câu trả lời từ trợ lý AI.
- Ba bước kiểm tra đầu tiên:
  1. Mở Panel Latency trên Dashboard để xác định thời điểm bắt đầu trễ và theo dõi tỷ lệ P50/P95/P99 cùng TTFT.
  2. Lọc file `data/logs.jsonl` trong khoảng thời gian có độ trễ cao, trích xuất `correlation_id` của request bị ảnh hưởng.
  3. Tìm kiếm trace trên Langfuse theo `correlation_id`, quan sát cây waterfall để xác định bước gây nghẽn (retrieval bị chậm hay generation sinh token chậm).
- Mitigation tạm thời: Rollback prompt về version ngắn hơn nếu prompt gây chậm, hoặc kích hoạt fallback tri thức cục bộ nếu RAG đang gặp sự cố mạng.
- Owner: `student-2A202602576`

## Alert 2

- Tên: `HighErrorRate`
- Severity: `critical`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: Guardrail `error_rate_pct_max` (<= 2%) và SLO thành công >= 99.5%
- Điều kiện và thời gian duy trì: `error_rate_pct > 2%` kéo dài liên tục trong 5 phút
- Ảnh hưởng tới người dùng: Yêu cầu bị gián đoạn, người dùng gặp thông báo lỗi hệ thống hoặc HTTP 500.
- Ba bước kiểm tra đầu tiên:
  1. Mở Panel Errors trên Dashboard để kiểm tra số lượng request hỏng và phân bố theo `error_type`.
  2. Mở file `data/logs.jsonl`, tìm kiếm các dòng log `event == "request_failed"`, đọc chi tiết `payload.detail` và lấy `correlation_id`.
  3. Mở trace có cùng `correlation_id` trên Langfuse để kiểm tra exception stack trace tại span tương ứng.
- Mitigation tạm thời: Kích hoạt circuit breaker chuyển sang fallback response an toàn; kiểm tra dịch vụ downstream (database, LLM provider).
- Owner: `student-2A202602576`

## Alert 3

- Tên: `LowRetrievalSuccessRate`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: Guardrail `retrieval_success_rate_pct_min` (>= 90%)
- Điều kiện và thời gian duy trì: `tool_success_rate_pct < 90%` trong vòng 5 phút
- Ảnh hưởng tới người dùng: Trợ lý AI thiếu thông tin tài liệu chuyên ngành để trả lời, chất lượng phản hồi suy giảm nghiêm trọng.
- Ba bước kiểm tra đầu tiên:
  1. Mở Panel Errors & Retrieval Success trên Dashboard để xác định tỷ lệ trích xuất tài liệu thành công.
  2. Lọc log trong `data/logs.jsonl` với điều kiện `tool_name == "retrieval"` và `tool_success == false` để lấy `correlation_id`.
  3. Kiểm tra trace trên Langfuse xem span `retrieval` bị lỗi do timeout, kết nối vector store hay cú pháp tìm kiếm.
- Mitigation tạm thời: Chuyển hướng truy vấn sang kho dữ liệu dự phòng (in-memory corpus), khởi động lại kết nối vector database.
- Owner: `student-2A202602576`