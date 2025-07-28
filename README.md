# 🚀 GCS Storage Strategy Simulator

## ⚠️ **Educational Disclaimer**

**This tool is designed for educational purposes and cost estimation guidance only.** While it models GCS pricing and behavior based on publicly available Google Cloud documentation, it should not be used as the sole basis for commercial decisions or production deployments.

**For commercial use and production environments:**

- Always conduct thorough testing with your actual data and access patterns
- Consult official [Google Cloud Storage documentation](https://cloud.google.com/storage/docs)
- Validate pricing with the [Google Cloud Pricing Calculator](https://cloud.google.com/products/calculator)
- Consider engaging with Google Cloud specialists for enterprise scenarios

**The authors are not responsible for any costs or issues arising from decisions based solely on this simulator.**

---

A production-ready Streamlit application that compares Google Cloud Storage (GCS) Autoclass vs Lifecycle Policies with accurate cost modeling, intelligent unit scaling, and comprehensive TCO analysis.

## ✨ Key Features

### 🔄 **Three Analysis Modes**

- **🤖 Autoclass Only**: Intelligent, access-based storage optimization with configurable terminal storage class
- **📋 Lifecycle Only**: Time-based storage transitions with custom transition rules
- **⚖️ Side-by-Side Comparison**: Direct cost and performance comparison with strategic insights

### 💰 **Enterprise-Grade Cost Modeling**

- **Accurate GCS Pricing**: Regional pricing (default: Iowa us-central1) with full customization
- **Strategy-Specific Costs**: Autoclass management fees vs lifecycle retrieval costs
- **Transition Costs**: Proper modeling of lifecycle transition operation charges
- **Object Size Compliance**: Strict 128 KiB Autoclass eligibility enforcement

### 📊 **Smart Analytics & Export**

- **Auto-Scaling Units**: Intelligent GB→TiB, $→$M scaling for large datasets
- **Professional Reports**: PDF executive summaries with cost breakdowns
- **Raw Data Export**: CSV export for further analysis and integration
- **TCO Validation**: Comprehensive error checking and configuration warnings

## 🚀 Quick Start

```bash
git clone https://github.com/knachiketa04/gcs-cost-simulator.git
cd gcs-cost-simulator
pip install -r requirements.txt
streamlit run gcs-cost-simulator-app/app.py
```

## 🏗️ Architecture

Clean, modular design with 6 focused components:

```
gcs-cost-simulator/
├── README.md & LICENSE         # Documentation
├── requirements.txt            # Dependencies
└── gcs-cost-simulator-app/     # Core application (6 files)
    ├── app.py                  # 🎯 Streamlit UI & orchestration
    ├── simulation.py           # 🧮 Generation-based cost modeling
    ├── reports.py              # 📄 PDF/CSV export with templates
    ├── utils.py                # 🛠️ Smart formatting & UI helpers
    ├── config.py               # ⚙️ Pricing schemas & defaults
    └── validation.py           # ✅ TCO-focused input validation
```

**Requirements**: Python 3.8+, Streamlit 1.30.0+, Pandas, Matplotlib, ReportLab

## 🎯 Core Capabilities

**Compare GCS storage strategies** with realistic enterprise scenarios:

- **Data Growth Modeling**: TB-scale datasets with configurable monthly growth (0-50%)
- **Access Pattern Configuration**: Conditional UI adapts based on terminal storage and access rates
- **Generation-Based Tracking**: Accurate data aging and lifecycle cost calculations
- **Long-Term Analysis**: 12-60 month simulations with generation optimization for performance

### 🎨 **Advanced Features**

- **Terminal Storage Configuration**: Nearline (GCS default) or Archive terminal classes
- **Smart UI Logic**: Conditional controls hide irrelevant options based on configuration
- **Cost Impact Analysis**: High-impact warnings for configurations affecting >30% of costs
- **Chart Visualization**: Side-by-side data distribution and cost comparison charts

## 📊 Default Configuration

- **Storage Classes**: Standard → Nearline (30d) → Coldline (90d) → Archive (365d)
- **Access Rates**: Standard 40% hot, Nearline 20%, Coldline 15%, Archive 15%
- **Object Sizes**: Large objects 512 KiB (Autoclass eligible), Small objects 64 KiB
- **Terminal Storage**: Archive (full progression enabled)

## 📜 License

MIT License - use freely with attribution.

---

### 🎉 **Version 2.0 - Production Ready**

✅ **Streamlined Codebase**: 6 essential modules with clear separation of concerns  
✅ **Accurate Cost Modeling**: Proper lifecycle transition costs and Autoclass compliance  
✅ **Enhanced UI/UX**: Conditional controls and smart validation with minimal noise  
✅ **Professional Export**: Template-driven PDF reports and comprehensive CSV data
