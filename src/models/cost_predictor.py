"""ML Plan Cost Predictor Model for estimating plan execution runtime."""

import pickle
import numpy as np
import pandas as pd
from typing import Optional, Union
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

class PlanCostPredictorModel:
    """Predicts execution cost and runtime for physical query plans."""

    def __init__(self, n_estimators: int = 100):
        self.pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("regressor", RandomForestRegressor(n_estimators=n_estimators, random_state=42))
        ])
        self.is_trained = False

    def fit(self, X: Union[np.ndarray, pd.DataFrame], y_cost: Union[np.ndarray, pd.Series], epochs: int = 100):
        """Trains cost prediction model."""
        self.pipeline.named_steps["regressor"].set_params(n_estimators=max(10, epochs))
        self.pipeline.fit(X, np.log1p(y_cost))
        self.is_trained = True

    def predict(self, X: Union[np.ndarray, pd.DataFrame]) -> np.ndarray:
        """Predicts cost values for given query plan features."""
        if not self.is_trained:
            # Fallback heuristic prediction when model is untrained
            if isinstance(X, pd.DataFrame):
                depth = X["query_depth"].values
                rows = X["avg_table_rows"].values
                ops = X["num_operators"].values
            else:
                X_arr = np.array(X)
                if X_arr.ndim == 1:
                    X_arr = X_arr.reshape(1, -1)
                depth = X_arr[:, 4]
                rows = X_arr[:, 8]
                ops = X_arr[:, 13]
            
            # Simple fallback formula
            cost = (rows * 0.1) + (ops * 10.0) + (depth * 5.0)
            return np.maximum(cost, 1.0)

        log_preds = self.pipeline.predict(X)
        return np.maximum(np.expm1(log_preds), 1.0)

    def save(self, filepath: str):
        with open(filepath, "wb") as f:
            pickle.dump({"pipeline": self.pipeline, "is_trained": self.is_trained}, f)

    def load(self, filepath: str):
        with open(filepath, "rb") as f:
            data = pickle.load(f)
            self.pipeline = data["pipeline"]
            self.is_trained = data["is_trained"]
