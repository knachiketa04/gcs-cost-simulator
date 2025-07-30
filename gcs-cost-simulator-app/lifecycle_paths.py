# lifecycle_paths.py - Lifecycle path definitions and logic
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class LifecyclePath:
    """Structured lifecycle path definition"""
    name: str
    category: str
    description: str
    path: str
    transitions: Dict[str, Optional[int]]
    default_days: List[int]
    classes: List[str]


class LifecyclePathManager:
    """Manager for lifecycle path operations"""
    
    PATHS = {
        # Category 1: Linear Paths
        "full_linear": LifecyclePath(
            name="Full Linear Path ⭐",
            category="Linear Paths",
            description="Traditional 4-tier progression through all storage classes",
            path="Standard → Nearline → Coldline → Archive",
            transitions={"nearline_days": 30, "coldline_days": 90, "archive_days": 365},
            default_days=[30, 90, 365],
            classes=["Standard", "Nearline", "Coldline", "Archive"]
        ),
        "std_nl_cld": LifecyclePath(
            name="Standard → Nearline → Coldline",
            category="Linear Paths",
            description="Stop at Coldline storage, no Archive transition",
            path="Standard → Nearline → Coldline",
            transitions={"nearline_days": 30, "coldline_days": 90, "archive_days": None},
            default_days=[30, 90],
            classes=["Standard", "Nearline", "Coldline"]
        ),
        "std_nl_arc": LifecyclePath(
            name="Standard → Nearline → Archive",
            category="Linear Paths",
            description="Skip Coldline, go directly from Nearline to Archive",
            path="Standard → Nearline → Archive",
            transitions={"nearline_days": 30, "coldline_days": None, "archive_days": 180},
            default_days=[30, 180],
            classes=["Standard", "Nearline", "Archive"]
        ),
        "std_nl": LifecyclePath(
            name="Standard → Nearline",
            category="Linear Paths",
            description="Stop at Nearline storage, no further transitions",
            path="Standard → Nearline",
            transitions={"nearline_days": 30, "coldline_days": None, "archive_days": None},
            default_days=[30],
            classes=["Standard", "Nearline"]
        ),
        
        # Category 2: Direct Skip Paths
        "std_cld_arc": LifecyclePath(
            name="Standard → Coldline → Archive",
            category="Direct Skip Paths",
            description="Skip Nearline entirely, go directly to Coldline then Archive",
            path="Standard → Coldline → Archive",
            transitions={"nearline_days": None, "coldline_days": 90, "archive_days": 365},
            default_days=[90, 365],
            classes=["Standard", "Coldline", "Archive"]
        ),
        "std_cld": LifecyclePath(
            name="Standard → Coldline",
            category="Direct Skip Paths",
            description="Skip Nearline, go directly to Coldline and stop",
            path="Standard → Coldline",
            transitions={"nearline_days": None, "coldline_days": 90, "archive_days": None},
            default_days=[90],
            classes=["Standard", "Coldline"]
        ),
        "std_arc": LifecyclePath(
            name="Standard → Archive ⚡",
            category="Direct Skip Paths",
            description="Most aggressive - go directly to Archive storage",
            path="Standard → Archive",
            transitions={"nearline_days": None, "coldline_days": None, "archive_days": 365},
            default_days=[365],
            classes=["Standard", "Archive"]
        ),
        
        # Category 3: Partial Paths
        "nl_cld_arc": LifecyclePath(
            name="Nearline → Coldline → Archive",
            category="Partial Paths",
            description="Data already in Nearline, continue progression",
            path="Nearline → Coldline → Archive",
            transitions={"nearline_days": None, "coldline_days": 90, "archive_days": 365},
            default_days=[90, 365],
            classes=["Nearline", "Coldline", "Archive"]
        ),
        "nl_arc": LifecyclePath(
            name="Nearline → Archive",
            category="Partial Paths",
            description="Data in Nearline, skip Coldline, go to Archive",
            path="Nearline → Archive",
            transitions={"nearline_days": None, "coldline_days": None, "archive_days": 180},
            default_days=[180],
            classes=["Nearline", "Archive"]
        ),
        "cld_arc": LifecyclePath(
            name="Coldline → Archive",
            category="Partial Paths",
            description="Data already in Coldline, final transition to Archive",
            path="Coldline → Archive",
            transitions={"nearline_days": None, "coldline_days": None, "archive_days": 365},
            default_days=[365],
            classes=["Coldline", "Archive"]
        )
    }
    
    @classmethod
    def get_path_by_name(cls, display_name: str) -> Optional[str]:
        """Get path ID from display name"""
        for path_id, path in cls.PATHS.items():
            if path.name == display_name:
                return path_id
        return None
    
    @classmethod
    def get_path_info(cls, path_id: str) -> Optional[LifecyclePath]:
        """Get path information by ID"""
        return cls.PATHS.get(path_id)
    
    @classmethod
    def convert_to_rules(cls, path_id: str, transition_days: List[int]) -> Dict:
        """Convert path configuration to lifecycle_rules format"""
        path = cls.PATHS[path_id]
        lifecycle_rules = {"nearline_days": None, "coldline_days": None, "archive_days": None}
        
        classes = path.classes
        for i, days in enumerate(transition_days):
            if i + 1 < len(classes):
                target_class = classes[i + 1].lower()
                if target_class == "nearline":
                    lifecycle_rules["nearline_days"] = days
                elif target_class == "coldline":
                    lifecycle_rules["coldline_days"] = days
                elif target_class == "archive":
                    lifecycle_rules["archive_days"] = days
        
        # Add metadata for simulation and reporting
        lifecycle_rules.update({
            "path_id": path_id,
            "path_name": path.name,
            "path_description": path.description,
            "path_classes": path.classes,
            "transition_days": transition_days
        })
        
        return lifecycle_rules
    
    @classmethod
    def get_grouped_options(cls) -> List[str]:
        """Get path options grouped by category"""
        categories = {"Linear Paths": [], "Direct Skip Paths": [], "Partial Paths": []}
        
        for path in cls.PATHS.values():
            if path.category in categories:
                categories[path.category].append(path.name)
        
        # Build options with category ordering
        path_options = []
        for category in ["Linear Paths", "Direct Skip Paths", "Partial Paths"]:
            if category in categories:
                path_options.extend(categories[category])
        
        return path_options
    
    @classmethod
    def create_timeline_display(cls, lifecycle_rules: Dict) -> str:
        """Create a timeline display for the selected lifecycle path"""
        if not lifecycle_rules:
            return "Standard lifecycle progression"
        
        path_classes = lifecycle_rules.get("path_classes", ["Standard", "Archive"])
        transition_days = lifecycle_rules.get("transition_days", [365])
        
        timeline = ""
        for i, days in enumerate(transition_days):
            from_class = path_classes[i]
            to_class = path_classes[i + 1]
            
            if i == 0:
                timeline += f"Day 0-{days}: {from_class} → "
            timeline += f"Day {days}+: {to_class}"
            if i < len(transition_days) - 1:
                timeline += " → "
        
        return timeline
    
    @classmethod
    def generate_path_recommendations(cls, lifecycle_rules: Dict, 
                                    storage_distribution: Dict[str, float], 
                                    total_data: float) -> List[str]:
        """Generate recommendations based on the selected lifecycle path"""
        recommendations = []
        path_id = lifecycle_rules.get("path_id", "")
        
        # Analyze distribution percentages
        archive_percentage = (storage_distribution.get("Archive", 0) / total_data * 100) if total_data > 0 else 0
        standard_percentage = (storage_distribution.get("Standard", 0) / total_data * 100) if total_data > 0 else 0
        
        # Path-specific recommendations
        if "std_arc" in path_id:  # Direct Standard → Archive
            if standard_percentage > 50:
                recommendations.append("⚡ Consider reducing transition time to Archive for better cost optimization")
            else:
                recommendations.append("✅ Direct Archive transition is working efficiently")
        
        elif "std_cld" in path_id:  # Standard → Coldline paths
            coldline_percentage = (storage_distribution.get("Coldline", 0) / total_data * 100) if total_data > 0 else 0
            if coldline_percentage > 60:
                recommendations.append("✅ Coldline strategy is effectively reducing storage costs")
            if standard_percentage > 30:
                recommendations.append("⚡ Consider faster transition to Coldline for additional savings")
        
        elif "full_linear" in path_id:  # Full linear path
            if archive_percentage < 30:
                recommendations.append("⚡ Consider more aggressive transition timing for better cost optimization")
            else:
                recommendations.append("✅ Balanced progression through all storage tiers")
        
        # General recommendations
        if standard_percentage > 40:
            recommendations.append("💡 High Standard storage usage - consider faster transitions for cost savings")
        
        if archive_percentage > 80:
            recommendations.append("🎯 Excellent archive utilization - optimal for long-term storage")
        
        # Default recommendation if none apply
        if not recommendations:
            recommendations.append("✅ Your current lifecycle path appears well-optimized for your data pattern")
        
        return recommendations
    
    @classmethod
    def get_default_rules(cls) -> Dict:
        """Get default lifecycle rules"""
        return {"nearline_days": 30, "coldline_days": 90, "archive_days": 365}
