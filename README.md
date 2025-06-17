
# 🚀 GCS Autoclass Simulator

A visual and interactive Streamlit application to simulate Google Cloud Storage (GCS) Autoclass behavior, including:

- Monthly data ingestion
- Storage class transitions (Standard → Nearline → Coldline → Archive)
- Access-triggered re-promotion
- Autoclass management fee calculation based on object eligibility (>128 KiB)
- Tier-wise accumulation chart
- Full cost breakdown (storage, retrieval, API, management fee)

## 📦 Features

- Support for average object size and object count modeling
- CSV export of results
- Realistic cost simulation with user-tunable access patterns
- Designed for cost planning, optimization, and educational use

## 📋 Installation

```bash
git clone https://github.com/yourusername/gcs-autoclass-simulator.git
cd gcs-autoclass-simulator
pip install -r requirements.txt
streamlit run streamlit_app/app.py
```

## 🧮 Inputs

- Monthly write volume (GB)
- Average object size (KiB)
- % of data >128 KiB (eligible for Autoclass)
- Access rates for Nearline / Coldline / Archive
- Monthly read/write operation counts

## 📊 Output

- Monthly cost breakdown: Storage, Retrieval, API, Autoclass Fee
- Data growth chart across storage classes
- CSV export

## 📸 Screenshot

_You can add screenshots to `assets/` and reference here._

## 📜 License

MIT License – use freely with attribution.
