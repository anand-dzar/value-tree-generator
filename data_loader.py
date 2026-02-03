"""Data loading functions for Value Tree Generator."""

from pathlib import Path
from typing import Optional
import pandas as pd

from config import (
    EXCEL_FILE_PATH, NODE_MASTER_SHEET, CONTEXT_APPLICABILITY_SHEET,
    VALUE_INTENT_SUMMARY_SHEET, ACTIVE_STATUS
)
from models import Node, ApplicabilityRule
from validators import validate_all, ValidationError


class DataLoader:
    """Loads and manages data from the Excel spreadsheet."""

    def __init__(self, excel_path: Optional[Path] = None):
        self.excel_path = excel_path or EXCEL_FILE_PATH
        self._node_master_df: Optional[pd.DataFrame] = None
        self._context_df: Optional[pd.DataFrame] = None
        self._value_intent_summary_df: Optional[pd.DataFrame] = None
        self._validation_errors: list[str] = []
        self._loaded = False

    def load(self) -> bool:
        """Load data from Excel file. Returns True if successful."""
        try:
            excel_file = pd.ExcelFile(self.excel_path)

            # Load sheets
            self._node_master_df = pd.read_excel(excel_file, NODE_MASTER_SHEET)
            self._context_df = pd.read_excel(excel_file, CONTEXT_APPLICABILITY_SHEET)

            # Load optional Value Intent Summary sheet
            if VALUE_INTENT_SUMMARY_SHEET in excel_file.sheet_names:
                self._value_intent_summary_df = pd.read_excel(
                    excel_file, VALUE_INTENT_SUMMARY_SHEET
                )

            # Validate data
            self._validation_errors = validate_all(
                excel_file, self._node_master_df, self._context_df
            )

            if self._validation_errors:
                return False

            self._loaded = True
            return True

        except FileNotFoundError:
            self._validation_errors = [f"Excel file not found: {self.excel_path}"]
            return False
        except Exception as e:
            self._validation_errors = [f"Error loading Excel file: {str(e)}"]
            return False

    @property
    def validation_errors(self) -> list[str]:
        """Return list of validation errors."""
        return self._validation_errors

    @property
    def is_loaded(self) -> bool:
        """Check if data has been successfully loaded."""
        return self._loaded

    @property
    def node_master_df(self) -> pd.DataFrame:
        """Return Node_Master DataFrame."""
        if not self._loaded:
            raise ValidationError("Data not loaded. Call load() first.")
        return self._node_master_df

    @property
    def context_df(self) -> pd.DataFrame:
        """Return Context_Applicability DataFrame."""
        if not self._loaded:
            raise ValidationError("Data not loaded. Call load() first.")
        return self._context_df

    def get_unique_value_intents(self) -> list[str]:
        """Extract unique Value_Intent values for dropdown."""
        if not self._loaded:
            return []
        values = self._context_df['Value_Intent'].dropna().unique().tolist()
        return sorted(values)

    def get_value_intent_description(self, value_intent: str) -> Optional[str]:
        """Get the description for a specific value intent."""
        if not self._loaded or self._value_intent_summary_df is None:
            return None
        row = self._value_intent_summary_df[
            self._value_intent_summary_df['Value_Intent'] == value_intent
        ]
        if row.empty:
            return None
        description = row.iloc[0]['Description']
        return description if pd.notna(description) else None

    def get_unique_industries(self) -> list[str]:
        """Extract unique Industry values for dropdown."""
        if not self._loaded:
            return []
        values = self._context_df['Industry'].dropna().unique().tolist()
        return sorted(values)

    def get_unique_functions(self) -> list[str]:
        """Extract unique Function values for dropdown."""
        if not self._loaded:
            return []
        values = self._context_df['Function'].dropna().unique().tolist()
        return sorted(values)

    def get_node_by_id(self, node_id: str) -> Optional[Node]:
        """Get a Node object by its ID."""
        if not self._loaded:
            return None

        row = self._node_master_df[self._node_master_df['Node_ID'] == node_id]
        if row.empty:
            return None

        row = row.iloc[0]
        return Node(
            node_id=row['Node_ID'],
            node_name=row['Node_Name'],
            node_level=row['Node_Level'],
            parent_node_id=row['Parent_Node_ID'] if pd.notna(row['Parent_Node_ID']) else None,
            description=row['Description'] if pd.notna(row['Description']) else "",
            is_leaf=bool(row['Is_Leaf']) if pd.notna(row['Is_Leaf']) else False,
            status=row['Status'] if pd.notna(row['Status']) else ACTIVE_STATUS
        )

    def get_all_nodes(self) -> list[Node]:
        """Get all nodes from Node_Master."""
        if not self._loaded:
            return []

        nodes = []
        for _, row in self._node_master_df.iterrows():
            nodes.append(Node(
                node_id=row['Node_ID'],
                node_name=row['Node_Name'],
                node_level=row['Node_Level'],
                parent_node_id=row['Parent_Node_ID'] if pd.notna(row['Parent_Node_ID']) else None,
                description=row['Description'] if pd.notna(row['Description']) else "",
                is_leaf=bool(row['Is_Leaf']) if pd.notna(row['Is_Leaf']) else False,
                status=row['Status'] if pd.notna(row['Status']) else ACTIVE_STATUS
            ))
        return nodes

    def get_applicability_rules(self, value_intent: str, industry: str,
                                function: str) -> list[ApplicabilityRule]:
        """Get applicability rules matching the given context."""
        if not self._loaded:
            return []

        # Filter by context
        filtered = self._context_df[
            (self._context_df['Value_Intent'] == value_intent) &
            (self._context_df['Industry'] == industry) &
            (self._context_df['Function'] == function)
        ]

        rules = []
        for _, row in filtered.iterrows():
            rules.append(ApplicabilityRule(
                applicability_id=row['Applicability_ID'],
                node_id=row['Node_ID'],
                value_intent=row['Value_Intent'],
                industry=row['Industry'],
                function=row['Function'],
                applicability_weight=int(row['Applicability_Weight']) if pd.notna(row['Applicability_Weight']) else 0,
                mandatory_flag=bool(row['Mandatory_Flag']) if pd.notna(row.get('Mandatory_Flag')) else False,
                notes=row['Notes'] if pd.notna(row.get('Notes')) else ""
            ))
        return rules
