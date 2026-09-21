"""Evaluation metrics for database query optimization experiments."""

import numpy as np
from typing import List, Dict, Union, Tuple

def calculate_q_error(actual: Union[float, np.ndarray], predicted: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
    """Calculates Q-error metric: max(actual / predicted, predicted / actual)."""
    act = np.maximum(np.array(actual, dtype=np.float64), 1e-5)
    pred = np.maximum(np.array(predicted, dtype=np.float64), 1e-5)
    
    ratio1 = act / pred
    ratio2 = pred / act
    return np.maximum(ratio1, ratio2)


def calculate_regret(selected_latency: float, optimal_latency: float) -> float:
    """Calculates Regret percentage: ((selected - optimal) / optimal) * 100."""
    opt = max(optimal_latency, 1e-5)
    regret = max(0.0, (selected_latency - opt) / opt) * 100.0
    return regret


def calculate_plan_accuracy(selected_plans: List[str], optimal_plans: List[str]) -> float:
    """Calculates percentage of queries where the optimizer selected the optimal plan."""
    if not selected_plans:
        return 0.0
    matches = sum(1 for sel, opt in zip(selected_plans, optimal_plans) if sel == opt)
    return (matches / len(selected_plans)) * 100.0


def calculate_latency_percentiles(latencies_ms: List[float]) -> Dict[str, float]:
    """Calculates P50, P95, P99, and Mean latencies in milliseconds."""
    if not latencies_ms:
        return {"mean": 0.0, "p50": 0.0, "p95": 0.0, "p99": 0.0}
    
    arr = np.array(latencies_ms)
    return {
        "mean": float(np.mean(arr)),
        "p50": float(np.percentile(arr, 50)),
        "p95": float(np.percentile(arr, 95)),
        "p99": float(np.percentile(arr, 99))
    }
