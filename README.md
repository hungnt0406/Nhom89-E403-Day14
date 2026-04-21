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

### 1. Chuẩn bị môi trường

Khuyến nghị dùng virtual environment để tách dependency cho bài lab:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Nếu dùng Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Cấu hình `.env`

Copy file mẫu:

```bash
cp .env.example .env
```

Thiết lập tối thiểu trong `.env`:

```bash
OPENROUTER_API_KEY=sk-or-...
JUDGE_MODE=auto
```

Các model mặc định giá vừa phải hiện dùng trong repo:

```bash
OPENROUTER_GPT_MODEL=openai/gpt-4.1-mini
OPENROUTER_CLAUDE_MODEL=anthropic/claude-3.5-haiku
OPENROUTER_GEMINI_MODEL=google/gemini-2.5-flash
OPENROUTER_EMBEDDING_MODEL=baai/bge-m3
OPENROUTER_AGENT_MODEL=google/gemini-2.5-flash
```

Giải thích ngắn:
- `JUDGE_MODE=auto`: có API key thì gọi OpenRouter, không có thì fallback offline.
- `OPENROUTER_EMBEDDING_MODEL`: model embedding dùng để index/query ChromaDB.
- `OPENROUTER_AGENT_MODEL`: model generation cho `RealEvaluationAgent`.

### 3. Chạy nhanh theo đúng thứ tự

```bash
# 1. Sinh lại golden dataset (khuyến nghị chạy trước benchmark)
python data/synthetic_gen.py

# 2. Chạy benchmark V1 vs V2
python main.py

# 3. Kiểm tra file nộp bài
python check_lab.py
```

Sau khi chạy `python main.py`, hệ thống sẽ tạo hoặc cập nhật:
- `reports/summary.json`
- `reports/benchmark_results.json`
- `analysis/failure_analysis.md`

### 4. Chạy real agent riêng lẻ

Hỏi một câu rồi thoát:

```bash
python agent/real_agent.py --question "Vì sao phải đánh giá retrieval trước generation?"
```

Chạy với model khác:

```bash
python agent/real_agent.py --model openai/gpt-4.1-mini --question "MRR là gì?"
```

Chạy interactive chat:

```bash
python agent/real_agent.py
```

### 5. Các mode benchmark đang hỗ trợ

Mặc định trong code:
- `Agent_V1_Base`: agent mô phỏng (`simulated`)
- `Agent_V2_Optimized`: agent thật (`real`)

Có thể đổi bằng `.env`.

#### Mode A: Baseline mô phỏng, candidate là agent thật

```bash
BENCHMARK_BASELINE_AGENT=simulated
BENCHMARK_CANDIDATE_AGENT=real
OPENROUTER_AGENT_MODEL=google/gemini-2.5-flash
OPENROUTER_EMBEDDING_MODEL=baai/bge-m3
```

#### Mode B: Cả V1 và V2 đều là agent thật

```bash
BENCHMARK_BASELINE_AGENT=real
BENCHMARK_CANDIDATE_AGENT=real
BENCHMARK_BASELINE_REAL_MODEL=openai/gpt-4.1-mini
BENCHMARK_CANDIDATE_REAL_MODEL=google/gemini-2.5-flash
```

#### Mode C: Cố tình làm V1 yếu hơn để chứng minh V2 cải thiện

```bash
BENCHMARK_BASELINE_AGENT=real
BENCHMARK_CANDIDATE_AGENT=real
BENCHMARK_BASELINE_REAL_MODEL=openai/gpt-4.1-mini
BENCHMARK_CANDIDATE_REAL_MODEL=google/gemini-2.5-flash
BENCHMARK_BASELINE_RETRIEVAL_MODE=degraded
BENCHMARK_BASELINE_FETCH_K=5
BENCHMARK_BASELINE_TOP_K=3
BENCHMARK_BASELINE_EXTRA_DELAY_SEC=0.25
BENCHMARK_CANDIDATE_RETRIEVAL_MODE=normal
BENCHMARK_CANDIDATE_TOP_K=4
```

### 6. Retrieval hiện đang chạy như thế nào

- Vector DB dùng `ChromaDB` với thư mục persist cục bộ tại `.chroma/`
- Dữ liệu được index từ `data/knowledge_base.py`
- Embedding được gọi qua OpenRouter bằng `OPENROUTER_EMBEDDING_MODEL`
- Nếu thiếu key hoặc lỗi mạng, retrieval sẽ fallback sang lexical search để pipeline không bị gãy

Lưu ý: hiện tại index đang ở mức **document-level**, tức là mỗi document trong knowledge base là một record trong Chroma. Sau khi retrieve document, agent mới rerank tiếp ở mức fact bên trong document.

### 7. Kiểm tra trước khi nộp

Nên chạy lại đầy đủ chuỗi sau trước khi nộp:

```bash
python data/synthetic_gen.py
python main.py
python check_lab.py
```

Checklist file đầu ra cần có:
- `reports/summary.json`
- `reports/benchmark_results.json`
- `analysis/failure_analysis.md`
- `analysis/reflections/reflection_*.md`

## ⚠️ Lưu ý quan trọng

- `data/golden_set.jsonl` có thể sinh lại bất cứ lúc nào bằng `python data/synthetic_gen.py`.
- File `.env` chứa API key, không được push lên GitHub.
- Nếu muốn kết quả benchmark sát nhất với phần báo cáo, nên giữ nguyên `.env` trong suốt một lần chạy `main.py`.
- `check_lab.py` chỉ là validator nhanh; quyết định chấm điểm thực tế vẫn phụ thuộc vào chất lượng report, reflection và logic benchmark.

---
*Chúc nhóm bạn xây dựng được một Evaluation Factory thực sự mạnh mẽ!*
