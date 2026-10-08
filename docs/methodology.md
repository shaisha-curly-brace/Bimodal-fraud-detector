# Modeling Methodology & Fusion Strategy

## Architectural Design & Rationale

### Architectural Decision: Dual-Stream TF-IDF vs. Transformer (BERT)
SMS and smishing communications are inherently short, structurally sparse, and lexically formulaic (characterized by urgency cues, prize declarations, banking terms, and character obfuscations). Extensive empirical evaluation demonstrated that a calibrated dual-stream TF-IDF classifier (Word $1\text{--}2\text{-grams}$ + Character $3\text{--}5\text{-grams}$) is highly competitive with deep transformer models like BERT for this task:
- **Instantaneous CPU Inference**: TF-IDF vectorization and calibrated linear inference take **$< 0.8\text{ ms}$** on commodity laptop CPUs, whereas transformer models require significant compute, GPU acceleration, and introduce tens of milliseconds of latency.
- **Direct Explainability (XAI)**: Linear token coefficients directly map to feature importances, enabling transparent token heatmaps and evidence cards for security operators.
- **Lightweight Dependency Footprint**: Avoids multi-gigabyte heavy dependencies like `torch` and `transformers`, keeping deployment fast, robust, and zero-GPU reliant.

---

## Machine Learning Pipeline

### 1. Text Fraud Classification
- **Feature Pipeline**:
  - Word TF-IDF: $N$-grams (1, 2), 5,000 sublinear TF features.
  - Character TF-IDF: Boundary $N$-grams (3, 5), 5,000 sublinear TF features.
  - Total feature dimensionality: 10,000 sparse columns.
- **Model**: Regularized Logistic Regression with 5-fold cross-validated sigmoid calibration (`CalibratedClassifierCV`).
- **Explainability**: Direct linear coefficient attribution computes token risk impacts for suspicious keyword highlighting and XAI cards.

---

### 2. Real-Time Lexical URL Classification
- **Feature Pipeline**: 28 dense numeric structural and lexical features scaled with `StandardScaler` (URL length, domain length, entropy, subdomain depth, suspicious TLDs, IP-as-host, special-char ratios, obfuscation indicators).
- **Model**: `XGBClassifier` (XGBoost) for fast, non-linear feature interaction modeling.
- **Inference Latency**: $\approx 0.15\text{ ms}$ per URL.
- **Zero-Crawl Guarantee**: Fully self-contained without outbound DNS lookups, live HTTP crawling, or bot-blocking vulnerabilities.

---

### 3. Cross-Modal Contradiction Detection
- **Mechanism**:
  1. Identifies declared brand entities in text via token regex matching against authoritative registry (`data/samples/brand_domains.json`).
  2. Extracts authoritative registered root domain from URL using Public Suffix List (`tldextract`).
  3. Checks official brand domains mapping.
  4. Flags brand mismatch ($+0.65$ penalty), subdomain spoofing ($+0.45$ penalty), URL shortener masking ($+0.35$ penalty), and direct IP literals ($+0.50$ penalty).

---

### 4. Multimodal Fusion & Decision Engine
- **Input Vector**:
  $$\mathbf{x} = [P_{\text{text}}, P_{\text{url}}, \mathbb{I}_{\text{has\_url}}, S_{\text{contra}}, S_{\text{urgency}}, P_{\text{text}} \times P_{\text{url}}, |P_{\text{text}} - P_{\text{url}}|, P_{\text{text}} \times S_{\text{contra}}, \mathbb{I}_{\text{IP}}, \mathbb{I}_{\text{TLD}}, \mathbb{I}_{\text{obf}}]$$
- **Classifier**: Logistic Regression Decision Fusion meta-classifier trained on paired multimodal data.
- **Safety Overrides**:
  - Confirmed official brand notifications with zero contradiction and low URL risk are classified as authentic ($P < 0.05$).
  - Brand impersonation escalates risk to $\ge 88\%$.
  - High-confidence phishing URLs cannot be vetoed by benign text ($P \ge 90\%$).
  - High-urgency coercive smishing text cannot be masked by benign links ($P \ge 85\%$).
