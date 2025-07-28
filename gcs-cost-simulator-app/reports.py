# reports.py - PDF report generation and export functionality

import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from datetime import datetime
from utils import format_storage_value, format_cost_value
from config import PDF_TEMPLATES


def create_pdf_styles():
    """Create custom PDF styles"""
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.darkblue,
        alignment=1,  # Center alignment
        spaceAfter=30
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.darkblue,
        spaceBefore=20,
        spaceAfter=10
    )
    
    return styles, title_style, heading_style


def generate_executive_summary(analysis_mode, autoclass_df=None, lifecycle_df=None, months=12, 
                             initial_data_gb=0, monthly_growth_rate=0, 
                             standard_access_rate=0, nearline_read_rate=0, 
                             coldline_read_rate=0, archive_read_rate=0, lifecycle_rules=None):
    """Generate executive summary content"""
    
    if analysis_mode == "comparison":
        autoclass_total_cost = autoclass_df["Total Cost ($)"].sum()
        lifecycle_total_cost = lifecycle_df["Total Cost ($)"].sum()
        cost_difference = autoclass_total_cost - lifecycle_total_cost
        savings_percentage = (abs(cost_difference) / max(autoclass_total_cost, lifecycle_total_cost)) * 100
        
        winner = "Lifecycle Policy" if cost_difference > 0 else "Autoclass"
        savings_amount = abs(cost_difference)
        
        final_autoclass_data = autoclass_df['Total Data (GB)'].iloc[-1]
        
        summary_text = f"""
        <b>Analysis Period:</b> {months} months<br/>
        <b>Initial Data:</b> {format_storage_value(initial_data_gb)}<br/>
        <b>Monthly Growth Rate:</b> {monthly_growth_rate*100:.1f}%<br/>
        <b>Final Data Volume:</b> {format_storage_value(final_autoclass_data)}<br/>
        <br/>
        <b>Cost Comparison Results:</b><br/>
        • Autoclass Total Cost: {format_cost_value(autoclass_total_cost)}<br/>
        • Lifecycle Total Cost: {format_cost_value(lifecycle_total_cost)}<br/>
        • <b>Winner: {winner}</b> (saves {format_cost_value(savings_amount)} / {savings_percentage:.1f}%)<br/>
        <br/>
        <b>Access Pattern Summary:</b><br/>
        • Standard Hot Data: {standard_access_rate*100:.1f}% stays hot<br/>
        • Nearline Access: {nearline_read_rate*100:.1f}%/month<br/>
        • Coldline Access: {coldline_read_rate*100:.1f}%/month<br/>
        • Archive Access: {archive_read_rate*100:.1f}%/month
        """
        
        if lifecycle_rules:
            summary_text += f"""<br/>
            <b>Lifecycle Configuration:</b><br/>
            • Nearline Transition: {lifecycle_rules['nearline_days']} days<br/>
            • Coldline Transition: {lifecycle_rules['coldline_days']} days<br/>
            • Archive Transition: {lifecycle_rules['archive_days']} days
            """
            
    else:
        # Single strategy analysis
        df = autoclass_df if analysis_mode == "autoclass" else lifecycle_df
        total_cost = df["Total Cost ($)"].sum()
        avg_monthly_cost = total_cost / months if months > 0 else 0
        final_data_gb = df['Total Data (GB)'].iloc[-1]
        final_archive_gb = df['Archive (GB)'].iloc[-1]
        archive_percentage = (final_archive_gb/final_data_gb*100) if final_data_gb > 0 else 0
        
        strategy_name = "Autoclass" if analysis_mode == "autoclass" else "Lifecycle Policy"
        
        summary_text = f"""
        <b>Analysis Period:</b> {months} months<br/>
        <b>Strategy:</b> {strategy_name}<br/>
        <b>Initial Data:</b> {format_storage_value(initial_data_gb)}<br/>
        <b>Monthly Growth Rate:</b> {monthly_growth_rate*100:.1f}%<br/>
        <b>Total Cost:</b> {format_cost_value(total_cost)}<br/>
        <b>Average Monthly Cost:</b> {format_cost_value(avg_monthly_cost)}<br/>
        <b>Final Data Volume:</b> {format_storage_value(final_data_gb)}<br/>
        <b>Archive Tier Usage:</b> {archive_percentage:.1f}%<br/>
        <br/>
        <b>Access Pattern Summary:</b><br/>
        • Standard Hot Data: {standard_access_rate*100:.1f}% stays hot<br/>
        • Nearline Access: {nearline_read_rate*100:.1f}%/month<br/>
        • Coldline Access: {coldline_read_rate*100:.1f}%/month<br/>
        • Archive Access: {archive_read_rate*100:.1f}%/month
        """
        
        if analysis_mode == "lifecycle" and lifecycle_rules:
            summary_text += f"""<br/>
            <b>Lifecycle Configuration:</b><br/>
            • Nearline Transition: {lifecycle_rules['nearline_days']} days<br/>
            • Coldline Transition: {lifecycle_rules['coldline_days']} days<br/>
            • Archive Transition: {lifecycle_rules['archive_days']} days
            """
    
    return summary_text


