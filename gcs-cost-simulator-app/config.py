# config.py - Centralized configuration management

# Default Pricing Constants (Iowa us-central1 Regional)
DEFAULT_PRICING = {
    "standard": {"storage": 0.020, "min_storage_days": 0},
    "nearline": {"storage": 0.010, "min_storage_days": 30},
    "coldline": {"storage": 0.004, "min_storage_days": 90},
    "archive": {"storage": 0.0012, "min_storage_days": 365},
    "operations": {
        "class_a": 0.05 / 10000,  # Per operation
        "class_b": 0.004 / 10000  # Per operation
    },
    # Lifecycle transition costs (Class A operations per 1000 operations)
    "lifecycle_transitions": {
        "standard_to_nearline": 0.0200 / 1000,    # $0.0200 per 1000 operations
        "nearline_to_coldline": 0.0400 / 1000,    # $0.0400 per 1000 operations  
        "coldline_to_archive": 0.1000 / 1000      # $0.1000 per 1000 operations
    },
    "autoclass_fee_per_1000_objects_per_month": 0.0025,  # Per 1000 objects per month
    "retrieval_costs": {
        "nearline": 0.01,    # $ per GB retrieved
        "coldline": 0.02,    # $ per GB retrieved  
        "archive": 0.05      # $ per GB retrieved
    },
    "early_deletion_fees": {
        "nearline": 0.010,   # $ per GB if deleted before 30 days
        "coldline": 0.004,   # $ per GB if deleted before 90 days
        "archive": 0.0012    # $ per GB if deleted before 365 days
    }
}

# UI Configuration Schema - Data-driven UI generation
UI_CONFIG = {
    "pricing": {
        "title": "💰 Pricing Configuration",
        "sections": {
            "storage": {
                "title": "Storage Costs ($ per GB per month)",
                "fields": {
                    "standard_storage_price": {"label": "Standard Storage", "default": "standard.storage", "format": "%.4f", "step": 0.001},
                    "nearline_storage_price": {"label": "Nearline Storage", "default": "nearline.storage", "format": "%.4f", "step": 0.001},
                    "coldline_storage_price": {"label": "Coldline Storage", "default": "coldline.storage", "format": "%.4f", "step": 0.001},
                    "archive_storage_price": {"label": "Archive Storage", "default": "archive.storage", "format": "%.4f", "step": 0.001}
                }
            },
            "operations": {
                "title": "API Operations ($ per operation)",
                "fields": {
                    "class_a_price": {"label": "Class A Operations (Writes)", "default": "operations.class_a", "format": "%.7f", "step": 0.000001},
                    "class_b_price": {"label": "Class B Operations (Reads)", "default": "operations.class_b", "format": "%.7f", "step": 0.000001}
                }
            },
            "autoclass": {
                "title": "Autoclass Management Fee",
                "fields": {
                    "autoclass_fee_price": {"label": "Per 1000 Objects per Month ($)", "default": "autoclass_fee_per_1000_objects_per_month", "format": "%.4f", "step": 0.0001}
                }
            },
            "lifecycle_transitions": {
                "title": "Lifecycle Transition Costs ($ per 1000 operations)",
                "fields": {
                    "std_to_nearline_price": {"label": "Standard → Nearline", "default": "lifecycle_transitions.standard_to_nearline", "format": "%.6f", "step": 0.000001},
                    "nearline_to_coldline_price": {"label": "Nearline → Coldline", "default": "lifecycle_transitions.nearline_to_coldline", "format": "%.6f", "step": 0.000001},
                    "coldline_to_archive_price": {"label": "Coldline → Archive", "default": "lifecycle_transitions.coldline_to_archive", "format": "%.6f", "step": 0.000001}
                }
            },
            "lifecycle": {
                "title": "Lifecycle-Specific Costs",
                "fields": {
                    "nearline_retrieval_price": {"label": "Nearline Retrieval ($/GB)", "default": "retrieval_costs.nearline", "format": "%.4f", "step": 0.001},
                    "coldline_retrieval_price": {"label": "Coldline Retrieval ($/GB)", "default": "retrieval_costs.coldline", "format": "%.4f", "step": 0.001},
                    "archive_retrieval_price": {"label": "Archive Retrieval ($/GB)", "default": "retrieval_costs.archive", "format": "%.4f", "step": 0.001}
                }
            }
        }
    },
    "sidebar": {
        "analysis_period": {
            "months": {"type": "slider", "label": "Total Analysis Period (Months)", "min": 12, "max": 60, "default": 36}
        },
        "data_growth": {
            "initial_data_gb": {"type": "number_input", "label": "Initial Data Upload (GB)", "min": 0, "default": 1048576, "step": 1, "help": "Amount of data uploaded in Month 1"},
            "monthly_growth_rate": {"type": "number_input", "label": "Monthly Growth Rate (%)", "min": 0.0, "max": 50.0, "default": 10.0, "step": 0.1, "help": "Percentage increase in data each month (0% = no new data)", "convert": "percentage"}
        },
        "object_characteristics": {
            "percent_large_objects": {"type": "slider", "label": "% of Data >128 KiB (Autoclass Eligible)", "min": 0, "max": 100, "default": 90, "convert": "percentage"}
        },
        "api_operations": {
            "reads": {"type": "number_input", "label": "Additional Class B (Reads) - Other Operations", "min": 0, "default": 0, "step": 1, "help": "Additional read operations beyond automatic upload operations (e.g., data access, list operations)"},
            "writes": {"type": "number_input", "label": "Additional Class A (Writes) - Other Operations", "min": 0, "default": 0, "step": 1, "help": "Additional write operations beyond automatic upload operations (e.g., metadata updates, deletes)"}
        }
    }
}

# PDF Report Templates
PDF_TEMPLATES = {
    "comparison": {
        "title": "GCS Storage Strategy Comparison Report",
        "subtitle": "Autoclass vs Lifecycle Policy Analysis",
        "sections": ["executive_summary", "cost_breakdown", "monthly_comparison", "insights"]
    },
    "autoclass": {
        "title": "GCS Autoclass Cost Analysis Report", 
        "subtitle": "Intelligent Storage Optimization Analysis",
        "sections": ["executive_summary", "cost_breakdown", "monthly_breakdown", "insights"]
    },
    "lifecycle": {
        "title": "GCS Lifecycle Policy Cost Analysis Report",
        "subtitle": "Time-Based Storage Transition Analysis", 
        "sections": ["executive_summary", "cost_breakdown", "monthly_breakdown", "insights"]
    }
}
