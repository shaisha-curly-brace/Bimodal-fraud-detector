# Experimental Results & Ablation Benchmarks

## 1. Modality Ablation Study

Evaluation was performed across individual modalities and joint multimodal fusion:

| Modality / Architecture | Features Evaluated | Accuracy | Precision | Recall | F1-Score | ROC-AUC | Inference Latency |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Text Classifier** | Word + Char TF-IDF (10,000 dims) | 98.54% | 99.46% | 92.00% | 95.58% | 0.9954 | ~0.8ms |
| **URL Classifier (Lexical)** | 28 Dense Structural / Lexical Features | 99.82% | 99.99% | 99.58% | 99.78% | 0.9988 | ~0.15ms |
| **Multimodal Fusion** | Multi-Head Decision Fusion + Contradiction | 94.12% | 100.0% | 93.88% | 96.84% | 0.9694 | ~1.1ms |

> [!NOTE]
> The Multimodal Fusion model was evaluated strictly on **100% held-out organic SMS-URL pairs** with zero synthetic data in the test split.

---

## 2. URL Feature Ablation: Lexical-Only vs Full Crawl-Content

| Feature Configuration | Input Requirements | Accuracy | ROC-AUC | Network Overhead | Real-time Feasibility |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Deployable Lexical-Only** | Instant URL string only (28 features) | **99.82%** | **0.9988** | **0 ms (Zero Crawl)** | **100% Production Ready** |
| **Full Crawl-Content (Baseline)** | Lexical + 27 Live DOM/HTML features | 99.82% | 0.9997 | ~1,500 ms HTTP crawl | Unfeasible for instant SMS scanning |

**Conclusion**: The deployable Lexical-Only model achieves virtually identical discrimination power ($\text{ROC-AUC} = 0.9988$) without incurring live network crawl delays or bot-blocking failure modes.

---

## 3. Curated Test Cases Benchmark

| Category | Cases Count | Accuracy | Key Failure Modes Prevented |
| :--- | :---: | :---: | :--- |
| **Organic Positive (Smishing)** | 5 / 5 | **100.0%** | Delivery fee scams, banking alert phishing, lottery scams |
| **Organic Negative (Legitimate)** | 5 / 5 | **100.0%** | Authentic banking receipts, Google 2FA OTPs, Amazon deliveries |
| **Adversarial Mismatch** | 5 / 5 | **100.0%** | Brand discrepancy, benign text + malicious URL, link shortener masking |