def generate_cost_breakdown_table(analysis_mode, autoclass_df=None, lifecycle_df=None):
    """Generate cost breakdown table data"""
    
    if analysis_mode == "comparison":
        autoclass_total_cost = autoclass_df["Total Cost ($)"].sum()
        lifecycle_total_cost = lifecycle_df["Total Cost ($)"].sum()
        cost_difference = autoclass_total_cost - lifecycle_total_cost
        
        autoclass_storage = autoclass_df["Storage Cost ($)"].sum()
        autoclass_api = autoclass_df["API Cost ($)"].sum()
        autoclass_fee = autoclass_df["Autoclass Fee ($)"].sum()
        
        lifecycle_storage = lifecycle_df["Storage Cost ($)"].sum()
        lifecycle_api = lifecycle_df["API Cost ($)"].sum()
        lifecycle_retrieval = lifecycle_df["Retrieval Cost ($)"].sum()
        
        cost_data = [
            ['Strategy', 'Storage Cost', 'API Cost', 'Special Cost', 'Total Cost'],
            ['Autoclass', format_cost_value(autoclass_storage), format_cost_value(autoclass_api), 
             f'{format_cost_value(autoclass_fee)} (Mgmt)', format_cost_value(autoclass_total_cost)],
            ['Lifecycle', format_cost_value(lifecycle_storage), format_cost_value(lifecycle_api), 
             f'{format_cost_value(lifecycle_retrieval)} (Retr)', format_cost_value(lifecycle_total_cost)],
            ['Difference', format_cost_value(autoclass_storage - lifecycle_storage), 
             format_cost_value(autoclass_api - lifecycle_api), 
             format_cost_value(autoclass_fee - lifecycle_retrieval), 
             format_cost_value(cost_difference)]
        ]
    else:
        # Single strategy breakdown
        df = autoclass_df if analysis_mode == "autoclass" else lifecycle_df
        total_storage = df["Storage Cost ($)"].sum()
        total_api = df["API Cost ($)"].sum()
        total_cost = df["Total Cost ($)"].sum()
        
        if analysis_mode == "autoclass":
            special_cost = df["Autoclass Fee ($)"].sum()
            special_label = "Autoclass Fee"
        else:
            special_cost = df["Retrieval Cost ($)"].sum()
            special_label = "Retrieval Cost"
        
        storage_pct = (total_storage / total_cost * 100) if total_cost > 0 else 0
        api_pct = (total_api / total_cost * 100) if total_cost > 0 else 0
        special_pct = (special_cost / total_cost * 100) if total_cost > 0 else 0
        
        cost_data = [
            ['Cost Component', 'Amount', 'Percentage'],
            ['Storage Costs', format_cost_value(total_storage), f'{storage_pct:.1f}%'],
            ['API Operations', format_cost_value(total_api), f'{api_pct:.1f}%'],
            [special_label, format_cost_value(special_cost), f'{special_pct:.1f}%'],
            ['Total', format_cost_value(total_cost), '100.0%']
        ]
    
    return cost_data


