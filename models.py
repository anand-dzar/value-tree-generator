"""Data models for Value Tree Generator."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Node:
    """Represents a node in the value tree hierarchy."""
    node_id: str
    node_name: str
    node_level: str
    parent_node_id: Optional[str]
    description: str
    is_leaf: bool
    status: str

    def __hash__(self):
        return hash(self.node_id)

    def __eq__(self, other):
        if isinstance(other, Node):
            return self.node_id == other.node_id
        return False


@dataclass
class ApplicabilityRule:
    """Represents an applicability rule from Context_Applicability sheet."""
    applicability_id: str
    node_id: str
    value_intent: str
    industry: str
    function: str
    applicability_weight: int
    mandatory_flag: bool
    notes: str


@dataclass
class ValueTreeNode:
    """Represents a node in the assembled value tree with children."""
    node: Node
    children: list['ValueTreeNode'] = field(default_factory=list)

    @property
    def node_id(self) -> str:
        return self.node.node_id

    @property
    def name(self) -> str:
        return self.node.node_name

    @property
    def level(self) -> str:
        return self.node.node_level

    @property
    def description(self) -> str:
        return self.node.description


@dataclass
class ValueTree:
    """Represents the complete assembled value tree."""
    roots: list[ValueTreeNode] = field(default_factory=list)
    context: dict = field(default_factory=dict)
    node_count: int = 0

    def get_all_nodes(self) -> list[Node]:
        """Return all nodes in the tree as a flat list."""
        nodes = []

        def collect(tree_node: ValueTreeNode):
            nodes.append(tree_node.node)
            for child in tree_node.children:
                collect(child)

        for root in self.roots:
            collect(root)
        return nodes
