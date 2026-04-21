# 🚀 Lab Day 14: AI Evaluation Factory (Team Edition)

## 🎯 Tổng quan
"Nếu bạn không thể đo lường nó, bạn không thể cải thiện nó." — Nhiệm vụ của nhóm bạn là xây dựng một **Hệ thống đánh giá tự động** chuyên nghiệp để benchmark AI Agent. Hệ thống này phải chứng minh được bằng con số cụ thể: Agent đang tốt ở đâu và tệ ở đâu.

---

## 🕒 Lịch trình thực hiện (4 Tiếng)
- **Giai đoạn 1 (45'):** Thiết kế Golden Dataset & Script SDG. Tạo ra ít nhất 50 test cases chất lượng.
- **Giai đoạn 2 (90'):** Phát triển Eval Engine (RAGAS, Custom Judge) & Async Runner.
- **Giai đoạn 3 (60'):** Chạy Benchmark, Phân cụm lỗi (Failure Clustering) & Phân tích "5 Whys".
- **Giai đoạn 4 (45'):** Tối ưu Agent dựa trên kết quả & Hoàn thiện báo cáo nộp bài.

---

## 🛠️ Các nhiệm vụ chính (Expert Mission)

### 1. Retrieval & SDG (Nhóm Data)
- **Retrieval Eval:** Tính toán Hit Rate và MRR cho Vector DB. Bạn phải chứng minh được Retrieval stage hoạt động tốt trước khi đánh giá Generation.
- **SDG:** Tạo 50+ cases, bao gồm cả Ground Truth IDs của tài liệu để tính Hit Rate.

### 2. Multi-Judge Consensus Engine (Nhóm AI/Backend)
- **Consensus logic:** Sử dụng ít nhất 2 model Judge khác nhau. 
- **Calibration:** Tính toán hệ số đồng thuận (Agreement Rate) và xử lý xung đột điểm số tự động.

### 3. Regression Release Gate (Nhóm DevOps/Analyst)
- **Delta Analysis:** So sánh kết quả của Agent phiên bản mới với phiên bản cũ.
- **Auto-Gate:** Viết logic tự động quyết định "Release" hoặc "Rollback" dựa trên các chỉ số Chất lượng/Chi phí/Hiệu năng.

---

## 📤 Danh mục nộp bài (Submission Checklist)
Nhóm nộp 1 đường dẫn Repository (GitHub/GitLab) chứa:
1. [ ] **Source Code**: Toàn bộ mã nguồn hoàn chỉnh.
2. [ ] **Reports**: File `reports/summary.json` và `reports/benchmark_results.json` (được tạo ra sau khi chạy `main.py`).
3. [ ] **Group Report**: File `analysis/failure_analysis.md` (đã điền đầy đủ).
4. [ ] **Individual Reports**: Các file `analysis/reflections/reflection_[Tên_SV].md`.

---

## 🏆 Bí kíp đạt điểm tuyệt đối (Expert Tips)

### ✅ Đánh giá Retrieval (15%)
Nhóm nào chỉ đánh giá câu trả lời mà bỏ qua bước Retrieval sẽ không thể đạt điểm tối đa. Bạn cần biết chính xác chunk nào đang gây ra lỗi Hallucination.

### ✅ Multi-Judge Reliability (20%)
Việc chỉ tin vào một Judge (ví dụ GPT-4o) là một sai lầm trong sản phẩm thực tế. Hãy chứng minh hệ thống của bạn khách quan bằng cách so sánh nhiều Judge model và tính toán độ tin cậy của chúng.

### ✅ Tối ưu hiệu năng & Chi phí (15%)
Hệ thống Expert phải chạy cực nhanh (Async) và phải có báo cáo chi tiết về "Giá tiền cho mỗi lần Eval". Hãy đề xuất cách giảm 30% chi phí eval mà không giảm độ chính xác.

### ✅ Phân tích nguyên nhân gốc rễ (Root Cause) (20%)
Báo cáo 5 Whys phải chỉ ra được lỗi nằm ở đâu: Ingestion pipeline, Chunking strategy, Retrieval, hay Prompting.

---

## 🔧 Hướng dẫn chạy

```bash
# 1. Cài đặt dependencies
pip install -r requirements.txt

# 1.5. Cấu hình OpenRouter để dùng 3 judge API thật (khuyến nghị)
# Tạo file .env với ít nhất:
# OPENROUTER_API_KEY=sk-or-...
# JUDGE_MODE=openrouter
#
# Retrieval hiện dùng vector DB thật:
# - Embedding model qua OpenRouter: OPENROUTER_EMBEDDING_MODEL=baai/bge-m3
# - Index cục bộ: ChromaDB PersistentClient tại thư mục `.chroma/`
#
# Mặc định code sẽ dùng 3 model judge giá vừa phải qua OpenRouter:
# - openai/gpt-4.1-mini
# - anthropic/claude-3.5-haiku
# - google/gemini-2.5-flash
#
# Có thể override bằng:
# OPENROUTER_GPT_MODEL=...
# OPENROUTER_CLAUDE_MODEL=...
# OPENROUTER_GEMINI_MODEL=...
# OPENROUTER_EMBEDDING_MODEL=baai/bge-m3
#
# Nếu để JUDGE_MODE=auto thì có key sẽ gọi OpenRouter, không có key sẽ fallback offline.

# 2. Tạo Golden Dataset (chạy trước khi benchmark)
python data/synthetic_gen.py

# 3. Chạy Benchmark & tạo reports
python main.py

# 4. Kiểm tra định dạng trước khi nộp
python check_lab.py

# 5. Chạy real agent liên quan đến lab
python agent/real_agent.py --question "Vi sao phai danh gia retrieval truoc generation?"

# Hoặc vào chế độ chat
python agent/real_agent.py
```

Mặc định benchmark hiện tại chạy:
- `Agent_V1_Base`: agent mô phỏng để làm baseline
- `Agent_V2_Optimized`: `RealEvaluationAgent` dùng OpenRouter

Cả hai agent hiện truy hồi qua ChromaDB thật, dùng embedding model từ OpenRouter.

Có thể đổi trong `.env`:
```bash
BENCHMARK_BASELINE_AGENT=simulated
BENCHMARK_CANDIDATE_AGENT=real
OPENROUTER_AGENT_MODEL=google/gemini-2.5-flash
OPENROUTER_EMBEDDING_MODEL=baai/bge-m3
```

Nếu muốn benchmark cả 2 phiên bản đều là agent thật, đặt:
```bash
BENCHMARK_BASELINE_AGENT=real
BENCHMARK_CANDIDATE_AGENT=real
BENCHMARK_BASELINE_REAL_MODEL=google/gemini-2.5-flash
BENCHMARK_CANDIDATE_REAL_MODEL=openai/gpt-4.1-mini
```

---

## ⚠️ Lưu ý quan trọng
- **Bắt buộc** chạy `python data/synthetic_gen.py` trước để tạo file `data/golden_set.jsonl`. File này không được commit sẵn trong repo.
- Trước khi nộp bài, hãy chạy `python check_lab.py` để đảm bảo định dạng dữ liệu đã chuẩn. Bất kỳ lỗi định dạng nào dẫn đến việc script chấm điểm tự động không chạy được sẽ bị trừ 5 điểm thủ tục.
- File `.env` chứa API Key **KHÔNG** được push lên GitHub.
- `agent/real_agent.py` là agent thật dùng OpenRouter để trả lời các câu hỏi liên quan trực tiếp tới lab AI Evaluation.
- Retrieval hiện không còn là lexical matching thuần nữa; hệ thống dùng ChromaDB local kết hợp embedding model qua OpenRouter. Nếu thiếu `OPENROUTER_API_KEY` hoặc lỗi mạng, retrieval sẽ fallback sang chế độ lexical để tránh làm vỡ pipeline.

---
*Chúc nhóm bạn xây dựng được một Evaluation Factory thực sự mạnh mẽ!*