def generate_monthly_table(analysis_mode, autoclass_df=None, lifecycle_df=None):
    """Generate monthly breakdown table data"""
    
    if analysis_mode == "comparison":
        max_data = max(autoclass_df['Total Data (GB)'].max(), lifecycle_df['Total Data (GB)'].max())
        data_unit = "TiB" if max_data >= 1024 else "GB"
        data_factor = 1024 if data_unit == "TiB" else 1
        
        display_months = min(12, len(autoclass_df))
        
        table_data = [['Month', f'Autoclass Cost', f'Lifecycle Cost', 'Cost Difference', f'Archive Data ({data_unit})']]
        
        for i in range(display_months):
            auto_row = autoclass_df.iloc[i]
            life_row = lifecycle_df.iloc[i]
            cost_diff = auto_row['Total Cost ($)'] - life_row['Total Cost ($)']
            archive_data = auto_row['Archive (GB)'] / data_factor
            
            table_data.append([
                auto_row['Month'],
                format_cost_value(auto_row['Total Cost ($)']),
                format_cost_value(life_row['Total Cost ($)']),
                format_cost_value(cost_diff),
                f"{archive_data:,.2f}"
            ])
        
        if len(autoclass_df) > 12:
            table_data.append(['...', '...', '...', '...', '...'])
            # Add final month
            auto_final = autoclass_df.iloc[-1]
            life_final = lifecycle_df.iloc[-1]
            final_cost_diff = auto_final['Total Cost ($)'] - life_final['Total Cost ($)']
            final_archive = auto_final['Archive (GB)'] / data_factor
            
            table_data.append([
                auto_final['Month'],
                format_cost_value(auto_final['Total Cost ($)']),
                format_cost_value(life_final['Total Cost ($)']),
                format_cost_value(final_cost_diff),
                f"{final_archive:,.2f}"
            ])
    else:
        # Single strategy table
        df = autoclass_df if analysis_mode == "autoclass" else lifecycle_df
        
        max_data = df['Total Data (GB)'].max()
        data_unit = "TiB" if max_data >= 1024 else "GB"
        data_factor = 1024 if data_unit == "TiB" else 1
        
        display_months = min(12, len(df))
        
        if analysis_mode == "autoclass":
            table_data = [['Month', f'Total Data ({data_unit})', 'Storage Cost', 'Autoclass Fee', 'Total Cost']]
            for i in range(display_months):
                row = df.iloc[i]
                table_data.append([
                    row['Month'],
                    f"{row['Total Data (GB)']/data_factor:,.2f}",
                    format_cost_value(row['Storage Cost ($)']),
                    format_cost_value(row['Autoclass Fee ($)']),
                    format_cost_value(row['Total Cost ($)'])
                ])
        else:
            table_data = [['Month', f'Total Data ({data_unit})', 'Storage Cost', 'Retrieval Cost', 'Total Cost']]
            for i in range(display_months):
                row = df.iloc[i]
                table_data.append([
                    row['Month'],
                    f"{row['Total Data (GB)']/data_factor:,.2f}",
                    format_cost_value(row['Storage Cost ($)']),
                    format_cost_value(row['Retrieval Cost ($)']),
                    format_cost_value(row['Total Cost ($)'])
                ])
        
        if len(df) > 12:
            table_data.append(['...', '...', '...', '...', '...'])
            # Add final month
            final_row = df.iloc[-1]
            if analysis_mode == "autoclass":
                table_data.append([
                    final_row['Month'],
                    f"{final_row['Total Data (GB)']/data_factor:,.2f}",
                    format_cost_value(final_row['Storage Cost ($)']),
                    format_cost_value(final_row['Autoclass Fee ($)']),
                    format_cost_value(final_row['Total Cost ($)'])
                ])
            else:
                table_data.append([
                    final_row['Month'],
                    f"{final_row['Total Data (GB)']/data_factor:,.2f}",
                    format_cost_value(final_row['Storage Cost ($)']),
                    format_cost_value(final_row['Retrieval Cost ($)']),
                    format_cost_value(final_row['Total Cost ($)'])
                ])
    
    return table_data


