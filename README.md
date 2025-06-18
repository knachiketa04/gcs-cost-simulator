
# 🚀 GCS Storage Strategy Simulator

A comprehensive interactive Streamlit application that compares Google Cloud Storage (GCS) Autoclass vs Lifecycle Policies with accurate cost modeling, intelligent unit scaling, and side-by-side analysis.

## ✨ Key Features

### 🔄 **Three Analysis Modes**
- **🤖 Autoclass Only**: Simulate intelligent, access-based storage optimization
- **📋 Lifecycle Only**: Model time-based storage transitions with custom rules
- **⚖️ Side-by-Side Comparison**: Direct cost and performance comparison

### 📊 **Advanced Analytics**
- **Intelligent Unit Scaling**: Automatic GB→TiB and $→$M conversion for large datasets
- **Custom Lifecycle Rules**: Configure transition days (Nearline, Coldline, Archive)
- **Real-time Cost Comparison**: Instant savings analysis and recommendations
- **Performance Optimized**: Handles 60+ month simulations efficiently

### 💰 **Comprehensive Cost Modeling**
- **Accurate GCS Pricing**: Regional pricing with custom configurations
- **Lifecycle-Specific Costs**: Retrieval costs and early deletion fees
- **No Hidden Costs**: Transparent Autoclass management fees vs lifecycle retrieval costs
- **TCO Analysis**: Total cost of ownership over extended periods

### 📈 **Professional Reporting**
- **Side-by-Side Charts**: Visual comparison of data distribution and costs
- **Detailed PDF Reports**: Comprehensive analysis with insights and recommendations
- **CSV Data Export**: Raw data for further analysis
- **Smart Insights**: Automated cost optimization recommendations

## 🚀 Quick Start

```bash
git clone https://github.com/yourusername/gcs-autoclass-simulator.git
cd gcs-autoclass-simulator
pip install -r requirements.txt
streamlit run streamlit_app/app.py
```

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

### 🔄 **Custom Lifecycle Rules** 
Configure transition timing for lifecycle policies:
- **Days to Nearline**: Custom transition timing (default: 30 days)
- **Days to Coldline**: Configurable cold storage transition (default: 90 days)  
- **Days to Archive**: Long-term storage timing (default: 365 days)
- **Validation**: Automatic rule validation and flow visualization

### 🎯 **Access Patterns**
Model realistic data usage:
- **Standard Tier Hotness**: Percentage staying actively accessed
- **Cold Tier Access**: Monthly access rates for Nearline, Coldline, Archive
- **Smart UI**: Conditional controls based on access patterns
- **Flow Visualization**: Clear data lifecycle progression display

## 💰 Advanced Cost Analysis

### 🏷️ **Autoclass Costs**
- **Storage Costs**: Multi-tier pricing (Standard→Nearline→Coldline→Archive)
- **Management Fee**: $0.0025 per eligible object per month
- **API Operations**: Class A (writes) and Class B (reads) 
- **No Retrieval Costs**: Key advantage over lifecycle policies

### 📋 **Lifecycle Policy Costs**
- **Storage Costs**: Same multi-tier pricing as Autoclass
- **Retrieval Costs**: $0.01-$0.05 per GB for accessing cold data
- **Early Deletion Fees**: Charges for accessing data before minimum storage duration
- **No Management Fees**: Cost advantage for large object counts

### ⚖️ **Side-by-Side Comparison**
- **Real-time Cost Difference**: Month-by-month savings analysis
- **Percentage Savings**: Clear ROI calculations
- **Visual Comparison**: Charts showing data distribution and cost trends
- **Strategic Recommendations**: Data-driven insights for optimal strategy selection

## 📈 Professional Features

### 🎨 **Smart Visualization**
- **Adaptive Units**: Automatic scaling (GB/TiB for storage, $/M for costs)
- **Multi-Strategy Charts**: Side-by-side data distribution comparison
- **Cost Difference Plots**: Visual savings analysis over time
- **Archive Utilization**: Track long-term storage optimization

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

## 🎯 Use Cases

### 💼 **Enterprise Planning**
- **TCO Analysis**: Long-term cost forecasting for budget planning
- **Strategy Selection**: Data-driven choice between Autoclass and lifecycle policies
- **Cost Optimization**: Identify optimal access patterns and transition timing
- **Capacity Planning**: Model data growth scenarios

