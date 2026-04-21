# Báo cáo Phân tích Thất bại

## 1. Tổng quan Benchmark
- **Tổng số case:** 54
- **Pass/Fail/Error:** 51/3/0
- **Điểm LLM-Judge trung bình:** 4.87 / 5.0
- **Chỉ số retrieval:** Hit Rate 0.94, MRR 0.86
- **So với V1:**
  - Avg score: +1.37
  - Hit Rate: +0.80
  - MRR: +0.74
  - Avg latency: -2.91s
  - Estimated cost: -0.0130 USD
- **Regression gate:** RELEASE
- **Tiêu chí pass:** Judge >= 3.5 và Hit Rate = 1.0.
- **Ghi chú:** V2 đã đạt RELEASE, nhưng 3 case fail đều xoay quanh retrieval miss ở nhóm câu hỏi paraphrase/ngắn.

## 2. Phân nhóm lỗi
| Nhóm lỗi | Số lượng | Nguyên nhân dự kiến |
|----------|----------|---------------------|
| Retrieval Miss | 3 | Retriever lấy các tài liệu gần chủ đề nhưng bỏ sót document ground-truth trong top-k. |

- **Tín hiệu phụ:** 2/3 case trong nhóm phân tích có disagreement giữa các judge.
- **Kết luận nhanh:** Vấn đề còn lại của V2 không nằm ở quality tổng thể mà nằm ở độ chính xác grounding của retrieval trên một số câu hỏi ngắn hoặc paraphrase mạnh.

## 3. Phân tích 5 Whys (3 case tệ nhất)

### Case #1: case_01_02 (Retrieval Miss)
- **Câu hỏi:** Tại sao nhóm benchmark cần đo bước tìm tài liệu trước bước sinh câu trả lời?
- **Expected retrieval IDs:** `doc_eval_factory`
- **Retrieved IDs:** `doc_failure_analysis`, `doc_performance_cost`, `doc_retrieval_metrics`, `doc_safety_edge_cases`
- **Judge score:** 2.0 | **Conflict:** có
1. **Triệu chứng:** Agent không lấy được `doc_eval_factory`, nên không có đúng tài liệu giải thích mối quan hệ giữa retrieval và generation.
2. **Why 1:** Câu hỏi được diễn đạt theo paraphrase, khiến embedding kéo về các tài liệu cùng chủ đề benchmark thay vì fact gốc.
3. **Why 2:** Retriever hiện tại ưu tiên semantic similarity nhưng chưa lexical-rerank theo cụm từ khóa đặc trưng như “retrieval trước generation”.
4. **Why 3:** Top-k bị lấp bởi các tài liệu liên quan nhưng không chứa đúng ý trọng tâm cần chấm.
5. **Why 4:** Khi context không khớp, agent chọn trả lời “không đủ thông tin”, dẫn đến điểm judge thấp và retrieval fail cùng lúc.
6. **Nguyên nhân gốc:** Hệ thống vẫn thiếu bước hybrid retrieval hoặc query expansion cho các câu hỏi ngắn nhưng mang fact rất cụ thể.

### Case #2: case_13_03 (Retrieval Miss)
- **Câu hỏi:** Những mẫu lỗi nào thường được sử dụng để phân cụm kết quả thất bại?
- **Expected retrieval IDs:** `doc_failure_analysis`
- **Retrieved IDs:** `doc_safety_edge_cases`, `doc_performance_cost`, `doc_multi_judge`, `doc_eval_factory`
- **Judge score:** 3.0 | **Conflict:** có
1. **Triệu chứng:** Agent trả lời từ các tài liệu liên quan tới safety và evaluation, nhưng thiếu đúng định nghĩa “failure clustering”.
2. **Why 1:** Cụm “phân cụm kết quả thất bại” gần nghĩa với nhiều tài liệu phân tích benchmark, nên retrieval bị kéo sang các document lân cận.
3. **Why 2:** Vector search hiện tại chưa ưu tiên từ khóa định danh như “hallucination”, “retrieval miss”, “incomplete answer”, “tone mismatch”.
4. **Why 3:** Vì không có `doc_failure_analysis` trong top-k, câu trả lời bị lệch sang mô tả hard cases và retrieval error nói chung.
5. **Why 4:** Judge vẫn thấy câu trả lời có liên quan một phần nên phát sinh disagreement thay vì đồng loạt chấm fail sâu.
6. **Nguyên nhân gốc:** Thiếu cơ chế rerank theo keyword chuyên biệt cho nhóm câu hỏi về taxonomy/phân loại lỗi.

### Case #3: case_04_02 (Retrieval Miss)
- **Câu hỏi:** Tài liệu đúng xuất hiện ở vị trí càng sớm thì chỉ số nào sẽ cao hơn?
- **Expected retrieval IDs:** `doc_retrieval_metrics`
- **Retrieved IDs:** `doc_safety_edge_cases`, `doc_rag_optimizations`, `doc_regression_gate`, `doc_multi_judge`
- **Judge score:** 5.0 | **Conflict:** không
1. **Triệu chứng:** Agent vẫn trả lời đúng là MRR, nhưng không retrieve được `doc_retrieval_metrics`.
2. **Why 1:** Câu hỏi rất ngắn nên embedding lấy về các document gần nghĩa với “ranking” và “optimization” thay vì đúng tài liệu định nghĩa metric.
3. **Why 2:** Retriever chưa có lexical-rerank cho từ khóa đặc thù như “MRR” hoặc “Mean Reciprocal Rank”.
4. **Why 3:** `doc_rag_optimizations` vẫn nhắc tới reranking, đủ để agent suy luận đúng đáp án về mặt nội dung.
5. **Why 4:** Tuy nhiên benchmark yêu cầu grounded retrieval, nên câu trả lời đúng do suy luận từ tài liệu lân cận vẫn bị đánh fail.
6. **Nguyên nhân gốc:** Hệ thống chưa phân biệt đủ rõ giữa “semantic near-miss” và “ground-truth retrieval success”.

## 4. Kế hoạch cải tiến
- Bổ sung hybrid retrieval: giữ Chroma embedding để lấy recall, sau đó lexical-rerank cho các từ khóa đặc thù như MRR, Hit Rate, failure clustering.
- Tăng `fetch_k` cho câu hỏi paraphrase ngắn, nhưng chỉ rerank và cắt `top_k` sau cùng để không đội chi phí generation quá nhiều.
- Theo dõi riêng nhóm “answer đúng nhưng grounding sai” vì đây là failure mode quan trọng của benchmark hiện tại.
- Giữ fallback “không đủ thông tin” cho out-of-context và prompt injection, nhưng cần tránh abstain sai khi knowledge base đã có đáp án.
- Tiếp tục dùng regression gate để chặn release nếu hit rate, MRR, latency hoặc cost đi xuống xấu.
