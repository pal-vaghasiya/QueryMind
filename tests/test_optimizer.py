"""Unit tests for Baseline CBO and ML-Guided Optimizers."""

import pytest
from src.executor.database import DatabaseEngine
from src.features.statistics import CatalogStatistics
from src.optimizer.baseline import TraditionalBaselineOptimizer
from src.optimizer.ml_optimizer import MLOptimizer

def test_baseline_optimizer():
    db = DatabaseEngine()
    db.setup_demo_schema(num_students=100, num_courses=20, num_enrollments=300)
    stats = CatalogStatistics()
    stats.collect_from_sqlite(db.conn)

    optimizer = TraditionalBaselineOptimizer(stats)
    sql = "SELECT * FROM students s JOIN enrollments e ON s.id = e.student_id WHERE s.cgpa > 8.0;"
    best_plan, ranked_plans = optimizer.optimize(sql)

    assert best_plan is not None
    assert len(ranked_plans) > 0
    assert ranked_plans[0][0] == best_plan

def test_ml_optimizer():
    db = DatabaseEngine()
    db.setup_demo_schema(num_students=100, num_courses=20, num_enrollments=300)
    stats = CatalogStatistics()
    stats.collect_from_sqlite(db.conn)

    ml_opt = MLOptimizer(stats)
    sql = "SELECT * FROM students s JOIN enrollments e ON s.id = e.student_id WHERE s.cgpa > 8.0;"
    best_plan, ranked_plans = ml_opt.optimize(sql)

    assert best_plan is not None
    assert len(ranked_plans) > 0
