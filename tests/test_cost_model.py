"""Unit tests for Traditional Cost Model and features."""

import pytest
from src.features.statistics import CatalogStatistics
from src.optimizer.cost_model import TraditionalCostModel
from src.planner.physical_plan import SeqScan, IndexScan, NestedLoopJoin

def test_traditional_cost_model_seq_scan():
    stats = CatalogStatistics()
    stats.stats["students"] = {"row_count": 1000, "num_columns": 5, "num_indexes": 1}
    
    cost_model = TraditionalCostModel(stats)
    seq = SeqScan("students", "s")
    cost = cost_model.estimate_plan_cost(seq)

    assert cost > 0.0
    assert seq.estimated_cardinality == 1000.0

def test_traditional_cost_model_nlj():
    stats = CatalogStatistics()
    stats.stats["students"] = {"row_count": 1000, "num_columns": 5, "num_indexes": 1}
    stats.stats["enrollments"] = {"row_count": 5000, "num_columns": 5, "num_indexes": 1}

    cost_model = TraditionalCostModel(stats)
    l_scan = SeqScan("students", "s")
    r_scan = SeqScan("enrollments", "e")
    nlj = NestedLoopJoin(l_scan, r_scan, "s.id", "e.student_id")

    cost = cost_model.estimate_plan_cost(nlj)
    assert cost > 0.0
    assert nlj.estimated_cardinality > 0.0
