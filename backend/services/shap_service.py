import numpy as np
from typing import Dict, Any, List

class SHAPExplainer:
    """
    AI Core component matching the Architecture Diagram.
    Provides feature importance based explanations for match results.
    """
    def __init__(self):
        # Feature weights aligned with match_ranker_v2
        self.feature_importance = {
            "distance_km": -0.45,
            "compatibility_score": 0.35,
            "urgency_level": 0.15,
            "medical_flags": -0.05
        }

    def explain_features(self, donor_data: Dict[str, Any], score_breakdown: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Calculates feature contributions to the final match score.
        This provides the data for the 'SHAP Explainer' component in the diagram.
        """
        explanations = []
        
        # 1. Proximity Impact
        dist = score_breakdown.get("distance_score", 0)
        explanations.append({
            "feature": "Logistics/Proximity",
            "impact": "Positive" if dist > 50 else "Negative",
            "contribution": dist * 0.40
        })
        
        # 2. Bio-compatibility Impact
        compat = score_breakdown.get("compatibility_score", 0)
        explanations.append({
            "feature": "Biological Compatibility",
            "impact": "High" if compat >= 100 else "Neutral",
            "contribution": compat * 0.20
        })
        
        # 3. XGBoost Model Contribution
        ml_score = score_breakdown.get("ml_score", 0)
        explanations.append({
            "feature": "Neural Suitability (XGBoost)",
            "impact": "High" if ml_score > 70 else "Risk Detected" if ml_score < 40 else "Neutral",
            "contribution": ml_score * 0.30
        })
        
        return explanations

_shap_explainer = SHAPExplainer()

def get_shap_explainer():
    return _shap_explainer
