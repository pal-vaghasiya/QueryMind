"""Unified Command Line Interface for QueryMind - Learning-Based Query Optimizer."""

import argparse
import os
import sys
import pytest
import pandas as pd
import numpy as np

from src.executor.database import DatabaseEngine, WorkloadGenerator
from src.features.statistics import CatalogStatistics
from src.features.query_features import QueryFeatureExtractor
from src.models.cardinality import CardinalityEstimatorModel
from src.models.cost_predictor import PlanCostPredictorModel
from src.optimizer.baseline import TraditionalBaselineOptimizer
from src.optimizer.ml_optimizer import MLOptimizer
from src.evaluation.benchmark import BenchmarkRunner

MODEL_DIR = "models"
CARD_MODEL_PATH = os.path.join(MODEL_DIR, "cardinality_model.pkl")
COST_MODEL_PATH = os.path.join(MODEL_DIR, "cost_model.pkl")

def train_models(epochs: int = 100):
    """Generates synthetic workload, extracts features, and trains ML models for the specified epochs."""
    print(f"=== [QueryMind] Starting ML Model Training (Epochs: {epochs}) ===")
    os.makedirs(MODEL_DIR, exist_ok=True)
    os.makedirs("data/processed", exist_ok=True)

    db = DatabaseEngine()
    print("Setting up synthetic database schema and collecting statistics...")
    db.setup_demo_schema()

    stats = CatalogStatistics()
    stats.collect_from_sqlite(db.conn)

    wg = WorkloadGenerator(db)
    print("Generating synthetic workload queries...")
    queries = wg.generate_queries(count=200)

    ml_opt = MLOptimizer(stats)
    dataset_rows = []

    print("Executing queries to record execution runtimes and cardinalities...")
    for sql in queries:
        try:
            actual_card, actual_time = db.execute_query(sql)
            best_plan, candidates = ml_opt.optimize(sql)
            
            for plan, card, cost in candidates:
                feats = ml_opt.feature_extractor.extract_features(plan)
                row_dict = {f_name: val for f_name, val in zip(ml_opt.feature_extractor.FEATURE_NAMES, feats)}
                row_dict["actual_cardinality"] = actual_card
                row_dict["actual_runtime_ms"] = actual_time
                dataset_rows.append(row_dict)
        except Exception as e:
            continue

    df = pd.DataFrame(dataset_rows)
    df.to_csv("data/processed/workload_dataset.csv", index=False)
    print(f"Dataset saved to data/processed/workload_dataset.csv ({len(df)} samples).")

    X = df[ml_opt.feature_extractor.FEATURE_NAMES]
    y_card = df["actual_cardinality"]
    y_cost = df["actual_runtime_ms"]

    print(f"Fitting Cardinality Estimator Model (Epochs/Estimators: {epochs})...")
    card_model = CardinalityEstimatorModel(n_estimators=epochs)
    card_model.fit(X, y_card, epochs=epochs)
    card_model.save(CARD_MODEL_PATH)
    print(f"Cardinality model saved to {CARD_MODEL_PATH}.")

    print(f"Fitting Plan Cost Predictor Model (Epochs/Estimators: {epochs})...")
    cost_model = PlanCostPredictorModel(n_estimators=epochs)
    cost_model.fit(X, y_cost, epochs=epochs)
    cost_model.save(COST_MODEL_PATH)
    print(f"Cost model saved to {COST_MODEL_PATH}.")

    print("=== Training Complete! ===")


