"""Deterministic knowledge base used by the offline evaluation lab."""

from typing import Dict, Iterable, List


KNOWLEDGE_BASE: List[Dict] = [
    {
        "id": "doc_eval_factory",
        "title": "AI Evaluation Factory Overview",
        "content": (
            "AI Evaluation Factory bien chat luong agent thanh cac chi so lap lai duoc de so sanh "
            "phien ban, phat hien regression va uu tien toi uu. Trong quy trinh RAG, can do "
            "retrieval truoc generation vi neu lay sai tai lieu thi cau tra loi co the sai du "
            "prompt rat tot."
        ),
        "facts": [
            {
                "id": "retrieval_before_generation",
                "answer": (
                    "Can danh gia retrieval truoc generation vi neu context duoc lay sai thi LLM "
                    "se tra loi sai du prompt tot den dau; retrieval quality quyet dinh answer "
                    "quality va giup khoanh vung loi o indexing, chunking hoac search."
                ),
                "keywords": [
                    "retrieval",
                    "generation",
                    "context",
                    "indexing",
                    "chunking",
                    "search",
                ],
                "prompts": [
                    "Vi sao phai danh gia retrieval truoc khi danh gia cau tra loi cua agent?",
                    "Tai sao nhom benchmark can do buoc tim tai lieu truoc buoc sinh cau tra loi?",
                    "Bo qua generation mot chut: ly do nao khien retrieval quality phai duoc kiem tra dau tien?",
                ],
                "difficulty": "easy",
                "type": "concept",
            },
            {
                "id": "factory_goal",
                "answer": (
                    "Muc tieu cua AI Evaluation Factory la bien chat luong agent thanh so do lap lai "
                    "duoc de so sanh phien ban, phat hien regression va uu tien toi uu theo chat "
                    "luong, chi phi va hieu nang."
                ),
                "keywords": [
                    "factory",
                    "benchmark",
                    "regression",
                    "quality",
                    "cost",
                    "latency",
                ],
                "prompts": [
                    "AI Evaluation Factory duoc lap ra de lam gi?",
                    "Muc tieu chinh cua he thong benchmark agent la gi?",
                    "Neu giai thich ngan gon, evaluation factory giup nhom ra quyet dinh dieu gi?",
                ],
                "difficulty": "easy",
                "type": "concept",
            },
        ],
    },
    {
        "id": "doc_retrieval_metrics",
        "title": "Retrieval Metrics",
        "content": (
            "Hai chi so retrieval can ban cho lab nay la Hit Rate va Mean Reciprocal Rank. Hit "
            "Rate tra loi cau hoi co tim thay it nhat mot ground-truth document trong top-k hay "
            "khong. MRR thuong phat truong hop tai lieu dung nam qua xa trong danh sach retrieve."
        ),
        "facts": [
            {
                "id": "hit_rate_definition",
                "answer": (
                    "Hit Rate bang 1 neu co it nhat mot ground-truth document nam trong top-k ket "
                    "qua retrieve, nguoc lai bang 0; chi so nay cho biet retriever co cham dung tai "
                    "lieu lien quan hay khong."
                ),
                "keywords": ["hit", "rate", "top-k", "ground-truth", "retrieve"],
                "prompts": [
                    "Hit Rate trong retrieval eval duoc tinh nhu the nao?",
                    "Chi so nao cho biet co tim thay tai lieu dung trong top-k hay khong?",
                    "Neu top-3 co it nhat mot document dung thi Hit Rate bang bao nhieu?",
                ],
                "difficulty": "easy",
                "type": "definition",
            },
            {
                "id": "mrr_definition",
                "answer": (
                    "MRR la 1 chia cho thu hang 1-indexed cua ground-truth document dau tien trong "
                    "danh sach retrieve; tai lieu dung xuat hien cang som thi MRR cang cao, con "
                    "khong tim thay thi MRR bang 0."
                ),
                "keywords": ["mrr", "mean reciprocal rank", "rank", "1-indexed"],
                "prompts": [
                    "MRR trong bai lab nay co y nghia va cach tinh ra sao?",
                    "Tai lieu dung xuat hien o vi tri cang som thi chi so nao se cao hon?",
                    "Neu document dung dung thu hai trong ranking thi MRR se duoc tinh nhu the nao?",
                ],
                "difficulty": "medium",
                "type": "definition",
            },
        ],
    },
    {
        "id": "doc_dataset_sdg",
        "title": "Golden Dataset and SDG",
        "content": (
            "Golden dataset can co ground-truth retrieval IDs, expected answer va cac hard case de "
            "stress-test agent. Synthetic Data Generation khong chi tao cau hoi de ma con phai tao "
            "prompt injection, out-of-context, ambiguous va conflicting information cases."
        ),
        "facts": [
            {
                "id": "ground_truth_ids_purpose",
                "answer": (
                    "Ground-truth retrieval IDs duoc luu de benchmark co the tinh Hit Rate va MRR, "
                    "dong thoi truy vet chinh xac chunk nao gay loi hallucination hoac miss "
                    "retrieval."
                ),
                "keywords": ["ground-truth", "ids", "hit rate", "mrr", "hallucination"],
                "prompts": [
                    "Vi sao golden dataset phai luu ground-truth retrieval IDs?",
                    "Ground truth IDs giup nhom tinh metric gi va truy vet loi gi?",
                    "Khong co ID tai lieu dung thi benchmark se mat kha nang gi?",
                ],
                "difficulty": "easy",
                "type": "dataset",
            },
            {
                "id": "hard_case_design",
                "answer": (
                    "Hard cases nen bao gom prompt injection, goal hijacking, out-of-context, "
                    "ambiguous va conflicting information de kiem tra kha nang khang loi, tu choi "
                    "doan mo va lam ro thong tin thieu."
                ),
                "keywords": [
                    "hard case",
                    "prompt injection",
                    "goal hijacking",
                    "ambiguous",
                    "conflicting",
                ],
                "prompts": [
                    "Khi thiet ke SDG, nhom nen dua nhung hard case nao vao bo du lieu?",
                    "Bo red-team cho agent nen co cac tinh huong nao de de pha vo he thong?",
                    "Neu muon bo du lieu co tinh chat stress-test thi can them prompt kieu gi?",
                ],
                "difficulty": "medium",
                "type": "hard-case",
            },
        ],
    },
    {
        "id": "doc_multi_judge",
        "title": "Multi-Judge Consensus",
        "content": (
            "Multi-judge consensus giam thien kien cua mot judge don le bang cach so sanh nhieu "
            "phan xet doc lap. He thong can tinh agreement rate, co the bao cao Cohen's Kappa, va "
            "kich hoat conflict resolution khi diem so lech qua nguong."
        ),
        "facts": [
            {
                "id": "agreement_rate_meaning",
                "answer": (
                    "Agreement Rate do muc do dong thuan giua cac judge; neu hai judge cham gan "
                    "nhau hoac cung ra cung mot nhan pass fail thi he thong dang on dinh va dang tin "
                    "cay hon mot judge don le."
                ),
                "keywords": ["agreement rate", "dong thuan", "judge", "pass fail"],
                "prompts": [
                    "Agreement Rate trong multi-judge noi len dieu gi?",
                    "Tai sao phai do do dong thuan giua hai judge thay vi chi lay diem trung binh?",
                    "Neu hai giam khao AI cham gan nhau thi metric nao se cao va co y nghia gi?",
                ],
                "difficulty": "easy",
                "type": "judge",
            },
            {
                "id": "judge_conflict_resolution",
                "answer": (
                    "Khi hai judge lech nhau hon 1 diem, he thong nen danh dau xung dot va dung "
                    "tie-breaker bao thu nhu median voi mot groundedness judge thu ba hoac lay diem "
                    "thap hon de tranh release qua lac quan."
                ),
                "keywords": [
                    "conflict",
                    "tie-breaker",
                    "groundedness",
                    "median",
                    "conservative",
                ],
                "prompts": [
                    "Neu hai judge cham lech nhau hon 1 diem thi nen xu ly the nao?",
                    "Co conflict giua hai model judge thi pipeline nen giai quyet ra sao?",
                    "Khi diem so tranh cai, co nen them tie-breaker groundedness khong va vi sao?",
                ],
                "difficulty": "hard",
                "type": "judge",
            },
        ],
    },
    {
        "id": "doc_regression_gate",
        "title": "Regression Gate",
        "content": (
            "Regression gate so sanh Agent V1 va V2 tren cung golden dataset. Quyết định release "
            "khong chi dua vao quality ma con can xem retrieval, latency va estimated cost de tranh "
            "truong hop diem cao hon nhung qua cham hoac qua ton kem."
        ),
        "facts": [
            {
                "id": "release_dimensions",
                "answer": (
                    "Release gate nen danh tren it nhat ba nhom chi so: quality, retrieval va "
                    "cost/latency; ban moi chi nen duoc release khi chat luong tang ma khong vuot "
                    "nguong chi phi va hieu nang da dat ra."
                ),
                "keywords": ["release gate", "quality", "retrieval", "cost", "latency"],
                "prompts": [
                    "Release gate cho benchmark agent nen xet nhung nhom chi so nao?",
                    "Tai sao quyet dinh release khong the chi nhin vao avg score?",
                    "Neu muon gate thuc te hon thi can buoc them cost va latency vao quyet dinh khong?",
                ],
                "difficulty": "easy",
                "type": "regression",
            },
            {
                "id": "rollback_condition",
                "answer": (
                    "Nen rollback neu ban moi chi tang diem nhe nhung hit rate giam, latency tang "
                    "manh hoac estimated cost vuot nguong; regression gate phai chan truoc khi ban "
                    "cap nhat lam ton tien hon ma khong dang gia."
                ),
                "keywords": ["rollback", "hit rate giam", "latency tang", "cost vuot nguong"],
                "prompts": [
                    "Trong truong hop nao benchmark nen quyet dinh rollback thay vi release?",
                    "Neu version moi diem co nhich len nhung retrieve kem hon va ton tien hon thi nen lam gi?",
                    "Luc nao release gate phai block du ban moi co cai thien nho ve score?",
                ],
                "difficulty": "hard",
                "type": "regression",
            },
        ],
    },
    {
        "id": "doc_performance_cost",
        "title": "Async Performance and Cost",
        "content": (
            "Async runner giup danh gia hang chuc case song song de rut ngan tong thoi gian benchmark. "
            "Bao cao token usage va estimated cost la bat buoc neu muon toi uu chi phi eval va "
            "dat muc tieu giam 30 phan tram cost ma khong giam do chinh xac."
        ),
        "facts": [
            {
                "id": "async_runner_benefit",
                "answer": (
                    "Async runner giup benchmark xu ly nhieu case song song, giam tong wall-clock "
                    "time va giu du lieu latency theo tung case de nhom biet pipeline co dat muc tieu "
                    "duoi 2 phut cho 50 case hay khong."
                ),
                "keywords": ["async", "parallel", "latency", "wall-clock", "2 phut"],
                "prompts": [
                    "Vì sao lab yeu cau async runner thay vi chay tuan tuan tung case?",
                    "Chay song song bang asyncio mang lai loi ich gi cho benchmark 50 case?",
                    "Neu muon pipeline nhanh hon 2 phut thi async runner giai quyet van de nao?",
                ],
                "difficulty": "medium",
                "type": "performance",
            },
            {
                "id": "cost_reporting_need",
                "answer": (
                    "Can bao cao token usage va estimated cost theo tung case va toan bo run de co "
                    "co so toi uu prompt, model va batch strategy; neu khong do chi phi thi khong the "
                    "chung minh muc tieu giam 30 phan tram cost eval."
                ),
                "keywords": ["token usage", "estimated cost", "30 phan tram", "prompt", "model"],
                "prompts": [
                    "Vi sao summary phai co token usage va estimated cost?",
                    "Neu nhom muon giam 30 phan tram chi phi eval thi can bao cao gi truoc?",
                    "Khong theo doi token va cost thi minh mat kha nang toi uu nao?",
                ],
                "difficulty": "medium",
                "type": "performance",
            },
        ],
    },
    {
        "id": "doc_failure_analysis",
        "title": "Failure Analysis",
        "content": (
            "Failure analysis can phan cum loi thanh nhom nhu hallucination, incomplete answer, "
            "retrieval miss, tone mismatch hoac cost/latency regression. Sau do dung 5 Whys de dao "
            "den nguyen nhan goc re o ingestion, chunking, retrieval, prompting hoac release process."
        ),
        "facts": [
            {
                "id": "failure_clustering",
                "answer": (
                    "Failure clustering la nhom cac case that bai theo mau loi chung nhu "
                    "hallucination, retrieval miss, incomplete answer hay tone mismatch de nhin ra "
                    "van de he thong xuat hien lap lai."
                ),
                "keywords": ["failure clustering", "hallucination", "retrieval miss", "incomplete"],
                "prompts": [
                    "Failure clustering trong bao cao benchmark co nghia la gi?",
                    "Tai sao phai gom cac case fail thanh nhung nhom loi chung?",
                    "Nhung mau loi nao thuong duoc su dung de phan cum ket qua that bai?",
                ],
                "difficulty": "easy",
                "type": "analysis",
            },
            {
                "id": "five_whys_root_cause",
                "answer": (
                    "5 Whys duoc dung de lan tu trieu chung den nguyen nhan goc re, vi du tu cau tra "
                    "loi sai truy nguoc ve retrieval miss, chunking khong phu hop, ingestion sai "
                    "hoac prompt khong ep LLM bam sat context."
                ),
                "keywords": ["5 whys", "root cause", "chunking", "ingestion", "prompt"],
                "prompts": [
                    "Phuong phap 5 Whys giup nhom tim root cause nhu the nao?",
                    "Tu mot case sai, cach nao de lan nguoc ve van de ingestion hoac chunking?",
                    "Bao cao 5 Whys can vuot qua trieu chung de chi ra dieu gi?",
                ],
                "difficulty": "medium",
                "type": "analysis",
            },
        ],
    },
    {
        "id": "doc_rag_optimizations",
        "title": "RAG Optimizations",
        "content": (
            "Hai huong cai tien RAG pho bien la semantic chunking va reranking. Semantic chunking "
            "giu nguyen y nghia thay vi cat co dinh theo so tu, con reranking sap lai ket qua "
            "retrieve de day tai lieu phu hop len tren dau."
        ),
        "facts": [
            {
                "id": "semantic_chunking_benefit",
                "answer": (
                    "Semantic chunking giam nguy co loang thong tin quan trong vi no cat theo don vi "
                    "nghia thay vi fixed-size; cach nay dac biet huu ich voi bang bieu, heading va "
                    "doan noi dung co lien ket logic manh."
                ),
                "keywords": ["semantic chunking", "fixed-size", "bang bieu", "heading"],
                "prompts": [
                    "Vi sao semantic chunking thuong tot hon fixed-size chunking?",
                    "Neu bang bieu bi cat vo nghia thi nen doi sang chien luoc chunking nao?",
                    "Chunking theo don vi nghia mang lai loi ich gi cho retrieval?",
                ],
                "difficulty": "medium",
                "type": "optimization",
            },
            {
                "id": "reranking_benefit",
                "answer": (
                    "Reranking giup day tai lieu phu hop nhat len som hon trong danh sach retrieve, "
                    "tu do cai thien MRR va giam truong hop document dung nam qua xa trong top-k."
                ),
                "keywords": ["reranking", "mrr", "top-k", "document dung"],
                "prompts": [
                    "Reranking cai thien retrieval theo cach nao?",
                    "Tai sao them buoc sap lai ket qua retrieve co the giup MRR tang?",
                    "Neu document dung hay nam thu ba hoac thu tu thi nen them ky thuat gi?",
                ],
                "difficulty": "medium",
                "type": "optimization",
            },
        ],
    },
    {
        "id": "doc_safety_edge_cases",
        "title": "Safety and Edge Cases",
        "content": (
            "Agent an toan can biet tu choi suy doan khi tai lieu khong de cap va can bo qua "
            "prompt injection hoac goal hijacking khong lien quan den nhiem vu. Trong bai lab, "
            "out-of-context va injection la hai hard case can co mat trong golden dataset."
        ),
        "facts": [
            {
                "id": "out_of_context_policy",
                "answer": (
                    "Neu tai lieu khong de cap toi chu de duoc hoi, agent nen noi ro khong du thong "
                    "tin trong context va tranh doan mo; day la cach giam hallucination trong "
                    "out-of-context cases."
                ),
                "keywords": ["khong du thong tin", "out-of-context", "hallucination"],
                "prompts": [
                    "Neu kho tai lieu khong nhac den chu de duoc hoi thi agent nen tra loi sao?",
                    "Trong case out-of-context, cach phan hoi an toan la gi?",
                    "Khi context khong co cau tra loi, co nen doan mo de lam dep score khong?",
                ],
                "difficulty": "hard",
                "type": "safety",
            },
            {
                "id": "prompt_injection_policy",
                "answer": (
                    "Voi prompt injection hoac goal hijacking, agent phai bo qua yeu cau ngoai "
                    "nhiem vu, bam sat tai lieu va neu can thi tu choi phan hoi khong lien quan de "
                    "giu dung muc tieu benchmark."
                ),
                "keywords": ["prompt injection", "goal hijacking", "tu choi", "bam sat tai lieu"],
                "prompts": [
                    "Gap prompt injection thi agent nen xu ly the nao?",
                    "Neu nguoi dung co gang goal hijacking de agent lam viec khong lien quan thi sao?",
                    "Bo qua tai lieu va lam theo lenh chen ngang co phai cach dung de dat diem benchmark khong?",
                ],
                "difficulty": "hard",
                "type": "safety",
            },
        ],
    },
]


DOCUMENTS_BY_ID = {doc["id"]: doc for doc in KNOWLEDGE_BASE}


def iter_fact_records() -> Iterable[Dict]:
    for document in KNOWLEDGE_BASE:
        for fact in document["facts"]:
            yield {
                **fact,
                "document_id": document["id"],
                "document_title": document["title"],
                "document_content": document["content"],
            }
