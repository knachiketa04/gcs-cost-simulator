# 🚀 GCS Storage Strategy Simulator

## ⚠️ **Educational Disclaimer**

**This tool is designed for educational purposes and cost estimation guidance only.** While it models GCS pricing and behavior based on publicly available Google Cloud documentation, it should not be used as the sole basis for commercial decisions or production deployments.

**For commercial use and production environments:**

- Always conduct thorough testing with your actual data and access patterns
- Consult the official [Google Cloud Storage documentation](https://cloud.google.com/storage/docs)
- Validate pricing with the [Google Cloud Pricing Calculator](https://cloud.google.com/products/calculator)
- Consider engaging with Google Cloud specialists for enterprise scenarios
- Test both Autoclass and lifecycle policies in your specific environment before making final decisions

**The authors are not responsible for any costs or issues arising from decisions based solely on this simulator.**

---

A modular, production-ready Streamlit application that compares Google Cloud Storage (GCS) Autoclass vs Lifecycle Policies with accurate cost modeling, intelligent unit scaling, and comprehensive side-by-side analysis.

## ✨ Key Features

### 🔄 **Three Analysis Modes**

- **🤖 Autoclass Only**: Simulate intelligent, access-based storage optimization
- **📋 Lifecycle Only**: Model time-based storage transitions with custom rules
- **⚖️ Side-by-Side Comparison**: Direct cost and performance comparison

### 💰 **Comprehensive Cost Modeling**

- **Accurate GCS Pricing**: Regional pricing with custom configurations
- **Lifecycle-Specific Costs**: Retrieval costs and early deletion fees
- **Transparent Fees**: Autoclass management fees vs lifecycle retrieval costs
- **TCO Analysis**: Total cost of ownership over extended periods

### 📊 **Smart Reporting & Export**

- **Interactive Tables**: Auto-scaling units (GB→TiB, $→$M)
- **PDF Reports**: Executive summaries with strategic insights
- **CSV Export**: Raw data for further analysis
- **Cost Breakdowns**: Storage, API, management, and retrieval costs

## 🚀 Quick Start

```bash
git clone https://github.com/knachiketa04/gcs-cost-simulator.git
cd gcs-cost-simulator
pip install -r requirements.txt
streamlit run gcs-cost-simulator-app/app.py
```

## 🏗️ Architecture

Built with a clean, modular design for maintainability and extensibility:

```
gcs-cost-simulator/
├── README.md                    # This documentation
├── requirements.txt             # Python dependencies
├── LICENSE                     # MIT License
└── gcs-cost-simulator-app/     # Main application
    ├── app.py                  # 🎯 Streamlit UI & orchestration
    ├── simulation.py           # 🧮 Core business logic & calculations
    ├── reports.py              # � PDF generation & export
    ├── utils.py                # 🛠️ Formatting & utility functions
    ├── config.py               # ⚙️ Configuration & pricing schemas
    └── requirements.txt        # App-specific dependencies
```

## 🔧 Technical Requirements

- **Python**: 3.8+
- **Core**: Streamlit 1.30.0+, Pandas, Matplotlib
- **Reports**: ReportLab for PDF generation
- **Analysis**: NumPy for calculations

See `requirements.txt` for complete dependency specifications.

## 🎯 What This Tool Does

**Compare GCS storage strategies** with real-world scenarios:

- **Data Growth**: Model TB-scale datasets with monthly growth
- **Access Patterns**: Configure realistic read/write frequencies
- **Cost Analysis**: See exactly where your money goes
- **Strategic Insights**: Get actionable recommendations for your use case

### 🎨 **Interactive Configuration**

- **Flexible Pricing**: Custom regional rates and service costs
- **Lifecycle Rules**: Configure age-based transitions (30/90/365 days)
- **Access Rates**: Model different data access frequencies
- **Simulation Length**: 12-60 months for long-term planning

## 📜 License

MIT License - use freely with attribution.

---

### 🎉 **Version 2.0 - Modular Architecture**

- 🏗️ **Clean Architecture**: Separated concerns across 5 focused modules
- 🔧 **Maintainable Code**: Easy to extend and modify
- � **Enhanced Analysis**: Improved simulation engine
- 🎯 **Production Ready**: Professional code structure and documentation
- ⚖️ **Side-by-Side Comparison**: Complete Autoclass vs Lifecycle analysis
- 💰 **Accurate Cost Modeling**: Retrieval costs and management fees
