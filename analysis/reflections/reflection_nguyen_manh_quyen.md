# Reflection - Nguyễn Mạnh Quyền

## Thông tin
- Họ và tên: Nguyễn Mạnh Quyền
- Mã sinh viên: 2A202600481

## Phân công
- Module đã đóng góp: `engine/text_utils.py`, `engine/retrieval_eval.py`, `engine/vector_store.py`, phần retrieval trong `agent/main_agent.py`
- Vai trò chính trong nhóm: phụ trách retrieval stack, vector DB và retrieval evaluation

## Công việc đã thực hiện
- Tôi xây dựng các hàm xử lý văn bản dùng chung như tokenize, token overlap và token F1 để phục vụ cho retrieval evaluation và heuristic scoring.
- Tôi triển khai lại phần chấm retrieval để tính Hit Rate và MRR từ `expected_retrieval_ids` và `retrieved_ids` thực tế, thay cho số giả lập của khung code ban đầu.
- Tôi tích hợp ChromaDB và embedding qua OpenRouter trong `engine/vector_store.py`, đồng thời nối phần retrieval này vào agent mô phỏng để benchmark phản ánh kiến trúc RAG thật hơn.

## Quyết định kỹ thuật
- Vấn đề khó nhất đã giải quyết: làm sao để retrieval vừa có vector search thật, vừa vẫn có fallback đủ ổn định để nhóm debug được khi API hoặc embedding lỗi.
- Trade-off đã chấp nhận: tôi giữ thêm lexical fallback bên cạnh vector retrieval. Cách này không “thuần vector DB” hoàn toàn nhưng giúp pipeline không gãy khi môi trường chạy thiếu mạng hoặc key.

## Bài học rút ra
- Điều tôi học được: nếu retrieval không được đo độc lập thì rất khó xác định agent sai do search, do grounding hay do generation.
- Điều sẽ làm khác đi ở lần tiếp theo: tôi muốn thêm hybrid reranking và synonym expansion để giảm semantic near-miss ở các câu hỏi paraphrase ngắn.