def generate_insights_content(analysis_mode, autoclass_df=None, lifecycle_df=None):
    """Generate insights and recommendations content"""
    
    if analysis_mode == "comparison":
        autoclass_total_cost = autoclass_df["Total Cost ($)"].sum()
        lifecycle_total_cost = lifecycle_df["Total Cost ($)"].sum()
        cost_difference = autoclass_total_cost - lifecycle_total_cost
        savings_percentage = (abs(cost_difference) / max(autoclass_total_cost, lifecycle_total_cost)) * 100
        
        winner_strategy = "Lifecycle Policy" if cost_difference > 0 else "Autoclass"
        insights_text = f"""
        <b>Strategy Comparison Results:</b><br/>
        • <b>Recommended Strategy: {winner_strategy}</b><br/>
        • Cost savings: {format_cost_value(abs(cost_difference))} ({savings_percentage:.1f}%)<br/>
        • Both strategies achieve similar archive utilization<br/>
        <br/>
        <b>Decision Factors:</b><br/>
        • {"Lifecycle saves money due to no management fees and predictable transitions" if cost_difference > 0 else "Autoclass saves money through intelligent optimization and no retrieval costs"}<br/>
        • {"Lifecycle requires manual rule configuration but offers more control" if cost_difference > 0 else "Autoclass provides automatic optimization with minimal configuration"}
        """
    else:
        strategy_name = "Autoclass" if analysis_mode == "autoclass" else "Lifecycle Policy"
        df = autoclass_df if analysis_mode == "autoclass" else lifecycle_df
        
        storage_percentage = (df["Storage Cost ($)"].sum() / df["Total Cost ($)"].sum() * 100)
        
        if analysis_mode == "autoclass":
            mgmt_percentage = (df["Autoclass Fee ($)"].sum() / df["Total Cost ($)"].sum() * 100)
            insights_text = f"""
            <b>{strategy_name} Analysis Results:</b><br/>
            • Storage costs represent {storage_percentage:.1f}% of total expenses<br/>
            • Autoclass management fee: {mgmt_percentage:.1f}% of total cost<br/>
            <br/>
            <b>Autoclass Benefits:</b><br/>
            • Automatic tier transitions based on access patterns<br/>
            • No retrieval costs for accessing cold data<br/>
            • Minimal configuration required<br/>
            • Intelligent optimization adapts to changing patterns
            """
        else:
            retrieval_percentage = (df["Retrieval Cost ($)"].sum() / df["Total Cost ($)"].sum() * 100)
            insights_text = f"""
            <b>{strategy_name} Analysis Results:</b><br/>
            • Storage costs represent {storage_percentage:.1f}% of total expenses<br/>
            • Retrieval costs: {retrieval_percentage:.1f}% of total cost<br/>
            <br/>
            <b>Lifecycle Policy Benefits:</b><br/>
            • No management fees (cost-effective for large datasets)<br/>
            • Predictable, time-based transitions<br/>
            • Full control over transition timing<br/>
            • Optimal for well-understood data lifecycle patterns
            """
    
    return insights_text


