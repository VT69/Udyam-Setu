"""
Udyam Setu — Entity Resolution ML Model
XGBoost Classifier with Platt Scaling calibration and SHAP explainability.
"""

import os
import pickle
import logging
import numpy as np
import xgboost as xgb
import shap
from sklearn.calibration import CalibratedClassifierCV

logger = logging.getLogger(__name__)

class EntityResolutionModel:
    def __init__(self, model_path: str = None):
        self.xgb_model = None
        self.calibrated_model = None
        self.is_trained = False
        
        if model_path and os.path.exists(model_path):
            self.load(model_path)

    def predict_proba(self, feature_vectors: list[list]) -> list[float]:
        """Returns calibrated probability scores for a list of feature vectors."""
        if not self.is_trained or self.calibrated_model is None:
            raise ValueError("Model is not trained or loaded yet.")
            
        X = np.array(feature_vectors, dtype=float)
        # predict_proba returns [[prob_0, prob_1], ...]
        probas = self.calibrated_model.predict_proba(X)
        return probas[:, 1].tolist()

    def predict_with_shap(self, feature_vector: list, feature_names: list) -> dict:
        """
        Predicts score and generates SHAP values for explainability.
        Returns score, ordered shap_values, and top_factors.
        """
        if not self.is_trained or self.xgb_model is None:
            raise ValueError("Model is not trained or loaded yet.")
            
        X = np.array(feature_vector, dtype=float).reshape(1, -1)
        score = self.calibrated_model.predict_proba(X)[0, 1]
        
        # Use TreeExplainer on the base XGBoost model
        explainer = shap.TreeExplainer(self.xgb_model)
        shap_vals = explainer.shap_values(X)[0]  # Array of SHAP values for the single instance
        
        shap_dict = {}
        factors = []
        
        for name, val, feat_val in zip(feature_names, shap_vals, feature_vector):
            shap_dict[name] = float(val)
            factors.append({
                "feature": name,
                "contribution": float(val),
                "direction": "positive" if val > 0 else "negative",
                "value": feat_val
            })
            
        # Sort factors by absolute contribution, descending
        factors.sort(key=lambda x: abs(x["contribution"]), reverse=True)
        top_factors = factors[:5]
        
        return {
            "score": float(score),
            "shap_values": shap_dict,
            "top_factors": top_factors
        }

    def train(self, X: list, y: list):
        """Train XGBoost base model and wrap in Platt scaling calibration."""
        logger.info(f"Training XGBoost on {len(X)} samples...")
        
        X_np = np.array(X, dtype=float)
        y_np = np.array(y, dtype=int)
        
        self.xgb_model = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=4,
            learning_rate=0.1,
            subsample=0.8,
            use_label_encoder=False,
            eval_metric="logloss"
        )
        
        # Train base model
        self.xgb_model.fit(X_np, y_np)
        
        # Calibrate using sigmoid (Platt Scaling) with cross-validation to prevent data leakage
        logger.info("Applying Platt Scaling calibration (cv=5)...")
        self.calibrated_model = CalibratedClassifierCV(
            estimator=self.xgb_model,
            method='sigmoid',
            cv=5
        )
        self.calibrated_model.fit(X_np, y_np)
        
        self.is_trained = True
        logger.info("Training complete.")

    def bootstrap_labels(self, features_list: list[dict]) -> tuple[list, list]:
        """
        Rule-based label generation for cold start.
        Returns X (list of feature dicts/vectors) and y (list of labels)
        """
        labeled_X = []
        labeled_y = []
        
        for f in features_list:
            # --- Rule: Label 1 (MATCH) ---
            # PAN exact match
            if f.get("pan_exact_match") == 1:
                labeled_X.append(f)
                labeled_y.append(1)
                continue
                
            # Strong name match + pincode match
            if f.get("name_jaro_winkler", 0) > 0.92 and f.get("address_pincode_match") == 1:
                # No anchor conflict
                if f.get("pan_exact_match") == 0 and f.get("anchor_present") == 1:
                    pass # Conflict! They have anchors but they don't match
                else:
                    labeled_X.append(f)
                    labeled_y.append(1)
                    continue

            # --- Rule: Label 0 (NON-MATCH) ---
            # Same department + diff pincode + weak name
            if f.get("same_department") == 1 and f.get("address_pincode_match") == 0 and f.get("name_token_set_ratio", 0) < 0.4:
                labeled_X.append(f)
                labeled_y.append(0)
                continue
                
        return labeled_X, labeled_y

    def save(self, path: str):
        """Save calibrated model and base XGB model."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            pickle.dump({
                "calibrated_model": self.calibrated_model,
                "xgb_model": self.xgb_model
            }, f)
        logger.info(f"Model saved to {path}")

    def load(self, path: str):
        """Load model from file."""
        with open(path, 'rb') as f:
            data = pickle.load(f)
            self.calibrated_model = data["calibrated_model"]
            self.xgb_model = data["xgb_model"]
            self.is_trained = True
        logger.info(f"Model loaded from {path}")
