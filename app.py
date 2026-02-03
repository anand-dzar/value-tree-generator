"""Streamlit main application for Value Tree Generator."""

import streamlit as st
from pathlib import Path

from config import DEFAULT_THRESHOLD, EXCEL_FILE_PATH
from data_loader import DataLoader
from assembler import ValueTreeAssembler
from models import ValueTreeNode, ValueTree


# Page configuration
st.set_page_config(
    page_title="Value Tree Generator",
    page_icon="🌳",
    layout="wide"
)


@st.cache_resource
def load_data() -> DataLoader:
    """Load and cache the data from Excel file."""
    loader = DataLoader()
    loader.load()
    return loader


def render_tree_node(node: ValueTreeNode, level: int = 0):
    """Recursively render a tree node with its children."""
    # Visual styling based on level
    level_icons = {
        "Lever": "🎯",
        "Business_Objective": "📊",
        "Value_Driver": "⚡",
        "KPI": "📈"
    }

    level_colors = {
        "Lever": "#1f77b4",
        "Business_Objective": "#ff7f0e",
        "Value_Driver": "#2ca02c",
        "KPI": "#9467bd"
    }

    icon = level_icons.get(node.level, "📌")
    color = level_colors.get(node.level, "#333")

    # Create indentation
    indent = "&nbsp;" * (level * 6)

    # For leaf nodes or nodes without children, just display
    if not node.children:
        st.markdown(
            f"{indent}{icon} **{node.name}**",
            unsafe_allow_html=True
        )
        if node.description:
            st.markdown(
                f"{indent}&nbsp;&nbsp;&nbsp;<small style='color: #666;'>{node.description}</small>",
                unsafe_allow_html=True
            )
    else:
        # Use expander for nodes with children
        with st.expander(f"{icon} {node.name}", expanded=(level < 2)):
            if node.description:
                st.caption(node.description)
            st.markdown(f"<small style='color: #888;'>ID: {node.node_id} | Level: {node.level}</small>",
                       unsafe_allow_html=True)
            st.markdown("---")
            for child in node.children:
                render_tree_node(child, level + 1)


def render_tree_flat(node: ValueTreeNode, level: int = 0):
    """Render tree in a flat, indented format."""
    level_icons = {
        "Lever": "🎯",
        "Business_Objective": "📊",
        "Value_Driver": "⚡",
        "KPI": "📈"
    }

    icon = level_icons.get(node.level, "📌")
    indent = "│   " * level

    # Display the node
    if level == 0:
        st.markdown(f"**{icon} {node.name}**")
    else:
        prefix = "├── " if level > 0 else ""
        st.markdown(f"`{indent}{prefix}`{icon} **{node.name}**")

    if node.description:
        desc_indent = "│   " * (level + 1)
        st.markdown(f"<small style='color: #666; margin-left: 20px;'>`{desc_indent}`{node.description}</small>",
                   unsafe_allow_html=True)

    # Render children
    for child in node.children:
        render_tree_flat(child, level + 1)


def display_tree(tree: ValueTree, view_mode: str = "hierarchical"):
    """Display the complete value tree."""
    if not tree.roots:
        st.warning("No nodes match the selected criteria. Try adjusting the threshold or context.")
        return

    if view_mode == "hierarchical":
        for root in tree.roots:
            render_tree_node(root, level=0)
    else:
        for root in tree.roots:
            render_tree_flat(root, level=0)
            st.markdown("---")


def main():
    """Main application entry point."""
    st.title("🌳 Value Tree Generator")
    st.markdown("""
    Generate a hierarchical value tree based on your business context.
    The tree shows the 4-level hierarchy: **Lever → Business Objective → Value Driver → KPI**
    """)

    # Load data
    data_loader = load_data()

    # Check for validation errors
    if data_loader.validation_errors:
        st.error("Data Validation Errors:")
        for error in data_loader.validation_errors:
            st.error(f"• {error}")
        st.stop()

    if not data_loader.is_loaded:
        st.error(f"Failed to load data from: {EXCEL_FILE_PATH}")
        st.stop()

    # Create assembler
    assembler = ValueTreeAssembler(data_loader)

    # Sidebar for inputs
    st.sidebar.header("Context Selection")

    # Get dropdown options
    value_intents = data_loader.get_unique_value_intents()
    industries = data_loader.get_unique_industries()
    functions = data_loader.get_unique_functions()

    # Dropdowns
    selected_intent = st.sidebar.selectbox(
        "Value Intent",
        options=value_intents,
        help="Select the strategic value intent"
    )

    selected_industry = st.sidebar.selectbox(
        "Industry",
        options=industries,
        help="Select the target industry"
    )

    selected_function = st.sidebar.selectbox(
        "Function",
        options=functions,
        help="Select the business function"
    )

    # Threshold slider
    threshold = st.sidebar.slider(
        "Applicability Threshold",
        min_value=1,
        max_value=5,
        value=DEFAULT_THRESHOLD,
        help="Minimum applicability weight for nodes to be included (1-5)"
    )

    # View mode selection
    view_mode = st.sidebar.radio(
        "View Mode",
        options=["hierarchical", "flat"],
        format_func=lambda x: "Hierarchical (Expandable)" if x == "hierarchical" else "Flat (Indented)",
        help="Choose how to display the tree"
    )

    # Generate button
    if st.sidebar.button("🔄 Generate Value Tree", type="primary", use_container_width=True):
        st.session_state['generate_clicked'] = True

    # Display info about selection
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Current Selection")
    st.sidebar.markdown(f"**Intent:** {selected_intent}")
    st.sidebar.markdown(f"**Industry:** {selected_industry}")
    st.sidebar.markdown(f"**Function:** {selected_function}")
    st.sidebar.markdown(f"**Threshold:** ≥ {threshold}")

    # Main content area
    col1, col2 = st.columns([3, 1])

    with col1:
        st.header("Value Tree")

        # Auto-generate on first load or when button clicked
        if 'generate_clicked' not in st.session_state:
            st.session_state['generate_clicked'] = True

        if st.session_state.get('generate_clicked'):
            with st.spinner("Assembling value tree..."):
                tree = assembler.assemble_value_tree(
                    value_intent=selected_intent,
                    industry=selected_industry,
                    function=selected_function,
                    threshold=threshold
                )

            # Display the tree
            display_tree(tree, view_mode)

    with col2:
        st.header("Statistics")

        if st.session_state.get('generate_clicked'):
            tree = assembler.assemble_value_tree(
                value_intent=selected_intent,
                industry=selected_industry,
                function=selected_function,
                threshold=threshold
            )
            stats = assembler.get_statistics(tree)

            st.metric("Total Nodes", stats["total_nodes"])

            st.markdown("**By Level:**")
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("🎯 Levers", stats["levers"])
                st.metric("⚡ Value Drivers", stats["value_drivers"])
            with col_b:
                st.metric("📊 Business Objectives", stats["business_objectives"])
                st.metric("📈 KPIs", stats["kpis"])

    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        "<small>Value Tree Generator v1.0<br>"
        "Powered by Streamlit</small>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
