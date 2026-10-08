# Datasets & Preprocessing Specification

## Datasets Overview

The system is built and evaluated strictly using the two provided datasets:

| Dataset | Raw File Path | Samples Count | Label Schema | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **SMS Phishing Corpus** | `ml/datasets/raw/sms/Dataset_5971.csv` / `sms_mendeley.csv` | 5,971 rows | `ham` (4,834), `smishing` (543), `spam` (454) | SMS message semantics, urgency, token feature extraction |
| **PhiUSIIL Phishing URL Dataset** | `ml/datasets/raw/url/PhiUSIIL_Phishing_URL_Dataset.csv` / `Dataset_5971.csv` | 235,795 rows | `1 = legitimate` (134,850), `0 = phishing` (100,520) | General URL reputation and lexical feature modeling |

---

## 1. SMS Dataset Preprocessing & Cleaning

### Key Preprocessing Rules:
- **Encoding**: Loaded using `encoding="utf-8-sig"` to handle BOM headers.
- **Label Normalization**: Lowercase normalization mapped inconsistent casing (`Smishing`, `smishing`, `Spam`, `spam`, `ham`) into uniform lowercase classes.
- **Entity Flag Normalization**: `URL`, `EMAIL`, `PHONE` fields normalized from inconsistent text strings (`Yes`, `yes`, `No`, `no`) into booleans.
- **URL Extraction**: Extracted inline URLs directly from message `TEXT` using regex `(https?://[^\s<>\"'()]+|www\.[^\s<>\"'()]+)`.
- **Token Preservation**: Special placeholders like `&lt;#&gt;` (anonymized numbers from original corpus) and currency symbols are preserved as informative tokens rather than stripped.

---

## 2. PhiUSIIL Phishing URL Dataset & Feature Constraints

### Label Mapping Guarantee:
- Raw `label == 1` represents **Legitimate URLs** (134,850 rows).
- Raw `label == 0` represents **Phishing / Fraud URLs** (100,945 rows).
- Target variable `is_fraud` is assigned `1` for phishing (raw 0) and `0` for legitimate (raw 1).

### Deployable Feature Subset (Zero-Crawl):
The deployable model uses **strictly lexical/structural features** computable instantly from a URL string alone:
- `URLLength`, `DomainLength`, `IsDomainIP`, `TLD`, `TLDLength`, `NoOfSubDomain`
- `HasObfuscation`, `NoOfObfuscatedChar`, `ObfuscationRatio`
- `NoOfLettersInURL`, `LetterRatioInURL`, `NoOfDegitsInURL`, `DegitRatioInURL`
- `NoOfEqualsInURL`, `NoOfQMarkInURL`, `NoOfAmpersandInURL`, `NoOfOtherSpecialCharsInURL`, `SpacialCharRatioInURL`
- `IsHTTPS`, `CharContinuationRate`, `Entropy`, `DomainEntropy`, `IsSuspiciousTLD`, `HasBrandInSubdomain`, `HasSecurityKeyword`

Live-page-content features (`LineOfCode`, `HasTitle`, `NoOfPopup`, `HasPasswordField`, etc.) are excluded from deployable inference and reserved only for comparative offline evaluation.

---

## 3. Multimodal Pairing & Evaluation Policy

### Strict Evaluation Policy:
- **Organic Pairs**: 171 SMS messages containing real embedded URLs from the original dataset.
- **Synthetic Augmentation**: 650 brand-consistent legitimate SMS-URL pairs generated using official brand domain mappings (`data/samples/brand_domains.json`).
- **RULE**: The evaluation and test split is **100% pure organic pairs** (`pair_type == 'organic'`). Synthetic pairs are strictly restricted to training augmentation and never appear in evaluation splits.
