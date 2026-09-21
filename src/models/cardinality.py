"""ML Cardinality Estimator Model supporting Linear Regression, Random Forest, and Gradient Boosting."""

import pickle
import numpy as np
import pandas as pd
from typing import Optional, Union, Dict, Any
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

class CardinalityEstimatorModel:
    """ML model for predicting intermediate and output cardinalities of physical query plans."""

    def __init__(self, model_type: str = "random_forest", n_estimators: int = 100):
        self.model_type = model_type
        self.n_estimators = n_estimators
        self.is_trained = False
        
        if model_type == "linear":
            base_model = LinearRegression()
        elif model_type == "gradient_boosting":
            base_model = GradientBoostingRegressor(n_estimators=n_estimators, random_state=42)
        else:
            base_model = RandomForestRegressor(n_estimators=n_estimators, random_state=42)

        self.pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("regressor", base_model)
        ])

    def fit(self, X: Union[np.ndarray, pd.DataFrame], y: Union[np.ndarray, pd.Series], epochs: int = 100):
        """Trains the cardinality prediction model."""
        if hasattr(self.pipeline.named_steps["regressor"], "n_estimators"):
            self.pipeline.named_steps["regressor"].set_params(n_estimators=max(10, epochs))
            
        self.pipeline.fit(X, np.log1p(y))
        self.is_trained = True

    def predict(self, X: Union[np.ndarray, pd.DataFrame]) -> np.ndarray:
        """Predicts expected cardinality for feature vectors."""
        if not self.is_trained:
            # Fallback heuristic prediction when model is untrained
            if isinstance(X, pd.DataFrame):
                tot_rows = X["total_table_rows"].values
                filters = X["number_of_filters"].values
                joins = X["number_of_joins"].values
            else:
                X_arr = np.array(X)
                if X_arr.ndim == 1:
                    X_arr = X_arr.reshape(1, -1)
                tot_rows = X_arr[:, 5]
                filters = X_arr[:, 2]
                joins = X_arr[:, 1]
            
            # Simple fallback formula: tot_rows * (0.5^filters) * (0.8^joins)
            preds = tot_rows * (0.5 ** filters) * (0.8 ** joins)
            return np.maximum(preds, 1.0)

        log_preds = self.pipeline.predict(X)
        preds = np.expm1(log_preds)
        return np.maximum(preds, 1.0)

    def save(self, filepath: str):
        """Saves model weights to disk."""
        with open(filepath, "wb") as f:
            pickle.dump({"pipeline": self.pipeline, "is_trained": self.is_trained, "model_type": self.model_type}, f)

    def load(self, filepath: str):
        """Loads model weights from disk."""
        with open(filepath, "rb") as f:
            data = pickle.load(f)
            self.pipeline = data["pipeline"]
            self.is_trained = data["is_trained"]
            self.model_type = data.get("model_type", "random_forest")
