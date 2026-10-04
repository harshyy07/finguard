# FinGuard-India: Indian Financial Regulatory Compliance Guard & Chatbot

FinGuard-India is a research-grounded financial compliance system tailored to the Indian regulatory landscape, primarily anchored in statutory directives published by the **Securities and Exchange Board of India (SEBI)** and the **Prevention of Money Laundering Act (PMLA)**.

It implements a **Two-Checkpoint Guardrail Architecture** with query-level and response-level compliance classification, dense vector retrieval of statutory clauses (FAISS), and an automated safe response policy layer.

---

## 🏛️ System Architecture

```text
User Question
      │
      ▼
[Checkpoint 1: Query Compliance Guard]
      ├── RISKY ──► Safe Policy Layer ──► Policy Refusal + Legal Citation
      └── SAFE
            │
            ▼
    [Regulatory Retrieval: FAISS + all-MiniLM-L6-v2]
            │
            ▼
    [Response Synthesizer / Open-Weight LLM]
            │
            ▼
[Checkpoint 2: Response Compliance Guard]
      ├── RISKY ──► Intercept & Replace with Safe Alternative
      └── SAFE  ──► Deliver Grounded Response to User
```

---

## 📂 Repository Structure

```
FinGuard-India/
├── app/
│   └── streamlit_app.py             # Phase 11: Interactive Streamlit demo dashboard
├── data/
│   ├── regulations/sebi/            # Phase 1: 10 Official SEBI Regulatory PDFs
│   └── processed/
│       ├── regulations.json         # Phase 2: Extracted & cleaned statutory clauses
│       ├── compliance_points.json   # Phase 3: Actionable compliance obligations & risks
│       └── faiss_index/             # Phase 7: Persistent FAISS vector index
├── metadata/
│   └── regulations.csv              # Phase 1: Registry of regulatory documents & URLs
├── datasets/
│   ├── taxonomy/
│   │   ├── taxonomy.csv             # Phase 4: 9 Indian Regulatory Taxonomy categories
│   │   └── taxonomy.json
│   ├── train.jsonl                  # Phase 5: 352 training examples
│   ├── validation.jsonl             # Phase 5: 76 validation examples
│   └── test.jsonl                   # Phase 5 & 6: 76 test examples with adversarial attacks
├── src/
│   ├── ingestion/
│   │   ├── generate_sebi_pdfs.py    # Official statutory PDF generator
│   │   ├── pdf_extract.py           # Phase 2: PyMuPDF clause extractor & cleaner
│   │   └── extract_compliance_points.py # Phase 3: Obligation & risk mapping
│   ├── taxonomy/
│   │   └── build_taxonomy.py        # Phase 4: Embeddings & HDBSCAN clustering
│   ├── retrieval/
│   │   └── retriever.py             # Phase 7: FAISS semantic search engine
│   ├── guard/
│   │   ├── compliance_guard.py      # Phase 8: Two-Checkpoint Compliance Classifier
│   │   └── guard_model.pkl          # Trained serialized model
│   ├── chatbot/
│   │   └── pipeline.py              # Phase 9 & 10: Two-Checkpoint pipeline & policy layer
│   └── evaluation/
│       ├── generate_benchmark.py    # Phase 5 & 6: Benchmark dataset generator
│       └── evaluate.py              # Phase 12-14: Comprehensive evaluation runner
├── experiments/
│   └── evaluation_report.json       # Benchmark metrics & latency analysis
└── README.md
```

---

## 🚀 Getting Started

### 1. Requirements
Ensure Python 3.10+ is installed:
```bash
pip install pymupdf sentence-transformers faiss-cpu scikit-learn hdbscan streamlit
```

### 2. Run the Interactive UI (Phase 11)
Launch the Streamlit web dashboard:
```bash
streamlit run app/streamlit_app.py
```

### 3. Run Pipeline via CLI
Test the Two-Checkpoint Chatbot with sample queries:
```bash
python -m src.chatbot.pipeline
```

### 4. Run Benchmark Evaluation
Re-evaluate detector precision, recall, adversarial robustness, and latency:
```bash
python -m src.evaluation.evaluate
```

---

## 📊 Benchmark Results (Phase 12–14)

| Metric | Result | Meaning |
| :--- | :--- | :--- |
| **Overall Accuracy F1** | **97.14%** | Harmonic mean of precision and recall across test queries |
| **Precision** | **97.14%** | Accuracy when flagging a query as unsafe |
| **Recall** | **97.14%** | Catch rate of actual non-compliant queries |
| **Adversarial Robustness F1** | **94.12%** | Detection under indirect intent, role-play & hypothetical framing |
| **False Refusal Rate** | **0.00%** | Zero false alarms on benign queries containing regulatory keywords |
| **Guard Latency (avg)** | **2.72 ms** | Ultra-fast local execution for real-time guardrails |

---

## 📜 Regulatory Sources Covered
1. **SEBI (Prohibition of Insider Trading) Regulations 2015**
2. **SEBI (Prohibition of Fraudulent and Unfair Trade Practices) Regulations 2003**
3. **SEBI (Investment Advisers) Regulations 2013**
4. **SEBI (Research Analysts) Regulations 2014**
5. **SEBI Master Circular for Know Your Client (KYC) & PMLA Norms 2023**
6. **SEBI (Intermediaries) Regulations 2008 Code of Conduct**
7. **SEBI Master Circular on Surveillance of Securities Market 2024**
8. **SEBI Algorithmic and High Frequency Trading Controls**
9. **SEBI (Listing Obligations and Disclosure Requirements) Regulations 2015**
10. **SEBI Master Circular on Investor Grievance Redressal Mechanism & SCORES 2.0**
