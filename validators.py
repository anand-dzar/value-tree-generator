"""Validation functions for Value Tree Generator."""

from typing import Optional
import pandas as pd

from config import NODE_MASTER_SHEET, CONTEXT_APPLICABILITY_SHEET, ACTIVE_STATUS

# Required columns for each sheet
NODE_MASTER_REQUIRED_COLUMNS = [
    "Node_ID", "Node_Name", "Node_Level", "Parent_Node_ID",
    "Description", "Is_Leaf", "Status"
]

CONTEXT_APPLICABILITY_REQUIRED_COLUMNS = [
    "Applicability_ID", "Node_ID", "Value_Intent", "Industry",
    "Function", "Applicability_Weight"
]


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


def validate_sheets_exist(excel_file: pd.ExcelFile) -> list[str]:
    """Verify both required sheets exist in the Excel file."""
    errors = []
    sheet_names = excel_file.sheet_names

    if NODE_MASTER_SHEET not in sheet_names:
        errors.append(f"Missing required sheet: '{NODE_MASTER_SHEET}'")

    if CONTEXT_APPLICABILITY_SHEET not in sheet_names:
        errors.append(f"Missing required sheet: '{CONTEXT_APPLICABILITY_SHEET}'")

    return errors


def validate_required_columns(df: pd.DataFrame, required_columns: list[str],
                              sheet_name: str) -> list[str]:
    """Verify all required columns are present in the DataFrame."""
    errors = []
    missing_columns = set(required_columns) - set(df.columns)

    if missing_columns:
        errors.append(
            f"Sheet '{sheet_name}' is missing required columns: {sorted(missing_columns)}"
        )

    return errors


def validate_node_master(df: pd.DataFrame) -> list[str]:
    """Validate Node_Master sheet data integrity."""
    errors = []

    # Check Node_ID uniqueness
    duplicates = df[df.duplicated(subset=['Node_ID'], keep=False)]
    if not duplicates.empty:
        dup_ids = duplicates['Node_ID'].unique().tolist()
        errors.append(f"Duplicate Node_IDs found: {dup_ids}")

    # Build lookup for validation
    node_ids = set(df['Node_ID'].dropna().tolist())

    # Validate Parent_Node_ID references (non-Lever nodes must have valid parent)
    for idx, row in df.iterrows():
        node_id = row['Node_ID']
        parent_id = row['Parent_Node_ID']
        node_level = row['Node_Level']

        # Levers should have no parent
        if node_level == "Lever":
            if pd.notna(parent_id):
                errors.append(
                    f"Lever node '{node_id}' should not have a Parent_Node_ID"
                )
        else:
            # Non-Lever nodes must have a valid parent
            if pd.isna(parent_id):
                errors.append(
                    f"Non-Lever node '{node_id}' is missing Parent_Node_ID"
                )
            elif parent_id not in node_ids:
                errors.append(
                    f"Node '{node_id}' references non-existent parent '{parent_id}'"
                )

    # Check for circular dependencies
    circular_errors = check_circular_dependencies(df)
    errors.extend(circular_errors)

    return errors


def check_circular_dependencies(df: pd.DataFrame) -> list[str]:
    """Check for circular dependencies in the node hierarchy."""
    errors = []

    # Build parent lookup
    parent_lookup = {}
    for _, row in df.iterrows():
        node_id = row['Node_ID']
        parent_id = row['Parent_Node_ID']
        if pd.notna(parent_id):
            parent_lookup[node_id] = parent_id

    # Check each node for circular path
    for node_id in parent_lookup.keys():
        visited = set()
        current = node_id

        while current in parent_lookup:
            if current in visited:
                errors.append(f"Circular dependency detected involving node '{node_id}'")
                break
            visited.add(current)
            current = parent_lookup[current]

    return errors


def validate_context_applicability(df: pd.DataFrame,
                                   valid_node_ids: set[str]) -> list[str]:
    """Validate Context_Applicability sheet data integrity."""
    errors = []

    # Check all Node_IDs exist in Node_Master
    for idx, row in df.iterrows():
        node_id = row['Node_ID']
        if pd.notna(node_id) and node_id not in valid_node_ids:
            errors.append(
                f"Context_Applicability row {idx + 2} references "
                f"non-existent Node_ID '{node_id}'"
            )

    # Validate Applicability_Weight is numeric and in valid range
    for idx, row in df.iterrows():
        weight = row['Applicability_Weight']
        if pd.notna(weight):
            try:
                weight_val = int(weight)
                if weight_val < 1 or weight_val > 5:
                    errors.append(
                        f"Context_Applicability row {idx + 2}: "
                        f"Applicability_Weight must be between 1 and 5, got {weight_val}"
                    )
            except (ValueError, TypeError):
                errors.append(
                    f"Context_Applicability row {idx + 2}: "
                    f"Invalid Applicability_Weight value '{weight}'"
                )

    return errors


def validate_all(excel_file: pd.ExcelFile,
                 node_master_df: pd.DataFrame,
                 context_df: pd.DataFrame) -> list[str]:
    """Run all validations and return list of errors."""
    all_errors = []

    # Check sheets exist
    all_errors.extend(validate_sheets_exist(excel_file))
    if all_errors:
        return all_errors  # Can't proceed if sheets missing

    # Check required columns
    all_errors.extend(
        validate_required_columns(node_master_df, NODE_MASTER_REQUIRED_COLUMNS,
                                  NODE_MASTER_SHEET)
    )
    all_errors.extend(
        validate_required_columns(context_df, CONTEXT_APPLICABILITY_REQUIRED_COLUMNS,
                                  CONTEXT_APPLICABILITY_SHEET)
    )
    if all_errors:
        return all_errors  # Can't proceed if columns missing

    # Validate Node_Master
    all_errors.extend(validate_node_master(node_master_df))

    # Validate Context_Applicability
    valid_node_ids = set(node_master_df['Node_ID'].dropna().tolist())
    all_errors.extend(validate_context_applicability(context_df, valid_node_ids))

    return all_errors
