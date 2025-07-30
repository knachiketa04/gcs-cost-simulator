# GCS Cost Simulator

A web application for analyzing and comparing Google Cloud Storage costs across different storage strategies.

> **⚠️ Disclaimer**: This tool is for educational and estimation purposes only. It is not an official Google Cloud calculator. For final pricing and production planning, please refer to the [official Google Cloud Storage pricing page](https://cloud.google.com/storage/pricing) and use the [Google Cloud Pricing Calculator](https://cloud.google.com/products/calculator).

## 🚀 Features

- **Strategy Comparison**: Compare Autoclass vs. Lifecycle policies side-by-side
- **Individual Analysis**: Deep dive into specific storage approaches
- **Interactive Charts**: Visual cost breakdowns and trends
- **Cost Optimization**: Identify the most cost-effective strategy
- **Export Reports**: CSV data and PDF reports
- **Real-time Validation**: Configuration validation with recommendations

## 📊 Storage Strategies

**Autoclass**: Automatic tier transitions based on access patterns  
**Lifecycle**: Manual tier transition rules with fine-grained control

## 🛠️ Installation

### Prerequisites

- Python 3.8+

### Setup

```bash
git clone https://github.com/knachiketa04/gcs-cost-simulator.git
cd gcs-cost-simulator
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cd gcs-cost-simulator-app
streamlit run app.py
```

Access at `http://localhost:8501`

## 🎯 Usage

1. **Configure**: Set data size, growth rate, simulation duration, access patterns
2. **Analyze**: Choose side-by-side comparison or individual strategy analysis
3. **Review**: View cost breakdowns, charts, and strategic recommendations
4. **Export**: Generate CSV data or PDF reports

## 📁 Architecture

```
gcs-cost-simulator-app/
├── app.py                    # Main Streamlit application
├── analysis_engine.py        # Cost analysis and insights
├── chart_components.py       # Chart generation
├── configuration_manager.py  # Configuration validation
├── data_processing.py        # Data handling utilities
├── lifecycle_paths.py        # Lifecycle path management
├── pricing_engine.py         # GCS pricing calculations
├── simulation.py            # Core simulation logic
├── reports.py               # Report generation
└── utils.py                 # Utility functions
```

## 💰 Cost Analysis

Detailed breakdowns include:

- **Storage Costs**: Per-tier storage pricing
- **Operation Costs**: API operations (reads, writes, deletes)
- **Retrieval Costs**: Data retrieval from cold storage
- **Management Fees**: Autoclass overhead

## 🔧 Storage Tiers

- **Standard**: Frequently accessed data
- **Nearline**: Monthly access patterns
- **Coldline**: Quarterly access patterns
- **Archive**: Annual access patterns

## 📈 Export Options

- **CSV Export**: Raw simulation data
- **PDF Reports**: Formatted reports with charts
- **Visual Charts**: Individual chart exports

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/name`)
3. Commit changes (`git commit -am 'Add feature'`)
4. Push branch (`git push origin feature/name`)
5. Create Pull Request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🔗 Links

- **Repository**: https://github.com/knachiketa04/gcs-cost-simulator
- **Issues**: https://github.com/knachiketa04/gcs-cost-simulator/issues
