# Value Tree Generator

A deterministic, spreadsheet-driven value tree assembly tool that generates a 4-level hierarchy based on user context inputs.

## Hierarchy Levels
- **Lever** (Root) → **Business Objective** → **Value Driver** → **KPI** (Leaf)

## Setup

### Prerequisites
- Python 3.10+
- The Excel data file: `service_transformation_node_master.xlsx` (should be in the parent directory)

### Installation

1. Navigate to the project directory:
   ```bash
   cd value-tree-generator
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   streamlit run app.py
   ```

## Usage

1. **Select Context**: Use the sidebar dropdowns to select:
   - Value Intent
   - Industry
   - Function

2. **Adjust Threshold**: Use the slider to set the minimum applicability weight (1-5)

3. **Generate**: Click "Generate Value Tree" to assemble the tree

4. **View Modes**:
   - **Hierarchical**: Expandable tree with expanders
   - **Flat**: Indented text-based view

## Project Structure

```
value-tree-generator/
├── app.py           # Streamlit main application
├── config.py        # Configuration (threshold, file paths)
├── data_loader.py   # Excel loading and validation
├── assembler.py     # Core assembly logic
├── models.py        # Data classes for Node, ValueTree
├── validators.py    # Spreadsheet and output validation
├── requirements.txt # Dependencies
└── README.md        # This file
```

## Data Files

The application reads from an Excel file with two sheets:
- **Node_Master**: Contains the node hierarchy definitions
- **Context_Applicability**: Contains applicability rules based on context

## Assembly Algorithm

1. Filter Context_Applicability by context (Value Intent, Industry, Function)
2. Apply threshold filter (weight >= threshold)
3. Resolve node definitions from Node_Master
4. Exclude deprecated nodes
5. Auto-include parent nodes (iterate up to Lever)
6. Deduplicate by Node_ID
7. Construct hierarchical structure
8. Sort lexicographically by Node_ID
