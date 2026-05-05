"""
Udyam Setu — Entity Resolution Decision Engine
Applies business logic and thresholds to ML probability scores.
"""

import uuid
from typing import List, Dict

class DecisionEngine:
    AUTO_LINK_THRESHOLD = 0.92
    AUTO_LINK_WITH_ANCHOR = 0.85  # Lower threshold if PAN/GSTIN present
    REVIEW_THRESHOLD = 0.60
    
    def decide(self, candidate_pair: dict, score: float, features: dict) -> dict:
        """
        Determine the action for a scored candidate pair based on thresholds and features.
        """
        has_anchor = features.get("anchor_present", 0) == 1
        
        action = "REJECT"
        reason = "Score below review threshold."
        
        if has_anchor and score >= self.AUTO_LINK_WITH_ANCHOR:
            action = "AUTO_LINK"
            reason = f"High confidence ({score:.3f}) with anchor match."
        elif not has_anchor and score >= self.AUTO_LINK_THRESHOLD:
            action = "AUTO_LINK"
            reason = f"Very high confidence ({score:.3f}) without anchor."
        elif score >= self.REVIEW_THRESHOLD:
            action = "QUEUE_REVIEW"
            reason = f"Borderline confidence ({score:.3f}). Needs human review."
            
        return {
            "action": action,
            "reason": reason,
            "requires_anchor": not has_anchor and score >= self.AUTO_LINK_WITH_ANCHOR and score < self.AUTO_LINK_THRESHOLD
        }
        
    def process_batch(self, pairs_with_scores: List[Dict]) -> Dict:
        """
        Process a batch of scored pairs and return summary statistics.
        Expects dicts with 'score' and 'features'.
        """
        summary = {
            "auto_linked": 0,
            "queued_review": 0,
            "rejected": 0
        }
        
        for pair in pairs_with_scores:
            decision = self.decide(pair, pair["score"], pair["features"])
            pair["decision"] = decision
            
            if decision["action"] == "AUTO_LINK":
                summary["auto_linked"] += 1
            elif decision["action"] == "QUEUE_REVIEW":
                summary["queued_review"] += 1
            else:
                summary["rejected"] += 1
                
        return summary
        
    def assign_ubid(self, records: List[Dict], pan: str = None, gstin: str = None) -> str:
        """
        Generates a standardized UBID. 
        If an anchor is present, incorporates it. Otherwise uses a UUID.
        """
        base = pan if pan else (gstin[2:12] if gstin else None)
        
        if base:
            return f"KA-UBID-{base}"
            
        return f"KA-UBID-{uuid.uuid4().hex[:8].upper()}"
