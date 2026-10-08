# Multimodal Datasets Directory

This folder contains raw and processed training datasets for the Bimodal Fraud & Phishing Detection System.

## Offline Bundled Datasets
To guarantee zero-manual-setup offline training in any demo or evaluation environment, full representative dataset corpora are bundled directly in `raw/`:

1. **Mendeley SMS Phishing Corpus** (`raw/sms/sms_mendeley.csv`):
   - **5,971 messages** labeled as `ham` (4,834), `smishing` (543), and `spam` (454).
   - Provides organic text samples, urgency language, and inline URLs.

2. **PhiUSIIL Phishing URL Dataset** (`raw/url/Dataset_5971.csv`):
   - **235,795 URLs** labeled as legitimate (`1`, 134,850 rows) or phishing (`0`, 100,945 rows).
   - Enriched with 28 instantaneous lexical/structural features without requiring live network crawling.

3. **Processed Datasets** (`processed/`):
   - `cleaned_sms.csv`: Cleaned and deduplicated SMS messages with regex-extracted URLs and normalized boolean flags.
   - `cleaned_url.csv`: Precomputed 28 dense lexical features across the full URL corpus for instantaneous training.
   - `merged_pairs.csv`: Paired multimodal dataset containing 171 organic SMS-URL pairs and 650 synthetic brand augmentation pairs.

## Rules & Splitting Policy
- **100% Organic Evaluation Split**: All test evaluations and benchmarks are performed strictly on `pair_type == 'organic'`. Zero synthetic data is ever included in evaluation splits.
- **Synthetic Augmentation**: Synthetic pairs are strictly restricted to training augmentation to establish authoritative brand-domain alignment.
