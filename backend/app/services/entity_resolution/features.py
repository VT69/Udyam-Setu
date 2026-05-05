"""
Udyam Setu — Entity Resolution Feature Extraction
Computes numerical features between two records for ML classification.
"""

from rapidfuzz import fuzz
from datetime import date
from typing import List

from app.services.entity_resolution.blocking import haversine


class FeatureExtractor:
    FEATURE_NAMES = [
        "name_jaro_winkler",
        "name_token_set_ratio",
        "name_soundex_match",
        "core_name_jaro",
        "address_street_similarity",
        "address_locality_match",
        "address_pincode_match",
        "address_proximity_score",
        "pan_exact_match",
        "gstin_exact_match",
        "nic_code_overlap",
        "registration_date_proximity",
        "phone_match",
        "email_match",
        "signatory_jaro",
        "same_department",
        "blocking_signal_count",
        "anchor_present"
    ]

    def _sim_jaro_winkler(self, s1: str, s2: str) -> float:
        if not s1 or not s2:
            return float('nan')
        return fuzz.jaro_winkler(s1.lower(), s2.lower()) / 100.0

    def _sim_token_set(self, s1: str, s2: str) -> float:
        if not s1 or not s2:
            return float('nan')
        return fuzz.token_set_ratio(s1.lower(), s2.lower()) / 100.0

    def _sim_jaro(self, s1: str, s2: str) -> float:
        if not s1 or not s2:
            return float('nan')
        # Rapidfuzz fuzz.jaro doesn't strictly exist by name, usually Jaro is included or we use JaroWinkler
        # Let's use Normalized InDel similarity or JaroWinkler without prefix scaling.
        # fuzz.ratio is Levenshtein based. fuzz.jaro_winkler is Jaro-Winkler.
        # Actually, rapidfuzz.distance.Jaro.normalized_similarity exists in newer versions.
        # We will fallback to basic ratio / 100 if Jaro isn't directly exposed in fuzz.
        # But we can just use fuzz.ratio for core name or JaroWinkler. The user asked for core_name_jaro.
        # rapidfuzz.distance.Jaro.normalized_similarity(s1, s2)
        from rapidfuzz.distance import Jaro
        return Jaro.normalized_similarity(s1.lower(), s2.lower())

    def _exact_match(self, s1: str, s2: str) -> int:
        if not s1 or not s2:
            return 0
        return 1 if s1.lower().strip() == s2.lower().strip() else 0

    def extract_features(self, record_a: dict, record_b: dict, blocking_signals: list) -> dict:
        """Computes similarity vectors between two normalized records."""
        
        # --- Name Features ---
        name_a = record_a.get("business_name_normalized", "")
        name_b = record_b.get("business_name_normalized", "")
        core_a = record_a.get("core_name", "")
        core_b = record_b.get("core_name", "")
        
        # --- Address Features ---
        street_a = record_a.get("address_street", "")
        street_b = record_b.get("address_street", "")
        
        # --- Proximity ---
        prox_score = float('nan')
        lat_a, lng_a = record_a.get("address_lat"), record_a.get("address_lng")
        lat_b, lng_b = record_b.get("address_lat"), record_b.get("address_lng")
        if lat_a is not None and lng_a is not None and lat_b is not None and lng_b is not None:
            dist = haversine(lat_a, lng_a, lat_b, lng_b)
            # 1 - (distance/200), clipped to [0,1]
            prox_score = max(0.0, min(1.0, 1.0 - (dist / 200.0)))
            
        # --- Dates ---
        reg_prox = float('nan')
        date_a = record_a.get("registration_date")
        date_b = record_b.get("registration_date")
        if date_a and date_b and isinstance(date_a, date) and isinstance(date_b, date):
            diff_days = abs((date_a - date_b).days)
            reg_prox = max(0.0, 1.0 - (diff_days / 365.0))
            
        # --- NIC Overlap ---
        nic_a = str(record_a.get("nic_code", ""))
        nic_b = str(record_b.get("nic_code", ""))
        nic_overlap = float('nan')
        if nic_a and nic_b:
            if nic_a == nic_b:
                nic_overlap = 1.0
            elif nic_a[:2] == nic_b[:2]:
                nic_overlap = 0.5 # Same 2-digit division
            else:
                nic_overlap = 0.0

        features = {
            "name_jaro_winkler": self._sim_jaro_winkler(name_a, name_b),
            "name_token_set_ratio": self._sim_token_set(name_a, name_b),
            "name_soundex_match": self._exact_match(record_a.get("soundex", ""), record_b.get("soundex", "")),
            "core_name_jaro": self._sim_jaro(core_a, core_b),
            
            "address_street_similarity": self._sim_token_set(street_a, street_b),
            "address_locality_match": self._exact_match(record_a.get("address_locality", ""), record_b.get("address_locality", "")),
            "address_pincode_match": self._exact_match(record_a.get("address_pincode", ""), record_b.get("address_pincode", "")),
            "address_proximity_score": prox_score,
            
            "pan_exact_match": self._exact_match(record_a.get("pan", ""), record_b.get("pan", "")),
            "gstin_exact_match": self._exact_match(record_a.get("gstin", ""), record_b.get("gstin", "")),
            "nic_code_overlap": nic_overlap,
            "registration_date_proximity": reg_prox,
            
            "phone_match": self._exact_match(str(record_a.get("phone", "")), str(record_b.get("phone", ""))),
            "email_match": self._exact_match(record_a.get("email", ""), record_b.get("email", "")),
            "signatory_jaro": self._sim_jaro_winkler(record_a.get("signatory_name", ""), record_b.get("signatory_name", "")),
            
            "same_department": 1 if record_a.get("department") == record_b.get("department") and record_a.get("department") else 0,
            "blocking_signal_count": len(blocking_signals) if blocking_signals else 0,
            
            "anchor_present": 1 if (record_a.get("pan") or record_a.get("gstin") or record_b.get("pan") or record_b.get("gstin")) else 0
        }
        
        return features

    def features_to_vector(self, features: dict) -> List[float]:
        """Returns ordered list of feature values corresponding to FEATURE_NAMES."""
        return [features.get(name, float('nan')) for name in self.FEATURE_NAMES]
