
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

A comprehensive interactive Streamlit application that compares Google Cloud Storage (GCS) Autoclass vs Lifecycle Policies with accurate cost modeling, intelligent unit scaling, and side-by-side analysis.

## ✨ Key Features

### 🔄 **Three Analysis Modes**
- **🤖 Autoclass Only**: Simulate intelligent, access-based storage optimization
- **📋 Lifecycle Only**: Model time-based storage transitions with custom rules
- **⚖️ Side-by-Side Comparison**: Direct cost and performance comparison

### 💰 **Comprehensive Cost Modeling**
- **Accurate GCS Pricing**: Regional pricing with custom configurations
- **Lifecycle-Specific Costs**: Retrieval costs and early deletion fees
- **No Hidden Costs**: Transparent Autoclass management fees vs lifecycle retrieval costs
- **TCO Analysis**: Total cost of ownership over extended periods


## 🚀 Quick Start

```bash
git clone https://github.com/knachiketa04/gcs-cost-simulator.git
cd gcs-cost-simulator
pip install -r requirements.txt
streamlit run streamlit_app/app.py
```

> **📍 Main Application**: The complete simulator is implemented in `streamlit_app/app.py` (1500+ lines of sophisticated logic)

## 📊 Simulation Configuration

### 🎯 **Analysis Mode Selection**
Choose your comparison strategy:
- **Autoclass Only**: Focus on intelligent access-based optimization
- **Lifecycle Only**: Analyze time-based policy performance  
- **Side-by-Side**: Compare both strategies with cost difference analysis

### 📁 **Data Configuration**
- **Initial Data Size**: Starting data volume (auto-scales GB→TiB)
- **Growth Pattern**: Monthly percentage growth or fixed amounts
- **Simulation Period**: 12-60 months for comprehensive TCO analysis
- **Object Characteristics**: Size distribution affecting Autoclass eligibility

### 📊 **Detailed Reporting**
- **Interactive Tables**: Formatted data with smart units
- **Cost Breakdown**: Storage, API, management fees, retrieval costs
- **Key Insights**: Automated analysis and optimization recommendations
- **Export Options**: CSV data and comprehensive PDF reports

### 📋 **PDF Report Generation**
- **Executive Summary**: High-level cost and strategy analysis
- **Detailed Breakdowns**: Monthly data and cost progression
- **Comparison Analysis**: Side-by-side strategy evaluation (comparison mode)
- **Strategic Insights**: Data-driven recommendations and decision factors

## 🔧 Technical Requirements

- Python 3.8+
- Streamlit 1.30.0+
- Pandas (data processing)
- Matplotlib (visualization)
- ReportLab (PDF generation)

See `requirements.txt` for complete dependency list.

## 📁 Repository Structure

```
gcs-cost-simulator/
├── README.md              # This documentation
├── requirements.txt       # Python dependencies
├── LICENSE               # MIT License
└── streamlit_app/
    └── app.py           # 🎯 Main application (1500+ lines)
```

> **Note**: All functionality is contained in the single `streamlit_app/app.py` file for simplicity and maintainability.


## 📜 License

MIT License - use freely with attribution.

---

### 🎉 **Latest Release v1.0**
- ⚖️ **Side-by-Side Comparison**: Complete Autoclass vs Lifecycle analysis
- 📋 **Custom Lifecycle Rules**: Configurable transition timing
- 🎯 **Smart Unit Scaling**: Automatic GB→TiB and $→$M conversion
- 📊 **Enhanced Reporting**: Comprehensive PDF reports with strategic insights
- 🔄 **Three Analysis Modes**: Flexible comparison strategies
- 💰 **Accurate Cost Modeling**: Retrieval costs and early deletion fees