"""
Udyam Setu — Activity Feature Engineer
Computes rolling 18-month feature vectors from business event timeseries data.
"""

import math
from datetime import datetime
from collections import defaultdict
import numpy as np
import pandas as pd
from typing import List, Dict, Any

from app.models.enums import Department

class ActivityFeatureEngineer:
    WINDOW_MONTHS = 18
    EXPECTED_DEPARTMENTS = 4  # e.g., SHOP_ESTABLISHMENT, FACTORIES, LABOUR, KSPCB
    
    def compute_features(self, ubid: str, events: List[Dict[str, Any]], as_of: datetime) -> Dict[str, Any]:
        """
        Compute an 18-month rolling feature vector for activity classification.
        Assumes events are sorted by event_time descending.
        """
        # Filter events to only the 18 month window
        window_start = as_of - pd.DateOffset(months=self.WINDOW_MONTHS)
        valid_events = [e for e in events if e["event_time"] >= window_start and e["event_time"] <= as_of]
        
        # ─── Recency Features ──────────────────────────────────────────────
        days_since_last_event = float('nan')
        days_since_last_event_by_dept = {}
        
        if valid_events:
            # First event is most recent since sorted desc
            latest_time = max(e["event_time"] for e in valid_events)
            days_since_last_event = (as_of - latest_time).days
            
            for evt in valid_events:
                dept = evt["department"]
                if dept not in days_since_last_event_by_dept:
                    days_since_last_event_by_dept[dept] = (as_of - evt["event_time"]).days

        # ─── Frequency Features ────────────────────────────────────────────
        month_counts = defaultdict(int)
        for evt in valid_events:
            # e.g. "2023-01"
            m_key = evt["event_time"].strftime("%Y-%m")
            month_counts[m_key] += 1
            
        events_per_month_total = len(valid_events) / self.WINDOW_MONTHS
        active_months_count = len(month_counts)
        
        # Compute trend (slope of counts across the 18 months)
        events_per_month_trend = 0.0
        if active_months_count > 1:
            # Create array of 18 months up to as_of
            months = [(as_of - pd.DateOffset(months=i)).strftime("%Y-%m") for i in range(self.WINDOW_MONTHS)]
            months.reverse() # chronological
            counts = [month_counts[m] for m in months]
            
            x = np.arange(self.WINDOW_MONTHS)
            y = np.array(counts)
            if len(x) > 1:
                slope, _ = np.polyfit(x, y, 1)
                events_per_month_trend = float(slope)

        # ─── Signal Diversity ──────────────────────────────────────────────
        distinct_departments = len(set(e["department"] for e in valid_events))
        signal_diversity_ratio = distinct_departments / self.EXPECTED_DEPARTMENTS

        # ─── Renewal Compliance ────────────────────────────────────────────
        renewals = [e for e in valid_events if e["event_type"] == "RENEWAL"]
        days_since_last_renewal = float('nan')
        if renewals:
            latest_renewal = max(e["event_time"] for e in renewals)
            days_since_last_renewal = (as_of - latest_renewal).days
            
        # Simplified: expected 1 renewal per active department (that requires it) per year
        expected_renewals = int(self.WINDOW_MONTHS / 12) * distinct_departments 
        missed_renewals_count = max(0, expected_renewals - len(renewals))
        renewal_compliance_rate = len(renewals) / expected_renewals if expected_renewals > 0 else float('nan')

        # ─── Consumption (BESCOM) ──────────────────────────────────────────
        bescom_events = [e for e in valid_events if e["department"] == Department.BESCOM.value]
        bescom_avg_monthly_units = float('nan')
        bescom_zero_months_count = 0
        bescom_consecutive_zero_months = 0
        bescom_cv = float('nan')
        
        if bescom_events:
            # Sort chronologically for consecutive check
            bescom_events_chrono = sorted(bescom_events, key=lambda x: x["event_time"])
            units = [e["event_data"].get("units_consumed", 0) for e in bescom_events_chrono]
            
            bescom_avg_monthly_units = np.mean(units)
            bescom_zero_months_count = sum(1 for u in units if u == 0)
            
            if len(units) > 1 and np.mean(units) > 0:
                bescom_cv = np.std(units) / np.mean(units)
                
            # Consecutive zeroes at the end
            for u in reversed(units):
                if u == 0:
                    bescom_consecutive_zero_months += 1
                else:
                    break

        # ─── Inspection Outcomes ───────────────────────────────────────────
        inspections = [e for e in valid_events if e["event_type"] == "INSPECTION"]
        inspection_count = len(inspections)
        months_since_last_inspection = float('nan')
        compliance_failure_count = 0
        has_closure_order = 0
        
        if inspections:
            latest_insp = max(e["event_time"] for e in inspections)
            months_since_last_inspection = (as_of - latest_insp).days / 30.4
            
            for insp in inspections:
                if insp["event_data"].get("violations_found", 0) > 0:
                    compliance_failure_count += 1
                    
        closures = [e for e in valid_events if e["event_type"] == "CLOSURE_ORDER"]
        if closures:
            has_closure_order = 1

        # ─── Signatory Changes ─────────────────────────────────────────────
        signatory_change_count = len([e for e in valid_events if e["event_type"] == "SIGNATORY_CHANGE"])

        # ─── Derived Heuristic (Inactivity Score) ──────────────────────────
        # Composite score 0-1, higher = more inactive
        score = 0.0
        if math.isnan(days_since_last_event) or days_since_last_event > 365:
            score += 0.4
        if bescom_consecutive_zero_months > 3:
            score += 0.3
        if missed_renewals_count > 1:
            score += 0.2
        if has_closure_order == 1:
            score += 0.5
            
        inactivity_score = min(1.0, score)

        # Build feature dictionary
        features = {
            "days_since_last_event": days_since_last_event,
            "events_per_month_total": events_per_month_total,
            "events_per_month_trend": events_per_month_trend,
            "active_months_count": active_months_count,
            "distinct_departments_active": distinct_departments,
            "signal_diversity_ratio": signal_diversity_ratio,
            "missed_renewals_count": missed_renewals_count,
            "renewal_compliance_rate": renewal_compliance_rate,
            "days_since_last_renewal": days_since_last_renewal,
            "bescom_avg_monthly_units": bescom_avg_monthly_units,
            "bescom_zero_months_count": bescom_zero_months_count,
            "bescom_consecutive_zero_months": bescom_consecutive_zero_months,
            "bescom_cv": bescom_cv,
            "inspection_count": inspection_count,
            "months_since_last_inspection": months_since_last_inspection,
            "compliance_failure_count": compliance_failure_count,
            "has_closure_order": has_closure_order,
            "signatory_change_count": signatory_change_count,
            "inactivity_score": inactivity_score
        }
        
        # Flatten days since dept
        for dept in Department:
            features[f"days_since_last_{dept.value.lower()}_event"] = days_since_last_event_by_dept.get(dept.value, float('nan'))
            
        return features

    def compute_features_batch(self, ubid_events_map: Dict[str, List[Dict]], as_of: datetime) -> pd.DataFrame:
        """Batch computation for multiple UBIDs."""
        data = []
        for ubid, events in ubid_events_map.items():
            f_dict = self.compute_features(ubid, events, as_of)
            f_dict["ubid"] = ubid
            data.append(f_dict)
            
        df = pd.DataFrame(data)
        # Ensure 'ubid' is index
        if not df.empty:
            df.set_index('ubid', inplace=True)
        return df