def run_tests_and_benchmark():
    """Runs test suite and benchmark evaluation."""
    print("=== [QueryMind] Running Unit Tests ===")
    exit_code = pytest.main(["-v", "tests"])
    if exit_code != 0:
        print(f"Warning: Tests completed with exit code {exit_code}")

    print("\n=== [QueryMind] Running Experimental Evaluation Benchmark ===")
    db = DatabaseEngine()
    db.setup_demo_schema()

    stats = CatalogStatistics()
    stats.collect_from_sqlite(db.conn)

    wg = WorkloadGenerator(db)
    queries = wg.generate_queries(count=20)

    runner = BenchmarkRunner(db, stats)
    results = runner.run_benchmark(queries)

    print("\n--- Experimental Results ---")
    print(f"Total Benchmark Queries: {results['total_queries']}")
    print("\nTraditional Baseline Optimizer:")
    print(f"  Mean Q-Error:       {results['baseline']['mean_q_error']:.2f}")
    print(f"  Plan Accuracy:      {results['baseline']['plan_accuracy']:.1f}%")
    print(f"  Mean Latency:       {results['baseline']['mean_latency_ms']:.2f} ms")
    print(f"  P95 Latency:        {results['baseline']['p95_latency_ms']:.2f} ms")

    print("\nML-Guided Query Optimizer:")
    print(f"  Mean Q-Error:       {results['ml']['mean_q_error']:.2f}")
    print(f"  Plan Accuracy:      {results['ml']['plan_accuracy']:.1f}%")
    print(f"  Mean Latency:       {results['ml']['mean_latency_ms']:.2f} ms")
    print(f"  P95 Latency:        {results['ml']['p95_latency_ms']:.2f} ms")
    print("========================================")


def optimize_query(sql_query: str):
    """Optimizes a single query and displays plan options."""
    db = DatabaseEngine()
    db.setup_demo_schema()

    stats = CatalogStatistics()
    stats.collect_from_sqlite(db.conn)

    ml_opt = MLOptimizer(stats)

    # Load trained models if available
    if os.path.exists(CARD_MODEL_PATH):
        ml_opt.cardinality_model.load(CARD_MODEL_PATH)
    if os.path.exists(COST_MODEL_PATH):
        ml_opt.cost_model.load(COST_MODEL_PATH)

    print("\n=========================================")
    print("QueryMind Optimizer")
    print("=========================================")
    print(f"Query:\n{sql_query}\n")

    best_plan, candidate_plans = ml_opt.optimize(sql_query)

    print("Candidate Execution Plans:")
    print("-----------------------------------------")
    for i, (plan, card, cost) in enumerate(candidate_plans, 1):
        print(f"Plan {i}: Estimated Cost = {cost:.2f} | Estimated Rows = {card:.0f}")
        print(f"        Plan Tree: {plan}")

    print("\n-----------------------------------------")
    print(f"Selected Best Plan: Plan 1 ({best_plan})")
    print(f"Estimated Cost: {best_plan.estimated_cost:.2f}")

    actual_rows, actual_time = db.execute_query(sql_query)
    print(f"Actual Execution Time: {actual_time:.2f} ms ({actual_rows} rows)")
    print("=========================================\n")


def main():
    parser = argparse.ArgumentParser(description="QueryMind — Learning-Based Query Optimizer CLI")
    parser.add_argument("--train", action="store_true", help="Train the ML models on synthetic query workloads")
    parser.add_argument("--epochs", "--epoch", type=int, default=50, help="Number of training epochs/estimators (default: 50)")
    parser.add_argument("--test", action="store_true", help="Run tests and evaluation benchmark")
    parser.add_argument("--query", type=str, help="SQL query to optimize")

    args = parser.parse_args()

    if args.train:
        train_models(epochs=args.epochs)
    elif args.test:
        run_tests_and_benchmark()
    elif args.query:
        optimize_query(args.query)
    else:
        # Default demo behavior if no flags passed
        print("QueryMind - Learning-Based Query Optimizer")
        print("Usage:")
        print("  python cli.py --train [--epochs 50]")
        print("  python cli.py --test")
        print("  python cli.py --query \"SELECT * FROM students s JOIN enrollments e ON s.id = e.student_id WHERE s.cgpa > 8.0;\"\n")
        
        # Run demo optimization query
        optimize_query("SELECT * FROM students s JOIN enrollments e ON s.id = e.student_id WHERE s.cgpa > 8.0;")


if __name__ == "__main__":
    main()
