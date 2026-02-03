"""Configuration settings for Value Tree Generator."""

from pathlib import Path

# Excel file configuration
EXCEL_FILE_PATH = Path(__file__).parent.parent / "service_transformation_node_master.xlsx"
NODE_MASTER_SHEET = "Node_Master"
CONTEXT_APPLICABILITY_SHEET = "Context_Applicability"

# Default applicability threshold (1-5 scale)
DEFAULT_THRESHOLD = 3

# Node levels in hierarchical order
NODE_LEVELS = ["Lever", "Business_Objective", "Value_Driver", "KPI"]

# Node status values
ACTIVE_STATUS = "Active"
DEPRECATED_STATUS = "Deprecated"