### 🔍 **Decision Support**
- **Autoclass vs Lifecycle**: Clear comparison with savings analysis
- **Custom Rule Testing**: Validate lifecycle policy configurations
- **Access Pattern Impact**: Understand cost implications of usage patterns
- **Regional Pricing**: Model costs across different GCP regions

### 📚 **Educational & Training**
- **GCS Strategy Understanding**: Learn Autoclass vs lifecycle behavior
- **Cost Modeling**: Understand GCS pricing components
- **Optimization Techniques**: Best practices for storage cost management
- **Hands-on Analysis**: Interactive learning with real scenarios

## 🔧 Technical Accuracy

### ✅ **GCS Autoclass Modeling**
- **Correct Transition Timing**: 30/90/365 day thresholds
- **Access-Based Intelligence**: Hot vs cold data behavior
- **Management Fee Calculation**: Per eligible object pricing
- **Re-promotion Logic**: Proper Standard tier return behavior

### ✅ **Lifecycle Policy Modeling**  
- **Time-Based Transitions**: Configurable day-based rules
- **Retrieval Cost Calculation**: Accurate cold data access pricing
- **No Re-promotion**: One-way transitions (realistic behavior)
- **Early Deletion Fees**: Minimum storage duration enforcement

### ✅ **Performance Optimizations**
- **Generation Batching**: Efficient data aging simulation
- **Smart Filtering**: Remove negligible data amounts
- **Memory Management**: Handle long-term simulations
- **Progressive Loading**: Visual feedback for complex calculations

## 📦 Advanced Configuration

### 💰 **Custom Pricing**
- **Regional Support**: Iowa (us-central1) default with custom options
- **Contract Pricing**: Model enterprise pricing agreements
- **Lifecycle Costs**: Retrieval and early deletion fee configuration
- **API Pricing**: Separate Class A/B operation costs

### 🎛️ **Simulation Controls**
- **Performance Hints**: Automatic optimization for long simulations
- **Progress Indicators**: Visual feedback during calculations
- **Error Validation**: Input validation and boundary checking
- **Smart Defaults**: Realistic starting configurations

## 📸 Screenshots

![Strategy Comparison](assets/strategy-comparison.png)
![Lifecycle Configuration](assets/lifecycle-config.png)  
![Cost Analysis](assets/cost-analysis.png)

## 🔧 Technical Requirements

- Python 3.8+
- Streamlit 1.30.0+
- Pandas (data processing)
- Matplotlib (visualization)
- ReportLab (PDF generation)

See `requirements.txt` for complete dependency list.

## 📊 Sample Scenarios

### 🏢 **Enterprise Archive Scenario**
- 100 TiB initial data, 5% monthly growth
- 80% large objects (Autoclass eligible)
- Low access rates (10% Standard, 5% cold tiers)
- **Result**: Lifecycle saves ~15% due to no management fees

### 🔄 **Dynamic Access Scenario**  
- 10 TiB initial data, 2% monthly growth
- 90% large objects
- High access rates (50% Standard, 20% cold tiers)
- **Result**: Autoclass saves ~25% due to no retrieval costs

### 🎯 **Mixed Workload Scenario**
- 50 TiB initial data, 1% monthly growth  
- 70% large objects
- Medium access rates (30% Standard, 15% cold tiers)
- **Result**: Close comparison, strategy choice depends on specific access patterns

## 🤝 Contributing

Contributions welcome! Areas for enhancement:
- Additional GCP regions and pricing
- Multi-cloud storage comparisons  
- Advanced access pattern modeling
- Performance optimizations
- UI/UX improvements

## 📜 License

MIT License - use freely with attribution.

---

### 🎉 **New in v2.0**
- ⚖️ **Side-by-Side Comparison**: Complete Autoclass vs Lifecycle analysis
- 📋 **Custom Lifecycle Rules**: Configurable transition timing
- 🎯 **Smart Unit Scaling**: Automatic GB→TiB and $→$M conversion
- 📊 **Enhanced Reporting**: Comprehensive PDF reports with strategic insights
- 🔄 **Three Analysis Modes**: Flexible comparison strategies
- 💰 **Accurate Cost Modeling**: Retrieval costs and early deletion fees
