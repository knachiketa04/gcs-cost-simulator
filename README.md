
# 🚀 GCS Autoclass Cost Simulator

A comprehensive interactive Streamlit application to simulate Google Cloud Storage (GCS) Autoclass behavior with accurate cost modeling and lifecycle transitions.

## ✨ Key Features

- **Accurate GCS Autoclass Modeling**: Proper data transitions (Standard → Nearline → Coldline → Archive)
- **Flexible Growth Patterns**: Both fixed data scenarios and percentage-based growth models
- **Configurable Pricing**: Support for different GCP regions and custom pricing contracts
- **Performance Optimized**: Handles long-term simulations (60+ months) efficiently
- **Professional UI**: Clean interface with smart number formatting and progress indicators
- **No Retrieval Costs**: Unlike manual lifecycle policies, Autoclass doesn't charge for retrievals
- **Object Count Tracking**: Accurate autoclass management fee calculation

## 🚀 Quick Start

```bash
git clone https://github.com/yourusername/gcs-autoclass-simulator.git
cd gcs-autoclass-simulator
pip install -r requirements.txt
streamlit run streamlit_app/app.py
```

## 📊 Simulation Inputs

### Data Configuration
- **Initial Data Size**: Starting data volume in GB
- **Data Growth Pattern**: Monthly growth rate (percentage or fixed amount)
- **Simulation Period**: 12-60 months for comprehensive TCO analysis

### Object Characteristics  
- **Average Object Size**: In KiB (affects Autoclass eligibility - must be >128 KiB)
- **Large Object Percentage**: Percentage of data eligible for Autoclass transitions

### Access Patterns
- **Nearline Access Rate**: Monthly access percentage for Nearline data
- **Coldline Access Rate**: Monthly access percentage for Coldline data  
- **Archive Access Rate**: Monthly access percentage for Archive data

### API Operations
- **Class A Operations**: Write/delete operations per month
- **Class B Operations**: Read/list operations per month

## 💰 Comprehensive Cost Analysis

### Storage Costs
- **Multi-tier Pricing**: Accurate costs for Standard, Nearline, Coldline, and Archive storage
- **Regional Pricing**: Default Iowa (us-central1) with configurable custom pricing
- **Autoclass Management Fee**: $0.0025 per object per month (for eligible objects >128 KiB)

### Operational Costs
- **API Operation Pricing**: Separate Class A and Class B operation costs
- **Early Deletion Fees**: Charged when data is accessed before minimum storage duration
- **No Retrieval Costs**: Key advantage of Autoclass over manual lifecycle policies

## 📈 Advanced Features

### Performance Optimizations
- **Generation Batching**: Efficient handling of data generations for long simulations
- **Smart Filtering**: Automatic filtering of tiny data amounts (<1MB) to improve performance
- **Progress Indicators**: Visual feedback for simulations longer than 24 months

### Data Visualization
- **Monthly Cost Breakdown**: Detailed charts showing cost trends over time
- **Storage Distribution**: Visual representation of data across storage classes
- **Key Metrics Dashboard**: Total costs, data distribution, and optimization insights

### Professional Formatting
- **Smart Number Display**: Scientific notation for very small values, appropriate precision for costs
- **Configurable Pricing**: Easy-to-use interface for custom pricing scenarios
- **Export Capabilities**: Detailed CSV export with monthly breakdowns

## 🎯 Use Cases

- **TCO Planning**: Long-term cost forecasting for GCS Autoclass adoption
- **Storage Strategy Analysis**: Compare costs across different data growth scenarios  
- **Budget Planning**: Detailed monthly cost projections for financial planning
- **Pricing Negotiations**: Model costs under different GCP contract terms
- **Educational Tool**: Understand GCS Autoclass behavior and cost implications

## 🔧 Technical Accuracy

This simulator implements Google Cloud Storage Autoclass behavior accurately:

- ✅ **Correct Transition Timing**: 30 days to Nearline, 90 days to Coldline, 365 days to Archive
- ✅ **Object Size Eligibility**: Only objects >128 KiB are eligible for Autoclass transitions
- ✅ **No Retrieval Costs**: Unlike manual lifecycle policies, no charges for data access
- ✅ **Management Fee Calculation**: $0.0025 per eligible object per month
- ✅ **Early Deletion Logic**: Proper minimum storage duration enforcement
- ✅ **Regional Pricing**: Accurate GCP pricing for supported regions

## 📋 Requirements

- Python 3.8+
- Streamlit
- Pandas  
- Plotly

See `requirements.txt` for complete dependency list.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.

## 📜 License

MIT License - see LICENSE file for details.

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
