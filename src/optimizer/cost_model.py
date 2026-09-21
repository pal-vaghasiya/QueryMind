"""Traditional Cost Model calculating physical plan execution cost estimates based on DBMS cost formulas."""

from typing import Dict, Any, Tuple
from ..planner.physical_plan import (
    PhysicalOperator, SeqScan, IndexScan, NestedLoopJoin, HashJoin, FilterOperator, ProjectionOperator
)
from ..features.statistics import CatalogStatistics

class TraditionalCostModel:
    """Traditional Cost-Based Optimizer (CBO) cost estimation model."""

    # Cost constants (similar to PostgreSQL default cost weights)
    TUPLE_COST = 0.01
    PAGE_READ_COST = 1.0
    INDEX_TUPLE_COST = 0.005
    HASH_BUILD_COST = 0.02
    FILTER_COST = 0.002

    def __init__(self, catalog_stats: CatalogStatistics):
        self.catalog_stats = catalog_stats

    def estimate_plan_cost(self, plan: PhysicalOperator) -> float:
        """Recursively calculates estimated cost and populates cardinalities/costs on the plan nodes."""
        card, cost = self._compute_node_cost(plan)
        plan.estimated_cardinality = card
        plan.estimated_cost = cost
        return cost

    def _compute_node_cost(self, node: PhysicalOperator) -> Tuple[float, float]:
        """Returns (estimated_cardinality, cumulative_cost)."""
        if isinstance(node, SeqScan):
            t_stats = self.catalog_stats.get_table_stats(node.table_name)
            rows = float(t_stats.get("row_count", 1000))
            pages = max(1.0, rows / 50.0)
            cost = (pages * self.PAGE_READ_COST) + (rows * self.TUPLE_COST)
            return rows, cost

        elif isinstance(node, IndexScan):
            t_stats = self.catalog_stats.get_table_stats(node.table_name)
            rows = float(t_stats.get("row_count", 1000))
            # Index scan selectivity estimation ~10% returned
            sel_rows = max(1.0, rows * 0.1)
            pages = max(1.0, sel_rows / 50.0)
            cost = (pages * self.PAGE_READ_COST) + (sel_rows * self.INDEX_TUPLE_COST)
            return sel_rows, cost

        elif isinstance(node, FilterOperator):
            child_card, child_cost = self._compute_node_cost(node.children[0])
            # Selectivity factor based on operator
            if node.operator in [">", "<", ">=", "<="]:
                selectivity = 0.33
            elif node.operator == "=":
                col_stats = self.catalog_stats.get_column_stats("", node.column.split(".")[-1])
                distincts = max(1, col_stats.get("distinct_values", 10))
                selectivity = 1.0 / distincts
            else:
                selectivity = 0.5

            card = max(1.0, child_card * selectivity)
            cost = child_cost + (child_card * self.FILTER_COST)
            return card, cost

        elif isinstance(node, NestedLoopJoin):
            l_card, l_cost = self._compute_node_cost(node.left)
            r_card, r_cost = self._compute_node_cost(node.right)
            
            # Join cardinality estimation
            join_card = max(1.0, min(l_card, r_card) * 0.5)
            # NLJ Cost: left_cost + (left_card * right_cost)
            cost = l_cost + (l_card * r_cost) + (join_card * self.TUPLE_COST)
            return join_card, cost

        elif isinstance(node, HashJoin):
            l_card, l_cost = self._compute_node_cost(node.left)
            r_card, r_cost = self._compute_node_cost(node.right)

            join_card = max(1.0, min(l_card, r_card) * 0.5)
            # Hash Join Cost: left_cost + right_cost + hash_build + hash_probe
            cost = l_cost + r_cost + (l_card * self.HASH_BUILD_COST) + ((l_card + r_card) * self.TUPLE_COST)
            return join_card, cost

        elif isinstance(node, ProjectionOperator):
            return self._compute_node_cost(node.children[0])

        return 100.0, 100.0
