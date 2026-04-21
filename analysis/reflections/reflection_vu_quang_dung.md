# Reflection - Vũ Quang Dũng

## Thông tin
- Họ và tên: Vũ Quang Dũng
- Mã sinh viên: 2A202600442

## Phân công
- Module đã đóng góp: `engine/runner.py`, phần tổng hợp latency và cost trong `main.py`
- Vai trò chính trong nhóm: phụ trách async runner, hiệu năng và thống kê chi phí

## Công việc đã thực hiện
- Tôi chuẩn hóa benchmark runner theo hướng chạy bất đồng bộ với giới hạn đồng thời để có thể chạy hết bộ 54 case trong thời gian hợp lý.
- Tôi tách và ghi lại `agent_latency_sec`, `judge_latency_sec` và `latency_sec` để nhóm nhìn rõ thời gian đang bị tiêu ở agent hay ở judge.
- Tôi tham gia phần tổng hợp token usage, estimated cost của agent và judge để báo cáo cuối có thêm góc nhìn vận hành chứ không chỉ có điểm chất lượng.

## Quyết định kỹ thuật
- Vấn đề khó nhất đã giải quyết: đảm bảo benchmark không chết toàn bộ khi một case hoặc một request API bị lỗi tạm thời.
- Trade-off đã chấp nhận: tôi ưu tiên continue-on-error và ghi nhận kết quả từng case thay vì dừng toàn pipeline ngay khi có exception. Cách này thực dụng hơn nhưng làm phần phân tích lỗi phải kỹ hơn.

## Bài học rút ra
- Điều tôi học được: tối ưu chất lượng mà không đo latency và cost thì chưa đủ để ra quyết định release trong thực tế.
- Điều sẽ làm khác đi ở lần tiếp theo: tôi muốn bổ sung retry có kiểm soát và thống kê p95 latency để phần performance đầy đủ hơn.
