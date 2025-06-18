
# 🚀 GCS Autoclass Simulator

A comprehensive visual and interactive Streamlit application to simulate Google Cloud Storage (GCS) Autoclass behavior with accurate cost modeling, including:

- **Flexible Analysis Periods**: 12-60 months for long-term TCO planning
- **Accurate Storage Class Transitions**: Standard → Nearline (30 days) → Coldline (90 days) → Archive (365 days)
- **Smart Access-triggered Re-promotion**: Instant promotion back to Standard on data access
- **Autoclass Management Fee Calculation**: Based on object eligibility (>128 KiB only)
- **Early Deletion Fees**: For data accessed before minimum storage duration
- **Generation-based Object Tracking**: Proper lifecycle modeling with object aging
- **Comprehensive Cost Breakdown**: Storage, retrieval, API operations, management fees
- **Advanced Visualizations**: Data distribution and cost trends over time

## 📦 Enhanced Features

- ✅ **Accurate Day-based Transitions** (30, 90, 365 days)
- ✅ **Object Size Eligibility** (<128 KiB stays in Standard)
- ✅ **Generation Tracking** for proper data aging
- ✅ **Re-promotion Logic** with new generation creation
- ✅ **Early Deletion Penalties** for premature access
- ✅ **Extended TCO Analysis** (12-60 months)
- ✅ **Regional Autoclass Pricing** (accurate GCP rates)
- ✅ **Cost Validation Alerts** for optimization insights
- ✅ **CSV Export** with detailed monthly breakdown
- ✅ **Autoclass vs Manual Lifecycle** comparison guide

## 📋 Installation

```bash
git clone https://github.com/yourusername/gcs-autoclass-simulator.git
cd gcs-autoclass-simulator
pip install -r requirements.txt
streamlit run streamlit_app/app.py
```

## 🧮 Comprehensive Inputs

### Analysis Configuration
- **TCO Period**: 12-60 months for long-term cost planning
- **Monthly Write Volume**: GB of new data ingested monthly

### Object Characteristics
- **Average Object Size**: In KiB (affects eligibility for Autoclass)
- **Large Object Percentage**: % of data >128 KiB (Autoclass eligible)

### Access Patterns
- **Nearline Access Rate**: % of Nearline data accessed monthly
- **Coldline Access Rate**: % of Coldline data accessed monthly  
- **Archive Access Rate**: % of Archive data accessed monthly

### API Operations
- **Class A Operations**: Write operations per month
- **Class B Operations**: Read operations per month

## 📊 Detailed Output

### Cost Breakdown
- **Storage Costs**: By tier (Standard, Nearline, Coldline, Archive)
- **Retrieval Costs**: Based on access patterns and tier pricing
- **Early Deletion Fees**: For data accessed before minimum duration
- **API Operation Costs**: Class A and Class B operations
- **Autoclass Management Fee**: Per eligible object per month

### Visualizations
- **Data Distribution Chart**: Growth across storage classes over time
- **Cost Trend Analysis**: Monthly cost breakdown by category
- **Key Performance Metrics**: Total data, archive percentage, active generations

### Insights & Validation
- **Cost Optimization Alerts**: When management fees exceed storage costs
- **Data Lifecycle Analysis**: Transition patterns and final distribution
- **Autoclass vs Manual Comparison**: Decision-making guidance

## 🎯 Use Cases

- **TCO Planning**: Long-term cost forecasting for GCS Autoclass
- **Access Pattern Optimization**: Understanding cost impact of data access frequency
- **Storage Strategy Comparison**: Autoclass vs manual lifecycle policies
- **Budget Planning**: Detailed cost breakdown for financial planning
- **Educational Tool**: Understanding GCS Autoclass behavior and pricing

## 📸 Screenshot

_You can add screenshots to `assets/` and reference here._

## 🔧 Technical Accuracy

- ✅ Implements correct GCS Autoclass transition timings (30/90/365 days)
- ✅ Accurate Regional Autoclass pricing (as of 2024)
- ✅ Proper object eligibility rules (128 KiB threshold)
- ✅ Early deletion fee calculations
- ✅ Generation-based data tracking for realistic aging
- ✅ Re-promotion logic with new generation creation

## 📜 License

MIT License – use freely with attribution.
