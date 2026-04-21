# Reflection - Bùi Đức Thắng

## Thông tin
- Họ và tên: Bùi Đức Thắng
- Mã sinh viên: 2A202600002

## Phân công
- Module đã đóng góp: `agent/real_agent.py`, `README.md`, `.env.example`, `analysis/failure_analysis.md`
- Vai trò chính trong nhóm: phụ trách real agent, tài liệu cấu hình và báo cáo phân tích lỗi

## Công việc đã thực hiện
- Tôi xây dựng `RealEvaluationAgent` để benchmark có một agent thật dùng OpenRouter, retrieval trên knowledge base và generation từ model API thật.
- Tôi cập nhật README và `.env.example` để nhóm cấu hình được ba model judge, model baseline/candidate và embedding model qua OpenRouter mà không phải dò lại toàn bộ repo.
- Tôi hoàn thiện `failure_analysis.md` theo dữ liệu benchmark thật, gồm phân nhóm lỗi, 5 Whys và kế hoạch cải tiến thay vì chỉ để template mô tả chung.

## Quyết định kỹ thuật
- Vấn đề khó nhất đã giải quyết: làm sao để real agent dùng API thật nhưng vẫn đủ an toàn cho quá trình demo và debug khi môi trường chạy có thể thiếu key hoặc lỗi mạng.
- Trade-off đã chấp nhận: tôi giữ fallback và prompt cấu trúc tương đối đơn giản để agent ổn định trước, thay vì tối ưu quá mạnh cho chất lượng trong từng case riêng lẻ.

## Bài học rút ra
- Điều tôi học được: tài liệu cấu hình và failure analysis là phần rất quan trọng để biến một repo kỹ thuật thành một bài nộp có thể giải thích và bảo vệ được.
- Điều sẽ làm khác đi ở lần tiếp theo: tôi muốn thêm một script smoke test riêng cho OpenRouter để kiểm tra key, model và quota trước khi chạy full benchmark.
