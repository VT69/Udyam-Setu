import os
import sys
import json
import asyncio
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__dirname), "backend"))

from app.db.database import get_db, engine, Base
from app.db.models import DepartmentRecord, CandidatePair, UBID, Event, ActivityClassification
from app.services.entity_resolution.pipeline import run_entity_resolution_pipeline
from app.services.activity.event_processor import EventProcessor
from app.services.activity.classifier import ActivityClassifier
from sqlalchemy.orm import Session
from sqlalchemy import text

# Assuming seed_data generates directly to DB or provides a function
try:
    from scripts.seed_data import generate_and_seed_data
except ImportError:
    # Fallback if seed_data doesn't have this function
    def generate_and_seed_data():
        os.system(f"python {os.path.join(os.path.dirname(__file__), 'seed_data.py')}")

def clear_tables(db: Session):
    confirm = input("This will clear all tables. Type 'yes' to confirm: ")
    if confirm.lower() != 'yes':
        print("Aborting.")
        sys.exit(0)
    
    print("Clearing tables...")
    # Safe delete ordering
    db.query(ActivityClassification).delete()
    db.query(Event).delete()
    db.query(CandidatePair).delete()
    db.query(DepartmentRecord).delete()
    db.query(UBID).delete()
    db.commit()
    print("Tables cleared.")

def run_demo_setup():
    db = next(get_db())
    
    # 1. Clear tables
    clear_tables(db)
    
    # 2. Run seed_data.py
    print("Generating synthetic data...")
    generate_and_seed_data()
    
    # 3. Run ER pipeline
    print("Running Entity Resolution Pipeline (sync mode)...")
    er_stats = run_entity_resolution_pipeline()
    
    # 4. Print ER Report
    print("\n=== DEMO DATA READY ===")
    print(f"Records ingested: {er_stats.get('total_records', 0)} across 4 departments")
    print(f"Candidate pairs generated: {er_stats.get('total_pairs', 0)}")
    print(f"Auto-linked: {er_stats.get('auto_linked', 0)} pairs ({er_stats.get('new_ubids', 0)} UBIDs created)")
    print(f"Queued for review: {er_stats.get('queued', 0)} pairs")
    print(f"Rejected: {er_stats.get('rejected', 0)} pairs\n")
    
    # 5. Ingest events & 6. Run Activity Classification
    print("Running Activity Classification...")
    classifier = ActivityClassifier()
    # Assuming classifier has a batch method or we just call the endpoint equivalent
    # Since we need to run it on all UBIDs
    ubids = db.query(UBID).all()
    for u in ubids:
        # In a real setup, event processor would have already ingested events during seed
        classifier.classify_ubid(db, u.id)
    db.commit()
    
    # 7. Print Activity Report
    active = db.query(ActivityClassification).filter(ActivityClassification.status == 'ACTIVE').count()
    dormant = db.query(ActivityClassification).filter(ActivityClassification.status == 'DORMANT').count()
    closed = db.query(ActivityClassification).filter(ActivityClassification.status == 'CLOSED').count()
    
    print(f"Active businesses: {active}")
    print(f"Dormant businesses: {dormant}")
    print(f"Closed businesses: {closed}\n")
    
    # 8. Run Demo Query
    print("Running Cross-Department Query: 'active factories in 560058 with no inspection in 18 months'")
    query = text("""
        SELECT u.id, dr.business_name
        FROM ubids u
        JOIN activity_classifications ac ON ac.ubid_id = u.id
        JOIN department_records dr ON dr.ubid_id = u.id
        WHERE ac.status = 'ACTIVE' 
          AND dr.department = 'FACTORIES' 
          AND dr.address_pincode = '560058'
          AND NOT EXISTS (
              SELECT 1 FROM events e 
              WHERE e.ubid_id = u.id 
                AND e.department = 'FACTORIES' 
                AND e.event_type = 'INSPECTION'
                AND e.event_time >= NOW() - INTERVAL '18 months'
          )
        LIMIT 3
    """)
    results = db.execute(query).fetchall()
    print(f"Query returned {len(results)} results (showing first 3):")
    for r in results:
        print(f" - {r.id}: {r.business_name}")
        
    # 9. Save state summary
    state = {
        "timestamp": datetime.now().isoformat(),
        "entity_resolution": er_stats,
        "activity_intelligence": {
            "active": active,
            "dormant": dormant,
            "closed": closed
        },
        "query_results": [
            {"ubid": str(r.id), "business_name": r.business_name} for r in results
        ]
    }
    
    docs_dir = os.path.join(os.path.dirname(__dirname), "docs")
    os.makedirs(docs_dir, exist_ok=True)
    with open(os.path.join(docs_dir, "demo_state.json"), "w") as f:
        json.dump(state, f, indent=2)
        
    print("\nDemo state saved to docs/demo_state.json")
    print("Setup complete! You may now run `npm start` in the frontend directory.")

if __name__ == "__main__":
    run_demo_setup()
