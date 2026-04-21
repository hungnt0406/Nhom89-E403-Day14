# Reflection - Dương Trịnh Hoài An

## Thông tin
- Họ và tên: Dương Trịnh Hoài An
- Mã sinh viên: 2A202600050

## Phân công
- Module đã đóng góp: `data/knowledge_base.py`, `data/synthetic_gen.py`
- Vai trò chính trong nhóm: phụ trách thiết kế knowledge base và golden dataset

## Công việc đã thực hiện
- Tôi chuẩn hóa knowledge base của bài lab thành các document nhỏ, có chủ đề rõ ràng như retrieval metrics, multi-judge, regression gate, failure analysis và safety edge cases.
- Tôi xây dựng bộ sinh dữ liệu để tạo 54 test case có cấu trúc thống nhất, bao gồm `case_id`, `expected_answer`, `expected_retrieval_ids`, độ khó và loại câu hỏi.
- Tôi bổ sung các case paraphrase, hard case, out-of-context và prompt injection để benchmark không chỉ đo fact recall mà còn đo độ bền của agent.

## Quyết định kỹ thuật
- Vấn đề khó nhất đã giải quyết: làm sao để dataset vừa đủ đa dạng để benchmark, vừa có ground truth retrieval rõ ràng để tính Hit Rate và MRR.
- Trade-off đã chấp nhận: tôi chọn knowledge base nội bộ có cấu trúc xác định thay vì dùng nguồn ngoài. Cách này giảm độ mở của dữ liệu nhưng giúp benchmark ổn định, dễ tái lập và dễ chấm.

## Bài học rút ra
- Điều tôi học được: chất lượng benchmark phụ thuộc rất nhiều vào độ rõ ràng của ground truth, không chỉ ở phần answer mà cả ở phần retrieval.
- Điều sẽ làm khác đi ở lần tiếp theo: tôi muốn bổ sung thêm case đa lượt và case có thông tin mâu thuẫn để kiểm tra agent sát thực tế hơn.
