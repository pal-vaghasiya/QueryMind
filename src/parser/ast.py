"""AST representation of Relational Algebra expressions for SQL queries."""

from typing import List, Optional, Any, Dict

class Node:
    """Base node for Relational Algebra AST."""
    def __init__(self, node_type: str, children: Optional[List['Node']] = None):
        self.node_type = node_type
        self.children = children or []

    def get_depth(self) -> int:
        if not self.children:
            return 1
        return 1 + max(child.get_depth() for child in self.children)

    def count_nodes(self) -> int:
        return 1 + sum(child.count_nodes() for child in self.children)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.node_type,
            "children": [child.to_dict() for child in self.children]
        }

    def __repr__(self) -> str:
        return f"{self.node_type}({self.children})"


class TableScan(Node):
    """Table Scan node representing a base table scan."""
    def __init__(self, table_name: str, alias: Optional[str] = None):
        super().__init__("TableScan")
        self.table_name = table_name
        self.alias = alias or table_name

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({"table_name": self.table_name, "alias": self.alias})
        return d

    def __repr__(self) -> str:
        return f"TableScan({self.table_name} AS {self.alias})"


class Selection(Node):
    """Selection node representing σ (WHERE filter conditions)."""
    def __init__(self, child: Node, predicate: str, column: str, operator: str, value: Any):
        super().__init__("Selection", [child])
        self.predicate = predicate
        self.column = column
        self.operator = operator
        self.value = value

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({
            "predicate": self.predicate,
            "column": self.column,
            "operator": self.operator,
            "value": self.value
        })
        return d

    def __repr__(self) -> str:
        return f"σ[{self.predicate}]({self.children[0]})"


class Projection(Node):
    """Projection node representing π (SELECT column list)."""
    def __init__(self, child: Node, columns: List[str]):
        super().__init__("Projection", [child])
        self.columns = columns

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({"columns": self.columns})
        return d

    def __repr__(self) -> str:
        return f"π[{', '.join(self.columns)}]({self.children[0]})"


class Join(Node):
    """Join node representing ⋈ (INNER JOIN)."""
    def __init__(self, left: Node, right: Node, left_key: str, right_key: str, join_type: str = "INNER"):
        super().__init__("Join", [left, right])
        self.left_key = left_key
        self.right_key = right_key
        self.join_type = join_type

    @property
    def left(self) -> Node:
        return self.children[0]

    @property
    def right(self) -> Node:
        return self.children[1]

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({
            "left_key": self.left_key,
            "right_key": self.right_key,
            "join_type": self.join_type
        })
        return d

    def __repr__(self) -> str:
        return f"({self.left} ⋈[{self.left_key}={self.right_key}] {self.right})"
