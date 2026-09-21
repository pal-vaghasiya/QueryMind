"""Physical plan operator definitions representing concrete database execution operations."""

from typing import List, Optional, Dict, Any

class PhysicalOperator:
    """Base class for physical execution operators."""
    def __init__(self, op_name: str, children: Optional[List['PhysicalOperator']] = None):
        self.op_name = op_name
        self.children = children or []
        self.estimated_cardinality: float = 0.0
        self.estimated_cost: float = 0.0

    def get_depth(self) -> int:
        if not self.children:
            return 1
        return 1 + max(child.get_depth() for child in self.children)

    def count_operators(self) -> int:
        return 1 + sum(child.count_operators() for child in self.children)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "operator": self.op_name,
            "estimated_cardinality": self.estimated_cardinality,
            "estimated_cost": self.estimated_cost,
            "children": [child.to_dict() for child in self.children]
        }

    def __repr__(self) -> str:
        return f"{self.op_name}({self.children})"


class SeqScan(PhysicalOperator):
    """Sequential table scan physical operator."""
    def __init__(self, table_name: str, alias: Optional[str] = None):
        super().__init__("SeqScan")
        self.table_name = table_name
        self.alias = alias or table_name

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({"table_name": self.table_name, "alias": self.alias})
        return d

    def __repr__(self) -> str:
        return f"SeqScan({self.table_name} AS {self.alias})"


class IndexScan(PhysicalOperator):
    """Index scan physical operator."""
    def __init__(self, table_name: str, index_col: str, alias: Optional[str] = None):
        super().__init__("IndexScan")
        self.table_name = table_name
        self.index_col = index_col
        self.alias = alias or table_name

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({"table_name": self.table_name, "index_col": self.index_col, "alias": self.alias})
        return d

    def __repr__(self) -> str:
        return f"IndexScan({self.table_name}.{self.index_col} AS {self.alias})"


class NestedLoopJoin(PhysicalOperator):
    """Nested-loop join physical operator."""
    def __init__(self, left: PhysicalOperator, right: PhysicalOperator, left_key: str, right_key: str):
        super().__init__("NestedLoopJoin", [left, right])
        self.left_key = left_key
        self.right_key = right_key

    @property
    def left(self) -> PhysicalOperator:
        return self.children[0]

    @property
    def right(self) -> PhysicalOperator:
        return self.children[1]

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({"left_key": self.left_key, "right_key": self.right_key})
        return d

    def __repr__(self) -> str:
        return f"NestedLoopJoin({self.left} ⋈ {self.right})"


class HashJoin(PhysicalOperator):
    """Hash join physical operator."""
    def __init__(self, left: PhysicalOperator, right: PhysicalOperator, left_key: str, right_key: str):
        super().__init__("HashJoin", [left, right])
        self.left_key = left_key
        self.right_key = right_key

    @property
    def left(self) -> PhysicalOperator:
        return self.children[0]

    @property
    def right(self) -> PhysicalOperator:
        return self.children[1]

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({"left_key": self.left_key, "right_key": self.right_key})
        return d

    def __repr__(self) -> str:
        return f"HashJoin({self.left} ⋈ {self.right})"


class FilterOperator(PhysicalOperator):
    """Filter (Selection) physical operator."""
    def __init__(self, child: PhysicalOperator, predicate: str, column: str, operator: str, value: Any):
        super().__init__("Filter", [child])
        self.predicate = predicate
        self.column = column
        self.operator = operator
        self.value = value

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({"predicate": self.predicate, "column": self.column, "operator": self.operator, "value": self.value})
        return d

    def __repr__(self) -> str:
        return f"Filter[{self.predicate}]({self.children[0]})"


class ProjectionOperator(PhysicalOperator):
    """Projection physical operator."""
    def __init__(self, child: PhysicalOperator, columns: List[str]):
        super().__init__("Projection", [child])
        self.columns = columns

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({"columns": self.columns})
        return d

    def __repr__(self) -> str:
        return f"Projection[{', '.join(self.columns)}]({self.children[0]})"
