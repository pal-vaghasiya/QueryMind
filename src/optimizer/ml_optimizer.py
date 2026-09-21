"""ML-Guided Query Optimizer ranking candidate plans using machine learning predictions."""

from typing import List, Tuple, Optional
from ..planner.physical_plan import PhysicalOperator
from ..planner.join_enumerator import JoinEnumerator
from ..parser.sql_parser import SQLParser
from ..features.statistics import CatalogStatistics
from ..features.query_features import QueryFeatureExtractor
from ..models.cardinality import CardinalityEstimatorModel
from ..models.cost_predictor import PlanCostPredictorModel

class MLOptimizer:
    """ML-Guided Query Optimizer using learned cardinality/cost models."""

    def __init__(
        self,
        catalog_stats: CatalogStatistics,
        cardinality_model: Optional[CardinalityEstimatorModel] = None,
        cost_model: Optional[PlanCostPredictorModel] = None
    ):
        self.catalog_stats = catalog_stats
        self.parser = SQLParser()
        self.enumerator = JoinEnumerator(catalog_stats.stats)
        self.feature_extractor = QueryFeatureExtractor(catalog_stats)
        
        self.cardinality_model = cardinality_model or CardinalityEstimatorModel()
        self.cost_model = cost_model or PlanCostPredictorModel()

    def optimize(self, sql_query: str) -> Tuple[PhysicalOperator, List[Tuple[PhysicalOperator, float, float]]]:
        """Parses query, enumerates candidate plans, extracts features, predicts costs/cardinalities, and selects best plan."""
        ast_root = self.parser.parse(sql_query)
        candidates = self.enumerator.enumerate_candidate_plans(ast_root)

        features_df = self.feature_extractor.extract_features_df(candidates)
        
        pred_cardinalities = self.cardinality_model.predict(features_df)
        pred_costs = self.cost_model.predict(features_df)

        ranked_plans = []
        for plan, card, cost in zip(candidates, pred_cardinalities, pred_costs):
            plan.estimated_cardinality = float(card)
            plan.estimated_cost = float(cost)
            ranked_plans.append((plan, float(card), float(cost)))

        # Sort candidate plans by predicted cost ascending
        ranked_plans.sort(key=lambda x: x[2])

        best_plan = ranked_plans[0][0]
        return best_plan, ranked_plans
