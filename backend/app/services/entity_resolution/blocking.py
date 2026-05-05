"""
Udyam Setu — Entity Resolution Blocking
Generates candidate pairs from normalized department records using multi-pass rules.
"""

import math
import logging
from collections import defaultdict
from itertools import combinations

logger = logging.getLogger(__name__)

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance in meters between two points on the earth."""
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return float('inf')
    
    R = 6371.0 # Radius of earth in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) * math.sin(dlat / 2) +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) * math.sin(dlon / 2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c * 1000 # returns meters

class BlockingEngine:
    def __init__(self):
        self.blocks = [
            ("ANCHOR_PAN", self._block_anchor),
            ("PHONETIC_PIN", self._block_phonetic_pin),
            ("TOKEN_OVERLAP", self._block_token_overlap),
            ("ADDRESS_PROXIMITY", self._block_address_proximity),
        ]

    def generate_candidate_pairs(self, records: list[dict]) -> list[dict]:
        """
        Runs multiple blocking passes and returns deduplicated pairs.
        Returns: list of {record_a_id, record_b_id, blocking_signals: list[str]}
        """
        pair_signals = defaultdict(list)
        
        for block_name, block_func in self.blocks:
            logger.info(f"Running block pass: {block_name}")
            pairs = block_func(records)
            logger.info(f"Block pass {block_name} generated {len(pairs)} pairs")
            
            for r_a, r_b in pairs:
                # Ensure ordered and not self-pairing
                if r_a != r_b:
                    pair_key = tuple(sorted((r_a, r_b)))
                    pair_signals[pair_key].append(block_name)

        # Convert to final list of dicts
        results = []
        for (r_a, r_b), signals in pair_signals.items():
            results.append({
                "record_a_id": str(r_a),
                "record_b_id": str(r_b),
                "blocking_signals": list(set(signals)) # Deduplicate signals if any
            })
            
        logger.info(f"Total unique candidate pairs generated: {len(results)}")
        return results

    def _block_anchor(self, records: list[dict]) -> set[tuple]:
        """Exact match on valid PAN or GSTIN."""
        pairs = set()
        
        pan_map = defaultdict(list)
        gstin_map = defaultdict(list)
        
        for r in records:
            if r.get("pan"):
                pan_map[r["pan"]].append(r["id"])
            if r.get("gstin"):
                gstin_map[r["gstin"]].append(r["id"])
                
        for ids in pan_map.values():
            if len(ids) > 1:
                pairs.update(combinations(ids, 2))
                
        for ids in gstin_map.values():
            if len(ids) > 1:
                pairs.update(combinations(ids, 2))
                
        return pairs

    def _block_phonetic_pin(self, records: list[dict]) -> set[tuple]:
        """Same pincode AND Soundex match on core_name."""
        pairs = set()
        bucket_map = defaultdict(list)
        
        for r in records:
            pincode = r.get("address_pincode")
            soundex = r.get("soundex")
            if pincode and soundex:
                bucket_map[(pincode, soundex)].append(r["id"])
                
        for ids in bucket_map.values():
            if len(ids) > 1:
                pairs.update(combinations(ids, 2))
                
        return pairs

    def _block_token_overlap(self, records: list[dict]) -> set[tuple]:
        """Jaccard similarity > 0.55 on name tokens, same district."""
        pairs = set()
        
        district_map = defaultdict(list)
        for r in records:
            dist = r.get("address_district")
            if dist and dist != "Unknown":
                district_map[dist].append(r)
                
        for dist, dist_records in district_map.items():
            for i, r_a in enumerate(dist_records):
                tokens_a = set(r_a.get("business_name_tokens", []))
                if not tokens_a:
                    continue
                    
                for j in range(i + 1, len(dist_records)):
                    r_b = dist_records[j]
                    tokens_b = set(r_b.get("business_name_tokens", []))
                    if not tokens_b:
                        continue
                        
                    intersection = len(tokens_a & tokens_b)
                    union = len(tokens_a | tokens_b)
                    
                    if union > 0:
                        jaccard = intersection / union
                        if jaccard > 0.55:
                            pairs.add((r_a["id"], r_b["id"]))
                            
        return pairs

    def _block_address_proximity(self, records: list[dict]) -> set[tuple]:
        """Haversine distance < 200m AND name token overlap > 0.35."""
        pairs = set()
        
        # Filter records with lat/lng
        geo_records = [r for r in records if r.get("address_lat") is not None and r.get("address_lng") is not None]
        
        for i, r_a in enumerate(geo_records):
            tokens_a = set(r_a.get("business_name_tokens", []))
            
            for j in range(i + 1, len(geo_records)):
                r_b = geo_records[j]
                
                dist_m = haversine(r_a["address_lat"], r_a["address_lng"], r_b["address_lat"], r_b["address_lng"])
                if dist_m < 200:
                    tokens_b = set(r_b.get("business_name_tokens", []))
                    intersection = len(tokens_a & tokens_b)
                    union = len(tokens_a | tokens_b)
                    
                    if union > 0:
                        jaccard = intersection / union
                        if jaccard > 0.35:
                            pairs.add((r_a["id"], r_b["id"]))
                            
        return pairs
