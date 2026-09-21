"""Query feature extractor for vectorizing physical query plans and database statistics into tabular vectors."""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Union
from ..planner.physical_plan import (
    PhysicalOperator, SeqScan, IndexScan, NestedLoopJoin, HashJoin, FilterOperator, ProjectionOperator
)
from .statistics import CatalogStatistics

class QueryFeatureExtractor:
    """Extracts numerical features from physical plans and catalog statistics for ML estimation."""

    FEATURE_NAMES = [
        "number_of_tables",
        "number_of_joins",
        "number_of_filters",
        "number_of_projections",
        "query_depth",
        "total_table_rows",
        "max_table_rows",
        "min_table_rows",
        "avg_table_rows",
        "num_indexes_total",
        "has_index_scan",
        "has_hash_join",
        "has_nested_loop",
        "num_operators"
    ]

    def __init__(self, catalog_stats: CatalogStatistics):
        self.catalog_stats = catalog_stats

    def extract_features(self, plan: PhysicalOperator) -> np.ndarray:
        """Vectorizes a physical execution plan into a 1D float array."""
        counts = {
            "tables": 0,
            "joins": 0,
            "filters": 0,
            "projections": 0,
            "has_index_scan": 0,
            "has_hash_join": 0,
            "has_nested_loop": 0
        }

        table_rows: List[float] = []
        index_counts: List[int] = []

        def _traverse(node: PhysicalOperator):
            if isinstance(node, SeqScan):
                counts["tables"] += 1
                t_stats = self.catalog_stats.get_table_stats(node.table_name)
                table_rows.append(t_stats.get("row_count", 1000))
                index_counts.append(t_stats.get("num_indexes", 0))

            elif isinstance(node, IndexScan):
                counts["tables"] += 1
                counts["has_index_scan"] = 1
                t_stats = self.catalog_stats.get_table_stats(node.table_name)
                table_rows.append(t_stats.get("row_count", 1000))
                index_counts.append(t_stats.get("num_indexes", 1))

            elif isinstance(node, NestedLoopJoin):
                counts["joins"] += 1
                counts["has_nested_loop"] = 1

            elif isinstance(node, HashJoin):
                counts["joins"] += 1
                counts["has_hash_join"] = 1

            elif isinstance(node, FilterOperator):
                counts["filters"] += 1

            elif isinstance(node, ProjectionOperator):
                counts["projections"] += 1

            for child in node.children:
                _traverse(child)

        _traverse(plan)

        num_tables = max(counts["tables"], 1)
        tot_rows = float(sum(table_rows)) if table_rows else 1000.0
        max_rows = float(max(table_rows)) if table_rows else 1000.0
        min_rows = float(min(table_rows)) if table_rows else 1000.0
        avg_rows = tot_rows / num_tables

        features = [
            float(counts["tables"]),
            float(counts["joins"]),
            float(counts["filters"]),
            float(counts["projections"]),
            float(plan.get_depth()),
            tot_rows,
            max_rows,
            min_rows,
            avg_rows,
            float(sum(index_counts)),
            float(counts["has_index_scan"]),
            float(counts["has_hash_join"]),
            float(counts["has_nested_loop"]),
            float(plan.count_operators())
        ]

        return np.array(features, dtype=np.float32)

    def extract_features_df(self, plans: List[PhysicalOperator]) -> pd.DataFrame:
        """Vectorizes a list of physical execution plans into a pandas DataFrame."""
        matrix = [self.extract_features(p) for p in plans]
        return pd.DataFrame(matrix, columns=self.FEATURE_NAMES)
