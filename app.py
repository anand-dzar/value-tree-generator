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


def render_tree_node(node: ValueTreeNode, level: int = 0, default_expanded: bool = True):
    """Recursively render a tree node with its children."""
    # Visual styling based on level
    level_icons = {
        "Lever": "🎯",
        "Business_Objective": "📊",
        "Value_Driver": "⚡",
        "KPI": "📈"
    }

    icon = level_icons.get(node.level, "📌")

    # For leaf nodes or nodes without children, just display
    if not node.children:
        st.markdown(
            f"{icon} **{node.name}**",
            unsafe_allow_html=True
        )
        if node.description:
            st.markdown(
                f"&nbsp;&nbsp;&nbsp;<small style='color: #666;'>{node.description}</small>",
                unsafe_allow_html=True
            )
    else:
        # Use expander for nodes with children
        with st.expander(f"{icon} {node.name}", expanded=default_expanded):
            if node.description:
                st.caption(node.description)
            st.markdown(f"<small style='color: #888;'>ID: {node.node_id} | Level: {node.level}</small>",
                       unsafe_allow_html=True)
            st.markdown("---")
            for child in node.children:
                render_tree_node(child, level + 1, default_expanded)


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


def render_visual_tree(tree: ValueTree):
    """Render the tree as a visual diagram similar to the reference image."""

    # Collect nodes by level
    levers = []
    business_objectives = []
    value_drivers = []
    kpis = []

    # Build parent-child mappings
    bo_to_lever = {}
    vd_to_bo = {}
    kpi_to_vd = {}

    def collect_nodes(tree_node, parent_id=None):
        node = tree_node.node
        if node.node_level == "Lever":
            levers.append(node)
        elif node.node_level == "Business_Objective":
            business_objectives.append(node)
            bo_to_lever[node.node_id] = parent_id
        elif node.node_level == "Value_Driver":
            value_drivers.append(node)
            vd_to_bo[node.node_id] = parent_id
        elif node.node_level == "KPI":
            kpis.append(node)
            kpi_to_vd[node.node_id] = parent_id

        for child in tree_node.children:
            collect_nodes(child, node.node_id)

    for root in tree.roots:
        collect_nodes(root)

    # Group KPIs by Value Driver
    kpis_by_vd = {}
    for kpi in kpis:
        vd_id = kpi_to_vd.get(kpi.node_id)
        if vd_id not in kpis_by_vd:
            kpis_by_vd[vd_id] = []
        kpis_by_vd[vd_id].append(kpi)

    # Group Value Drivers by Business Objective
    vds_by_bo = {}
    for vd in value_drivers:
        bo_id = vd_to_bo.get(vd.node_id)
        if bo_id not in vds_by_bo:
            vds_by_bo[bo_id] = []
        vds_by_bo[bo_id].append(vd)

    # Group Business Objectives by Lever
    bos_by_lever = {}
    for bo in business_objectives:
        lever_id = bo_to_lever.get(bo.node_id)
        if lever_id not in bos_by_lever:
            bos_by_lever[lever_id] = []
        bos_by_lever[lever_id].append(bo)

    # Generate HTML
    html = """
    <style>
        .value-tree-container {
            font-family: Arial, sans-serif;
            font-size: 12px;
            overflow-x: auto;
        }
        .tree-header {
            display: flex;
            border-bottom: 2px solid #7B2D8E;
            margin-bottom: 10px;
            padding-bottom: 5px;
        }
        .tree-header-col {
            font-weight: bold;
            color: #7B2D8E;
            text-transform: uppercase;
            font-size: 11px;
        }
        .col-lever { width: 140px; min-width: 140px; }
        .col-bo { width: 160px; min-width: 160px; }
        .col-vd { width: 180px; min-width: 180px; }
        .col-kpi { width: 300px; min-width: 300px; }

        .lever-section {
            display: flex;
            margin-bottom: 15px;
            position: relative;
        }
        .lever-box {
            background: linear-gradient(135deg, #9B4DCA 0%, #7B2D8E 100%);
            color: white;
            padding: 12px 8px;
            border-radius: 6px;
            font-weight: bold;
            text-align: center;
            width: 120px;
            min-width: 120px;
            margin-right: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 13px;
        }
        .bo-container {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .bo-row {
            display: flex;
            align-items: flex-start;
        }
        .bo-box {
            background: white;
            border: 2px solid #E0E0E0;
            padding: 8px 10px;
            border-radius: 4px;
            width: 140px;
            min-width: 140px;
            margin-right: 15px;
            font-size: 11px;
        }
        .vd-container {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }
        .vd-row {
            display: flex;
            align-items: flex-start;
        }
        .vd-box {
            background: white;
            border: 2px solid #E0E0E0;
            padding: 8px 10px;
            border-radius: 4px;
            width: 160px;
            min-width: 160px;
            margin-right: 15px;
            font-size: 11px;
        }
        .kpi-container {
            display: flex;
            flex-wrap: wrap;
            gap: 4px 15px;
            align-items: flex-start;
            max-width: 300px;
        }
        .kpi-item {
            color: #9B4DCA;
            font-size: 10px;
            white-space: nowrap;
        }
        .kpi-item::before {
            content: "• ";
            color: #9B4DCA;
        }
        .connector {
            border-left: 2px solid #CCC;
            margin-left: 60px;
            padding-left: 10px;
        }
    </style>
    <div class="value-tree-container">
        <div class="tree-header">
            <div class="tree-header-col col-lever">Levers</div>
            <div class="tree-header-col col-bo">Business Objectives</div>
            <div class="tree-header-col col-vd">Value Drivers</div>
            <div class="tree-header-col col-kpi">Operational KPI's</div>
        </div>
    """

    for lever in levers:
        lever_bos = bos_by_lever.get(lever.node_id, [])

        # Calculate total rows for this lever
        total_vd_rows = sum(len(vds_by_bo.get(bo.node_id, [])) or 1 for bo in lever_bos) if lever_bos else 1

        html += f'<div class="lever-section">'
        html += f'<div class="lever-box">{lever.node_name}</div>'

        html += '<div class="bo-container">'
        for bo in lever_bos:
            bo_vds = vds_by_bo.get(bo.node_id, [])

            html += '<div class="bo-row">'
            html += f'<div class="bo-box">{bo.node_name}</div>'

            html += '<div class="vd-container">'
            if bo_vds:
                for vd in bo_vds:
                    vd_kpis = kpis_by_vd.get(vd.node_id, [])

                    html += '<div class="vd-row">'
                    html += f'<div class="vd-box">{vd.node_name}</div>'

                    html += '<div class="kpi-container">'
                    for kpi in vd_kpis:
                        html += f'<span class="kpi-item">{kpi.node_name}</span>'
                    html += '</div>'
                    html += '</div>'
            html += '</div>'

            html += '</div>'
        html += '</div>'

        html += '</div>'

    html += '</div>'

    st.markdown(html, unsafe_allow_html=True)


