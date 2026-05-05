"""
Udyam Setu — Entity Resolution Training Pipeline
Full pipeline to bootstrap labels and train the XGBoost ER model from department records.
"""

import sys
import os
import asyncio
import numpy as np
from sklearn.metrics import precision_score, recall_score, f1_score
from sklearn.model_selection import train_test_split

# Add backend dir to sys path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'backend')))

from sqlalchemy import select
from app.database import async_session_factory
from app.models.department_record import DepartmentRecord
from app.services.normalisation import normalize_record
from app.services.entity_resolution.blocking import BlockingEngine
from app.services.entity_resolution.features import FeatureExtractor
from app.services.entity_resolution.model import EntityResolutionModel

async def load_records():
    """Load all department records from the database."""
    print("Loading department records from DB...")
    async with async_session_factory() as session:
        result = await session.execute(select(DepartmentRecord))
        records = result.scalars().all()
        # Convert ORM objects to dicts for processing
        return [{
            "id": str(r.id),
            "department": r.department.value,
            "business_name": r.business_name,
            "address_raw": r.address_raw,
            "address_pincode": r.address_pincode,
            "address_lat": r.address_lat,
            "address_lng": r.address_lng,
            "pan": r.pan,
            "gstin": r.gstin,
            "nic_code": r.nic_code,
            "registration_date": r.registration_date,
            "phone": r.phone,
            "email": r.email,
            "signatory_name": r.signatory_name
        } for r in records]

def run_pipeline():
    # 1. Load and normalize records
    loop = asyncio.get_event_loop()
    raw_records = loop.run_until_complete(load_records())
    
    if not raw_records:
        print("No records found in database. Please run scripts/seed_data.py first.")
        return
        
    print(f"Loaded {len(raw_records)} records. Normalizing...")
    normalized_records = [normalize_record(r) for r in raw_records]
    record_dict = {r["id"]: r for r in normalized_records}
    
    # 2. Run Blocking to get Candidate Pairs
    print("Running Blocking Engine to generate candidate pairs...")
    blocker = BlockingEngine()
    candidate_pairs = blocker.generate_candidate_pairs(normalized_records)
    print(f"Generated {len(candidate_pairs)} candidate pairs.")
    
    if not candidate_pairs:
        print("No candidate pairs generated. Aborting training.")
        return
        
    # 3. Extract Features
    print("Extracting features...")
    extractor = FeatureExtractor()
    features_list = []
    vectors_list = []
    
    for pair in candidate_pairs:
        r_a = record_dict[pair["record_a_id"]]
        r_b = record_dict[pair["record_b_id"]]
        signals = pair["blocking_signals"]
        
        feat_dict = extractor.extract_features(r_a, r_b, signals)
        vector = extractor.features_to_vector(feat_dict)
        
        features_list.append(feat_dict)
        vectors_list.append(vector)
        
    # 4. Bootstrap Labels
    print("Bootstrapping labels using rule-based heuristics...")
    model = EntityResolutionModel()
    labeled_X_dicts, labeled_y = model.bootstrap_labels(features_list)
    
    if not labeled_y:
        print("Heuristics yielded 0 labeled pairs. Cannot train.")
        return
        
    print(f"Bootstrapped {len(labeled_y)} labeled pairs (Positives: {sum(labeled_y)}, Negatives: {len(labeled_y) - sum(labeled_y)})")
    
    # Convert labeled dicts to vectors
    labeled_X = [extractor.features_to_vector(f) for f in labeled_X_dicts]
    
    # Split into train/test
    X_train, X_test, y_train, y_test = train_test_split(labeled_X, labeled_y, test_size=0.2, random_state=42)
    
    # 5. Train Model
    print("Training model...")
    model.train(X_train, y_train)
    
    # 6. Evaluate Model
    print("Evaluating model...")
    y_probs = model.predict_proba(X_test)
    
    print("\n--- Evaluation Metrics ---")
    thresholds = [0.5, 0.7, 0.85, 0.95]
    
    for t in thresholds:
        y_pred = [1 if p >= t else 0 for p in y_probs]
        p = precision_score(y_test, y_pred, zero_division=0)
        r = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        print(f"Threshold {t:.2f} -> Precision: {p:.2%}, Recall: {r:.2%}, F1: {f1:.2f}")
        
    # 7. Save Model
    model_path = os.path.join(os.path.dirname(__file__), 'saved_models', 'er_xgboost_calibrated.pkl')
    model.save(model_path)
    
    # Print reliability diagram data roughly
    print("\n--- Reliability Diagram Data ---")
    bins = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
    for i in range(len(bins)-1):
        bin_probs = [p for j, p in enumerate(y_probs) if bins[i] <= p < bins[i+1]]
        bin_y = [y_test[j] for j, p in enumerate(y_probs) if bins[i] <= p < bins[i+1]]
        if bin_probs:
            print(f"Bin [{bins[i]:.1f}-{bins[i+1]:.1f}): Mean Predicted = {np.mean(bin_probs):.3f}, True Fraction = {np.mean(bin_y):.3f} (n={len(bin_probs)})")
        
    p_85 = precision_score(y_test, [1 if p >= 0.85 else 0 for p in y_probs], zero_division=0)
    r_85 = recall_score(y_test, [1 if p >= 0.85 else 0 for p in y_probs], zero_division=0)
    print(f"\nModel trained. Precision@0.85: {p_85:.2%}, Recall@0.85: {r_85:.2%}")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    run_pipeline()
