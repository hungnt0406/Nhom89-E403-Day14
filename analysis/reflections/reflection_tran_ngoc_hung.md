# Reflection - Trần Ngọc Hùng

## Thông tin
- Họ và tên: Trần Ngọc Hùng
- Mã sinh viên: 2A202600429

## Phân công
- Module đã đóng góp: `main.py`, `check_lab.py`
- Vai trò chính trong nhóm: phụ trách orchestration benchmark, regression gate và validator

## Công việc đã thực hiện
- Tôi ghép các thành phần dataset, retrieval, agent, judge và runner thành một pipeline benchmark chạy end-to-end cho cả V1 và V2.
- Tôi thiết kế phần regression report để so sánh baseline và candidate theo nhiều chiều như quality, hit rate, MRR, latency và cost, từ đó đưa ra quyết định `RELEASE` hoặc `ROLLBACK`.
- Tôi siết lại `check_lab.py` để script kiểm tra thực sự fail khi thiếu field quan trọng, thiếu số lượng case hoặc còn placeholder trong báo cáo.

## Quyết định kỹ thuật
- Vấn đề khó nhất đã giải quyết: làm sao để V2 thật sự tốt hơn V1 trên số liệu benchmark, thay vì chỉ khác nhau về mô tả hoặc thay model một cách hình thức.
- Trade-off đã chấp nhận: tôi dùng threshold cố định và cấu hình qua biến môi trường để release gate minh bạch, dễ giải thích, dù chưa linh hoạt bằng một policy engine riêng.

## Bài học rút ra
- Điều tôi học được: benchmark chỉ có giá trị khi phần orchestration và release gate đủ rõ để người khác đọc vào là hiểu vì sao nên release hay rollback.
- Điều sẽ làm khác đi ở lần tiếp theo: tôi muốn tách policy threshold ra file cấu hình riêng để việc thử nghiệm nhiều chiến lược gate thuận tiện hơn.
