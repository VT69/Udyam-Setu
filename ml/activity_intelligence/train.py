"""
Udyam Setu — Activity Intelligence Training Script
Trains the LightGBM classifier on the rolling 18-month event features.
"""

import os
import sys
import asyncio
from datetime import datetime
import pandas as pd
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# Add backend dir to sys path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'backend')))

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import async_session_factory
from app.models.ubid_registry import UbidRegistry
from app.models.business_event import BusinessEvent

from app.services.activity.feature_engineer import ActivityFeatureEngineer
from app.services.activity.classifier import ActivityClassifier

async def load_data():
    """Load UBID ground truth and events."""
    print("Loading Ground Truth from UbidRegistry...")
    async with async_session_factory() as session:
        ubid_res = await session.execute(select(UbidRegistry))
        registries = ubid_res.scalars().all()
        
        ubid_status_map = {r.ubid: r.status.value for r in registries if r.status.value in ["ACTIVE", "DORMANT", "CLOSED"]}
        
        print(f"Loaded {len(ubid_status_map)} valid UBIDs.")
        
        print("Loading events...")
        event_res = await session.execute(select(BusinessEvent).where(BusinessEvent.ubid.in_(ubid_status_map.keys())))
        events = event_res.scalars().all()
        
        ubid_events_map = {ubid: [] for ubid in ubid_status_map.keys()}
        for e in events:
            if e.ubid in ubid_events_map:
                ubid_events_map[e.ubid].append({
                    "event_time": e.event_time,
                    "department": e.department.value,
                    "event_type": e.event_type,
                    "event_data": e.event_data
                })
                
        return ubid_status_map, ubid_events_map

def run_training():
    loop = asyncio.get_event_loop()
    ubid_status_map, ubid_events_map = loop.run_until_complete(load_data())
    
    if not ubid_status_map:
        print("No data to train on. Run seed script.")
        return
        
    print("Computing 18-month rolling features...")
    engineer = ActivityFeatureEngineer()
    # Assuming "now" is the time of the latest event overall for realistic synthetic data processing
    all_times = [e["event_time"] for events in ubid_events_map.values() for e in events]
    as_of = max(all_times) if all_times else datetime.utcnow()
    
    features_df = engineer.compute_features_batch(ubid_events_map, as_of)
    print(f"Generated features for {len(features_df)} entities.")
    
    classifier = ActivityClassifier()
    X, y = classifier.bootstrap_labels_from_ground_truth(ubid_status_map, features_df)
    
    if len(X) < 10:
        print("Not enough data to train (need at least 10 samples).")
        return
        
    # Keep feature names for saving
    feature_names = list(X.columns)
    
    # Temporal Train/Test split (no shuffling to prevent look-ahead bias)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
    
    print("Training LightGBM Multiclass Model...")
    model = lgb.LGBMClassifier(
        n_estimators=200,
        max_depth=4,
        num_leaves=31,
        objective='multiclass',
        num_class=3,
        random_state=42,
        verbosity=-1
    )
    
    model.fit(X_train, y_train)
    
    print("\n--- Evaluating Model ---")
    y_pred = model.predict(X_test)
    
    target_names = [classifier.CLASS_MAPPING[i] for i in range(3)]
    report = classification_report(y_test, y_pred, target_names=target_names, zero_division=0)
    print(report)
    
    print("\nSaving model...")
    classifier.model = model
    classifier.feature_names = feature_names
    
    save_path = os.path.join(os.path.dirname(__file__), 'model.pkl')
    classifier.save(save_path)
    print(f"Model successfully saved to {save_path}")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    run_training()
