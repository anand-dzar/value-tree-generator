"""Core assembly engine for Value Tree Generator."""

from typing import Optional
from collections import defaultdict

from config import ACTIVE_STATUS, NODE_LEVELS
from models import Node, ValueTree, ValueTreeNode
from data_loader import DataLoader


class ValueTreeAssembler:
    """Assembles value trees based on context and applicability rules."""

    def __init__(self, data_loader: DataLoader):
        self.data_loader = data_loader
        # Build node lookup for efficient access
        self._node_lookup: dict[str, Node] = {}
        self._build_node_lookup()

    def _build_node_lookup(self):
        """Build a lookup dictionary for nodes by ID."""
        if self.data_loader.is_loaded:
            for node in self.data_loader.get_all_nodes():
                self._node_lookup[node.node_id] = node

    def assemble_value_tree(self, value_intent: str, industry: str,
                            function: str, threshold: int = 3) -> ValueTree:
        """
        Assemble a value tree based on context and applicability threshold.

        Implements the 8-step algorithm:
        1. Filter Context_Applicability by context
        2. Apply threshold filter (weight >= threshold)
        3. Resolve node definitions from Node_Master
        4. Exclude deprecated nodes
        5. Auto-include parent nodes (iterate up to Lever)
        6. Deduplicate by Node_ID
        7. Construct hierarchical structure
        8. Sort lexicographically by Node_ID
        """
        # Step 1: Filter Context_Applicability by context
        rules = self.data_loader.get_applicability_rules(
            value_intent, industry, function
        )

        # Step 2: Apply threshold filter (weight >= threshold)
        eligible_rules = [r for r in rules if r.applicability_weight >= threshold]

        # Step 3 & 4: Resolve node definitions and exclude deprecated
        eligible_node_ids = set()
        for rule in eligible_rules:
            node = self._node_lookup.get(rule.node_id)
            if node and node.status == ACTIVE_STATUS:
                eligible_node_ids.add(rule.node_id)

        # Step 5: Auto-include parent nodes (iterate up to Lever)
        all_node_ids = set()
        for node_id in eligible_node_ids:
            # Add the node itself
            all_node_ids.add(node_id)
            # Walk up the parent chain
            current_id = node_id
            while current_id:
                node = self._node_lookup.get(current_id)
                if not node:
                    break
                # Only include active nodes
                if node.status == ACTIVE_STATUS:
                    all_node_ids.add(current_id)
                # Move to parent
                current_id = node.parent_node_id

        # Step 6: Deduplicate by Node_ID (already using set)
        # Step 7: Construct hierarchical structure
        tree = self._build_hierarchy(all_node_ids)

        # Step 8: Sort lexicographically by Node_ID (done in _build_hierarchy)
        tree.context = {
            "value_intent": value_intent,
            "industry": industry,
            "function": function,
            "threshold": threshold
        }
        tree.node_count = len(all_node_ids)

        return tree

    def _build_hierarchy(self, node_ids: set[str]) -> ValueTree:
        """Build hierarchical tree structure from flat set of node IDs."""
        # Get all nodes that are included
        included_nodes = {
            node_id: self._node_lookup[node_id]
            for node_id in node_ids
            if node_id in self._node_lookup
        }

        # Group nodes by their parent
        children_by_parent: dict[Optional[str], list[Node]] = defaultdict(list)
        for node in included_nodes.values():
            children_by_parent[node.parent_node_id].append(node)

        # Sort children at each level by Node_ID (lexicographic)
        for parent_id in children_by_parent:
            children_by_parent[parent_id].sort(key=lambda n: n.node_id)

        # Build tree recursively
        def build_subtree(node: Node) -> ValueTreeNode:
            tree_node = ValueTreeNode(node=node)
            children = children_by_parent.get(node.node_id, [])
            for child in children:
                tree_node.children.append(build_subtree(child))
            return tree_node

        # Find root nodes (Levers - nodes with no parent in our set)
        roots = []
        for node in included_nodes.values():
            if node.parent_node_id is None or node.parent_node_id not in included_nodes:
                # This is a root for our tree
                if node.node_level == "Lever":
                    roots.append(build_subtree(node))

        # Sort roots by Node_ID
        roots.sort(key=lambda tn: tn.node_id)

        return ValueTree(roots=roots)

    def get_statistics(self, tree: ValueTree) -> dict:
        """Get statistics about the assembled tree."""
        stats = {
            "total_nodes": tree.node_count,
            "levers": 0,
            "business_objectives": 0,
            "value_drivers": 0,
            "kpis": 0
        }

        def count_levels(tree_node: ValueTreeNode):
            level = tree_node.node.node_level
            if level == "Lever":
                stats["levers"] += 1
            elif level == "Business_Objective":
                stats["business_objectives"] += 1
            elif level == "Value_Driver":
                stats["value_drivers"] += 1
            elif level == "KPI":
                stats["kpis"] += 1

            for child in tree_node.children:
                count_levels(child)

        for root in tree.roots:
            count_levels(root)

        return stats
