# Reflection - Nguyễn Tiến Đạt

## Thông tin
- Họ và tên: Nguyễn Tiến Đạt
- Mã sinh viên: 2A202600217

## Phân công
- Module đã đóng góp: `engine/llm_judge.py`
- Vai trò chính trong nhóm: phụ trách multi-judge consensus và judge thật qua OpenRouter

## Công việc đã thực hiện
- Tôi tích hợp ba judge thật qua OpenRouter, gồm GPT, Claude và Gemini, để benchmark có đa góc nhìn thay vì phụ thuộc vào một model chấm duy nhất.
- Tôi thiết kế logic tổng hợp kết quả với `individual_scores`, `individual_labels`, `individual_reasons`, `agreement_rate`, `cohens_kappa` và cờ `conflict_detected`.
- Tôi thêm cơ chế fallback offline và phần parse/phòng lỗi để pipeline vẫn chạy được khi một judge trả về định dạng không chuẩn hoặc API gặp sự cố.

## Quyết định kỹ thuật
- Vấn đề khó nhất đã giải quyết: làm sao để ba model khác nhau chấm theo cùng một rubric và trả về dữ liệu đủ ổn định để tổng hợp hàng loạt.
- Trade-off đã chấp nhận: tôi dùng cách tổng hợp theo median và conflict detection thay vì một tầng judge meta-model phức tạp hơn. Cách này đơn giản nhưng minh bạch và dễ debug hơn.

## Giải trình kỹ thuật
- Khái niệm kỹ thuật tôi hiểu rõ: Cohen's Kappa dùng để đo mức đồng thuận giữa các judge sau khi đã loại trừ phần đồng thuận ngẫu nhiên. Vì vậy nó mạnh hơn việc chỉ nhìn agreement rate thô, nhất là khi nhiều case dễ có thể khiến các model “đồng ý” với nhau một cách bề mặt.
- Position Bias liên quan thế nào tới lab: judge LLM có thể bị ảnh hưởng bởi cách trình bày, độ dài answer hoặc nguồn xuất hiện sớm trong context, nên việc chấm không hoàn toàn độc lập với ranking. Nếu context đầu danh sách lệch, cả answer lẫn judge đều có thể bị kéo theo một hướng thiên lệch.

## Bài học rút ra
- Điều tôi học được: trong bài toán eval, độ ổn định và khả năng truy vết của hệ thống judge quan trọng gần ngang với độ mạnh của model chấm.
- Điều sẽ làm khác đi ở lần tiếp theo: tôi muốn tinh chỉnh prompt judge kỹ hơn để giảm disagreement ở các case biên và tăng độ phân hóa điểm số.
