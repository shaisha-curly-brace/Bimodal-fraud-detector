# 🛡️ Bimodal Fraud & Phishing Detection System (Text + URL)

An end-to-end bimodal threat intelligence and fraud detection engine that evaluates SMS message semantics, inline URLs, and cross-modal brand contradictions in real time.

Built strictly using the **Mendeley SMS Phishing Corpus (5,971 messages)** and the **PhiUSIIL Phishing URL Dataset (235,795 URLs)**.

---

## ⚡ Quickstart for Demo (Ready in < 2 minutes)

Follow these exact steps from a clean checkout to a fully running dashboard:

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```
*(No GPU, PyTorch, or Transformer downloads required — pure scikit-learn & XGBoost)*

### 2. Train Models & Run Evaluation (Single Command)
```bash
python run.py --train
```
*This command cleans datasets, generates organic/synthetic pairs, trains the dual-stream TF-IDF text classifier, trains the XGBoost URL classifier, trains the decision fusion combiner, and evaluates test splits in under ~20 seconds.*

### 3. Launch the Server
```bash
python run.py
```

### 4. Open the Threat Intelligence Dashboard
Open your browser to:
- 🖥️ **Dashboard UI**: [http://localhost:8000](http://localhost:8000)
- 📖 **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

*In the dashboard, click any preloaded test case button (e.g., "Urgent Bank of America alert") or paste any message + URL, and click **Analyze Fraud Risk** to view real-time risk scores (0–100), modality breakdown cards, and forensic XAI evidence.*

---

## 🚀 Key Highlights & Architectural Features

- **⚡ Zero-Crawl Deployable URL Engine**: Operates exclusively on **28 dense lexical and structural features** modeled with **XGBoost**, running in **0.15ms** without live webpage crawling, DNS delays, or bot-blocking vulnerabilities.
- **💬 Dual-Stream TF-IDF Text Classifier**: Combines word ($1\text{--}2\text{-grams}$) and character boundary ($3\text{--}5\text{-grams}$) representations with 5-fold cross-validated sigmoid calibration (`CalibratedClassifierCV`). Directly feeds token weights into XAI evidence cards.
- **⚖️ Cross-Modal Contradiction Analyzer**: Flags brand impersonation (e.g. text claiming "Chase Bank" while linking to an unauthorized domain), subdomain spoofing, and link shortener evasion against authoritative brand domain mappings.
- **🔬 Explainable AI (XAI)**: Generates human-readable evidence cards, token risk heatmaps, URL lexical anatomy tables, and defensive security guidance.
- **🖥️ Cyber Threat Intelligence Dashboard**: High-contrast dark theme with animated SVG risk gauge meters, bimodal breakdown cards, and preloaded test case quick-loaders.

---

## 📊 Empirical Benchmarks & Ablation Study

> **Evaluation Policy**: Metrics are evaluated on **100% held-out organic data** (zero synthetic data in test splits). Running `python run.py --train` retrains all models and writes empirical metrics to `ml/experiments/results/`.

| Modality / Architecture | Features Evaluated | Accuracy | Precision | Recall | F1-Score | ROC-AUC | Inference Latency |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Text Classifier** | Word + Char TF-IDF (10,000 dims) | **98.54%** | **99.46%** | **92.00%** | **95.58%** | **0.9954** | ~0.8ms |
| **URL Classifier (Lexical)** | 28 Structural Features (XGBoost) | **99.80%** | **99.97%** | **99.56%** | **99.77%** | **0.9989** | ~0.15ms |
| **Bimodal Fusion** | Decision Fusion + Contradiction Engine | **96.08%** | **96.08%** | **100.0%** | **0.9800** | **1.0000** | ~1.1ms |

### Zero-Crawl vs Full Crawl-Content Ablation

| Feature Subset | Input Requirements | Accuracy | ROC-AUC | Network Overhead | Real-Time Suitability |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Deployable Lexical Model** | URL string only (28 features) | **99.80%** | **0.9989** | **0 ms (Zero Crawl)** | **100% Production Ready** |
| **Full Crawl-Content Baseline** | Lexical + 27 Live DOM features | 99.82% | 0.9997 | ~1,500 ms crawl | Unfeasible for instant SMS scan |

---

## 📁 Repository Structure

```text
multimodal-fraud-detection/
├── frontend/
│   ├── index.html                   # Cyber threat intelligence dashboard
│   ├── style.css                    # Glassmorphism dark-theme styling
│   ├── app.js                       # UI controller & API client
│   └── components/
│       ├── result-card.js           # Modality metric cards (Text, URL, Contradiction)
│       ├── risk-meter.js            # SVG animated speedometer gauge
│       ├── evidence-panel.js        # Forensic evidence & token highlighter
│       └── upload.js                # (Future-scope stub)
│
├── backend/
│   ├── main.py                      # FastAPI server & static file mounting
│   ├── config.py                    # Pydantic-settings & global configuration
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py                # REST API endpoints (/api/analyze, /api/health, etc.)
│   │   └── schemas.py               # Pydantic data models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── fraud_service.py         # Master bimodal orchestration (run_pipeline)
│   │   ├── fusion_service.py        # Calibrated decision fusion
│   │   └── explanation_service.py   # XAI evidence generator
│   ├── architectures/
│   │   ├── __init__.py
│   │   ├── text_model.py            # Calibrated TF-IDF text classifier wrapper
│   │   ├── url_model.py             # Lexical XGBoost URL model wrapper
│   │   ├── fusion_model.py          # Decision fusion meta-classifier wrapper
│   │   └── image_model.py           # (Future-scope stub)
│   ├── analyzers/
│   │   ├── __init__.py
│   │   ├── text_analyzer.py         # Text cleaning & urgency detection
│   │   ├── url_analyzer.py          # Instant lexical feature inspection
│   │   ├── contradiction_analyzer.py# Brand impersonation & spoofing detector
│   │   ├── image_analyzer.py        # (Future-scope stub)
│   │   └── ocr_analyzer.py          # (Future-scope stub)
│   └── utils/
│       ├── __init__.py
│       ├── preprocessing.py         # Tokenizer & entity extraction
│       ├── feature_extraction.py    # 28 dense lexical URL metrics
│       └── logger.py                # Structured logger
│
├── ml/
│   ├── datasets/
│   │   ├── raw/ (sms/ & url/)       # Original CSV datasets
│   │   ├── processed/               # Cleaned & paired CSV datasets
│   │   ├── clean_sms.py             # SMS cleaning & label normalization
│   │   ├── clean_url.py             # URL cleaning & 28 lexical features
│   │   ├── pairing.py               # Bimodal pairing script (organic test split)
│   │   ├── download_datasets.py     # Dataset verification & download script
│   │   └── README.md
│   ├── training/
│   │   ├── train_text.py            # Text model training pipeline
│   │   ├── train_url.py             # Lexical URL XGBoost training pipeline
│   │   ├── train_fusion.py          # Bimodal fusion training pipeline
│   │   └── train_image.py           # (Future-scope stub)
│   ├── evaluation/
│   │   ├── evaluate.py              # System evaluation suite
│   │   ├── metrics.py               # Metric calculation helpers
│   │   └── comparison.py            # Modality & feature ablation study
│   ├── notebooks/
│   │   └── eda.ipynb                # Exploratory data analysis notebook
│   └── experiments/results/         # Serialized metrics & benchmarks JSON
│
├── model_weights/                   # Serialized ML model weights & scalers
│   ├── text/
│   ├── url/
│   └── fusion/
│
├── data/
│   ├── samples/brand_domains.json   # Authoritative brand domains reference
│   └── test_cases/                  # Curated ground truth test suites
│       ├── organic_positive.json
│       ├── organic_negative.json
│       └── adversarial_mismatch.json
│
├── tests/                           # Automated Pytest unit & integration tests
│   ├── test_text.py
│   ├── test_url.py
│   ├── test_fusion.py
│   ├── test_api.py
│   └── test_image.py                # (Future-scope stub)
│
├── docs/                            # Comprehensive technical documentation
│   ├── architecture.md
│   ├── dataset.md
│   ├── methodology.md
│   └── experiments.md
│
├── run.py                           # CLI entry point (server / train / eval)
├── requirements.txt                 # Python dependencies
├── .env.example
└── README.md
```

---

## 🧪 Testing & Validation

```bash
# Run the automated pytest suite (30 comprehensive tests)
python -m pytest -v tests/
```

---

## 🌐 REST API Endpoints

- `POST /api/analyze` (or `POST /api/v1/analyze`): Master endpoint for analyzing SMS text and/or URL with full XAI evidence output.
- `GET /api/health` (or `GET /api/v1/health`): System health check returning `{"status": "ok", "models_loaded": {...}}`.
- `GET /api/test-cases` (or `GET /api/v1/test-cases`): Serves curated test suites for quick-testing.
- `GET /api/metrics` (or `GET /api/v1/metrics`): Serves empirical benchmark and ablation matrices.
