"""Logical Query Plan builder and optimizer rules (Selection & Projection Pushdown)."""

from typing import List, Optional
from ..parser.ast import Node, TableScan, Selection, Projection, Join

class LogicalPlan:
    """Represents a logical query plan tree."""
    def __init__(self, root: Node):
        self.root = root

    def get_tables(self) -> List[str]:
        """Extract all table names/aliases referenced in the plan."""
        tables = []
        def _extract(node: Node):
            if isinstance(node, TableScan):
                tables.append(node.alias)
            for child in node.children:
                _extract(child)
        _extract(self.root)
        return list(set(tables))

    def __repr__(self) -> str:
        return f"LogicalPlan({self.root})"


class LogicalPlanner:
    """Converts AST into optimized Logical Plans using standard rewrite rules."""

    def build_plan(self, ast_root: Node) -> LogicalPlan:
        """Converts raw AST into a logical plan."""
        optimized_root = self.optimize_logical_tree(ast_root)
        return LogicalPlan(optimized_root)

    def optimize_logical_tree(self, node: Node) -> Node:
        """Applies selection pushdown and structural normalization rules."""
        # Selection pushdown rule:
        # Before: Join -> Selection (Filter A)
        # After: Filter A -> Join (or pushed directly above TableScan A)
        if isinstance(node, Projection):
            return Projection(
                child=self.optimize_logical_tree(node.children[0]),
                columns=node.columns
            )
        elif isinstance(node, Selection):
            child = self.optimize_logical_tree(node.children[0])
            # Check if selection can be pushed down past Join
            if isinstance(child, Join):
                col_prefix = node.column.split(".")[0] if "." in node.column else None
                left_tables = self._get_node_tables(child.left)
                right_tables = self._get_node_tables(child.right)

                if col_prefix and col_prefix in left_tables:
                    # Push selection to left branch
                    new_left = Selection(child.left, node.predicate, node.column, node.operator, node.value)
                    return Join(self.optimize_logical_tree(new_left), child.right, child.left_key, child.right_key, child.join_type)
                elif col_prefix and col_prefix in right_tables:
                    # Push selection to right branch
                    new_right = Selection(child.right, node.predicate, node.column, node.operator, node.value)
                    return Join(child.left, self.optimize_logical_tree(new_right), child.left_key, child.right_key, child.join_type)

            return Selection(child, node.predicate, node.column, node.operator, node.value)

        elif isinstance(node, Join):
            left = self.optimize_logical_tree(node.left)
            right = self.optimize_logical_tree(node.right)
            return Join(left, right, node.left_key, node.right_key, node.join_type)

        return node

    def _get_node_tables(self, node: Node) -> List[str]:
        tables = []
        if isinstance(node, TableScan):
            tables.append(node.alias)
            tables.append(node.table_name)
        for child in node.children:
            tables.extend(self._get_node_tables(child))
        return list(set(tables))