def display_tree(tree: ValueTree, view_mode: str = "hierarchical_expanded"):
    """Display the complete value tree."""
    if not tree.roots:
        st.warning("No nodes match the selected criteria. Try adjusting the threshold or context.")
        return

    if view_mode == "visual":
        render_visual_tree(tree)
    elif view_mode == "hierarchical_expanded":
        for root in tree.roots:
            render_tree_node(root, level=0, default_expanded=True)
    elif view_mode == "hierarchical_collapsed":
        for root in tree.roots:
            render_tree_node(root, level=0, default_expanded=False)
    else:  # flat
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

    # Reload data button
    if st.sidebar.button("🔃 Reload Data", help="Reload Excel file to pick up changes"):
        load_data.clear()
        st.rerun()

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
        help="1 = Broad Value Tree (more nodes) | 5 = Narrow Value Tree (fewer nodes)"
    )
    st.sidebar.markdown(
        "<div style='display: flex; justify-content: space-between; font-size: 11px; color: #666; margin-top: -10px;'>"
        "<span>1: Broad</span><span>5: Narrow</span></div>",
        unsafe_allow_html=True
    )

    # View mode selection
    view_mode = st.sidebar.radio(
        "View Mode",
        options=["visual", "hierarchical_expanded", "hierarchical_collapsed", "flat"],
        index=2,  # Default to Hierarchical (Collapsed)
        format_func=lambda x: {
            "visual": "Visual Tree",
            "hierarchical_expanded": "Hierarchical (Expanded)",
            "hierarchical_collapsed": "Hierarchical (Collapsed)",
            "flat": "Flat (Indented)"
        }[x],
        help="Choose how to display the tree"
    )

    # Custom button styling
    st.markdown("""
        <style>
        div.stButton > button[kind="primary"] {
            background-color: #9B4DCA;
            border-color: #9B4DCA;
        }
        div.stButton > button[kind="primary"]:hover {
            background-color: #8A3DB8;
            border-color: #8A3DB8;
        }
        </style>
    """, unsafe_allow_html=True)

    # Generate button
    if st.sidebar.button("Generate", type="primary", use_container_width=True):
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

        if not st.session_state.get('generate_clicked'):
            st.info("Select your context options and click **Generate** to build the value tree.")
        elif st.session_state.get('generate_clicked'):
            # Display value intent description
            intent_description = data_loader.get_value_intent_description(selected_intent)
            if intent_description:
                st.info(f"**{selected_intent}:** {intent_description}")

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
