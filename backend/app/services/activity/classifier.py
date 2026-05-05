"""
Udyam Setu — Activity Classifier
Uses a trained LightGBM model to classify business operational status.
"""

import os
import pickle
import numpy as np
import pandas as pd
import lightgbm as lgb
import shap
from typing import Dict, Any, Tuple

class ActivityClassifier:
    ACTIVE_THRESHOLD = 0.80
    CLOSED_THRESHOLD = 0.80
    UNCERTAINTY_ENTROPY_THRESHOLD = 0.9  # entropy threshold for human review
    
    CLASS_MAPPING = {0: "ACTIVE", 1: "DORMANT", 2: "CLOSED"}
    INV_CLASS_MAPPING = {"ACTIVE": 0, "DORMANT": 1, "CLOSED": 2}
    
    def __init__(self, model_path: str = None):
        self.model = None
        self.feature_names = []
        if model_path and os.path.exists(model_path):
            self.load(model_path)
            
    def load(self, path: str):
        with open(path, 'rb') as f:
            data = pickle.load(f)
            self.model = data["model"]
            self.feature_names = data["feature_names"]
            
    def save(self, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            pickle.dump({
                "model": self.model,
                "feature_names": self.feature_names
            }, f)

    def _compute_entropy(self, probs: list) -> float:
        """Compute normalized entropy to detect model uncertainty."""
        p = np.array(probs)
        p = p[p > 0]
        entropy = -np.sum(p * np.log(p))
        normalized_entropy = entropy / np.log(len(self.CLASS_MAPPING))
        return normalized_entropy

    def classify(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Classify a single business using its 18-month feature vector."""
        if not self.model:
            raise ValueError("Model not loaded.")
            
        # Ensure ordered features
        vector = [features.get(f, float('nan')) for f in self.feature_names]
        X = np.array([vector])
        
        # LightGBM predict returns array of probabilities for each class
        probs = self.model.predict(X)[0]
        
        prob_dict = {self.CLASS_MAPPING[i]: float(p) for i, p in enumerate(probs)}
        max_idx = int(np.argmax(probs))
        predicted_status = self.CLASS_MAPPING[max_idx]
        confidence = float(probs[max_idx])
        
        # Uncertainty check
        entropy = self._compute_entropy(probs)
        needs_review = entropy > self.UNCERTAINTY_ENTROPY_THRESHOLD
        
        if predicted_status == "ACTIVE" and confidence < self.ACTIVE_THRESHOLD:
            needs_review = True
        elif predicted_status == "CLOSED" and confidence < self.CLOSED_THRESHOLD:
            needs_review = True
            
        # SHAP Explainability
        explainer = shap.TreeExplainer(self.model)
        # Note: LightGBM multiclass SHAP returns a list of arrays (one per class)
        shap_vals_all = explainer.shap_values(X)
        
        # Get SHAP values for the predicted class
        shap_vals_pred = shap_vals_all[max_idx][0]
        
        shap_dict = {}
        top_signals = []
        for name, val, feat_val in zip(self.feature_names, shap_vals_pred, vector):
            shap_dict[name] = float(val)
            top_signals.append({
                "feature": name,
                "contribution": float(val),
                "value": feat_val
            })
            
        top_signals.sort(key=lambda x: abs(x["contribution"]), reverse=True)
        
        # Build full sorted dictionary natively
        sorted_shap_dict = {x["feature"]: x["contribution"] for x in top_signals}
        
        return {
            "status": predicted_status,
            "probabilities": prob_dict,
            "confidence": confidence,
            "needs_review": needs_review,
            "shap_values": sorted_shap_dict,
            "top_signals": top_signals
        }


    def bootstrap_labels_from_ground_truth(self, ubid_status_map: Dict[str, str], features_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Merge ground truth labels with features for training.
        """
        labels = []
        valid_indices = []
        
        for ubid in features_df.index:
            if ubid in ubid_status_map:
                status_str = ubid_status_map[ubid]
                labels.append(self.INV_CLASS_MAPPING[status_str])
                valid_indices.append(ubid)
                
        X = features_df.loc[valid_indices].copy()
        y = pd.Series(labels, index=valid_indices)
        
        return X, y

    def classify_all_ubids(self):
        """Placeholder for Celery task to recompute status for all UBIDs and update ubid_registry."""
        pass
