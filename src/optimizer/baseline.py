"""Traditional Baseline Optimizer selecting plans based on traditional DBMS CBO cost estimates."""

from typing import List, Tuple
from ..planner.physical_plan import PhysicalOperator
from ..planner.join_enumerator import JoinEnumerator
from ..parser.sql_parser import SQLParser
from ..features.statistics import CatalogStatistics
from .cost_model import TraditionalCostModel

class TraditionalBaselineOptimizer:
    """Traditional Cost-Based Optimizer (CBO) baseline."""

    def __init__(self, catalog_stats: CatalogStatistics):
        self.catalog_stats = catalog_stats
        self.parser = SQLParser()
        self.cost_model = TraditionalCostModel(catalog_stats)
        self.enumerator = JoinEnumerator(catalog_stats.stats)

    def optimize(self, sql_query: str) -> Tuple[PhysicalOperator, List[Tuple[PhysicalOperator, float]]]:
        """Parses query, enumerates candidate plans, calculates CBO costs, and selects lowest-cost plan."""
        ast_root = self.parser.parse(sql_query)
        candidates = self.enumerator.enumerate_candidate_plans(ast_root)

        ranked_plans = []
        for plan in candidates:
            cost = self.cost_model.estimate_plan_cost(plan)
            ranked_plans.append((plan, cost))

        # Sort candidate plans by cost ascending
        ranked_plans.sort(key=lambda x: x[1])

        best_plan, best_cost = ranked_plans[0]
        return best_plan, ranked_plans