def generate_pdf_report(analysis_mode, autoclass_df=None, lifecycle_df=None, months=12, 
                       initial_data_gb=0, monthly_growth_rate=0, pricing=None, 
                       standard_access_rate=0, nearline_read_rate=0, coldline_read_rate=0, 
                       archive_read_rate=0, lifecycle_rules=None):
    """Generate a comprehensive PDF report using template-driven approach"""
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    story = []
    styles, title_style, heading_style = create_pdf_styles()
    
    # Determine template and analysis mode
    if analysis_mode == "⚖️ Side-by-Side Comparison":
        template_key = "comparison"
        mode_key = "comparison"
    elif analysis_mode == "🤖 Autoclass Only":
        template_key = "autoclass"
        mode_key = "autoclass"
    else:  # Lifecycle Only
        template_key = "lifecycle" 
        mode_key = "lifecycle"
    
    template = PDF_TEMPLATES[template_key]
    
    # Title and Header
    story.append(Paragraph(template["title"], title_style))
    story.append(Paragraph(template["subtitle"], styles['Normal']))
    story.append(Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Generate sections based on template
    for section in template["sections"]:
        if section == "executive_summary":
            story.append(Paragraph("Executive Summary", heading_style))
            summary_text = generate_executive_summary(
                mode_key, autoclass_df, lifecycle_df, months, initial_data_gb, 
                monthly_growth_rate, standard_access_rate, nearline_read_rate, 
                coldline_read_rate, archive_read_rate, lifecycle_rules
            )
            story.append(Paragraph(summary_text, styles['Normal']))
            story.append(Spacer(1, 20))
            
        elif section == "cost_breakdown":
            story.append(Paragraph("Cost Breakdown Analysis", heading_style))
            cost_data = generate_cost_breakdown_table(mode_key, autoclass_df, lifecycle_df)
            
            cost_table = Table(cost_data)
            cost_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
                ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(cost_table)
            story.append(PageBreak())
            
        elif section in ["monthly_comparison", "monthly_breakdown"]:
            title = "Detailed Monthly Comparison" if section == "monthly_comparison" else "Detailed Monthly Breakdown"
            story.append(Paragraph(title, heading_style))
            
            table_data = generate_monthly_table(mode_key, autoclass_df, lifecycle_df)
            
            data_table = Table(table_data)
            data_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(data_table)
            story.append(Spacer(1, 20))
            
        elif section == "insights":
            story.append(Paragraph("Key Insights and Recommendations", heading_style))
            insights_text = generate_insights_content(mode_key, autoclass_df, lifecycle_df)
            story.append(Paragraph(insights_text, styles['Normal']))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_csv_export(analysis_mode, autoclass_df=None, lifecycle_df=None):
    """Generate CSV export data"""
    
    csv_buffer = BytesIO()
    
    if analysis_mode == "⚖️ Side-by-Side Comparison":
        # Create combined CSV with both strategies
        combined_data = []
        for i in range(len(autoclass_df)):
            combined_data.append({
                "Month": autoclass_df.iloc[i]["Month"],
                "Autoclass_Standard_GB": autoclass_df.iloc[i]["Standard (GB)"],
                "Autoclass_Nearline_GB": autoclass_df.iloc[i]["Nearline (GB)"],
                "Autoclass_Coldline_GB": autoclass_df.iloc[i]["Coldline (GB)"],
                "Autoclass_Archive_GB": autoclass_df.iloc[i]["Archive (GB)"],
                "Autoclass_Total_Cost": autoclass_df.iloc[i]["Total Cost ($)"],
                "Autoclass_Storage_Cost": autoclass_df.iloc[i]["Storage Cost ($)"],
                "Autoclass_Management_Fee": autoclass_df.iloc[i]["Autoclass Fee ($)"],
                "Lifecycle_Standard_GB": lifecycle_df.iloc[i]["Standard (GB)"],
                "Lifecycle_Nearline_GB": lifecycle_df.iloc[i]["Nearline (GB)"],
                "Lifecycle_Coldline_GB": lifecycle_df.iloc[i]["Coldline (GB)"],
                "Lifecycle_Archive_GB": lifecycle_df.iloc[i]["Archive (GB)"],
                "Lifecycle_Total_Cost": lifecycle_df.iloc[i]["Total Cost ($)"],
                "Lifecycle_Storage_Cost": lifecycle_df.iloc[i]["Storage Cost ($)"],
                "Lifecycle_Retrieval_Cost": lifecycle_df.iloc[i]["Retrieval Cost ($)"],
                "Cost_Difference": autoclass_df.iloc[i]["Total Cost ($)"] - lifecycle_df.iloc[i]["Total Cost ($)"]
            })
        
        combined_df = pd.DataFrame(combined_data)
        combined_df.to_csv(csv_buffer, index=False)
        filename_suffix = "comparison"
    else:
        # Single strategy export
        df = autoclass_df if analysis_mode == "🤖 Autoclass Only" else lifecycle_df
        df.to_csv(csv_buffer, index=False)
        filename_suffix = "autoclass" if analysis_mode == "🤖 Autoclass Only" else "lifecycle"
    
    return csv_buffer, filename_suffix
