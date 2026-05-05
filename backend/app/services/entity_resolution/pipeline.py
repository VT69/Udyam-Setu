"""
Udyam Setu — Entity Resolution Pipeline
End-to-end task executing blocking, feature extraction, scoring, and automated decision making.
"""

import asyncio
import os
import uuid
import logging
from sqlalchemy import select, and_

from app.celery_app import celery_app
from app.database import async_session_factory
from app.models.department_record import DepartmentRecord
from app.models.candidate_pair import CandidatePair
from app.models.ubid_registry import UbidRegistry
from app.models.enums import PairStatus, RegistryStatus
from app.services.normalisation import normalize_record
from app.services.entity_resolution.blocking import BlockingEngine
from app.services.entity_resolution.features import FeatureExtractor
from app.services.entity_resolution.model import EntityResolutionModel
from app.services.entity_resolution.decision_engine import DecisionEngine
import networkx as nx

logger = logging.getLogger(__name__)

def resolve_golden_records(scored_pairs: list[dict]) -> list[list[str]]:
    """
    Uses graph theory for transitive closures.
    If Record A matches Record B (score > 0.92), and Record B matches Record C (score > 0.92),
    then A matches C implicitly.
    """
    # Filter only high-confidence pairs
    filtered_pairs = [p for p in scored_pairs if p.get("score", 0) > 0.92]
    
    G = nx.Graph()
    for pair in filtered_pairs:
        G.add_edge(pair["record_a_id"], pair["record_b_id"])
        
    if len(G.nodes) == 0:
        return []
        
    # Find all connected clusters
    clusters = list(nx.connected_components(G))
    return [list(c) for c in clusters]

async def _run_pipeline_async():
    logger.info("Starting Entity Resolution Pipeline...")
    
    # 1. Fetch all department records
    async with async_session_factory() as session:
        result = await session.execute(select(DepartmentRecord))
        records = result.scalars().all()
        
        # Convert to dicts for processing
        raw_records = []
        for r in records:
            raw_records.append({
                "id": str(r.id),
                "department": r.department.value,
                "business_name": r.business_name,
                "address_raw": r.address_raw,
                "address_pincode": r.address_pincode,
                "address_locality": r.address_locality,
                "address_district": r.address_district,
                "address_lat": r.address_lat,
                "address_lng": r.address_lng,
                "pan": r.pan,
                "gstin": r.gstin,
                "nic_code": r.nic_code,
                "registration_date": r.registration_date,
                "phone": r.phone,
                "email": r.email,
                "signatory_name": r.signatory_name,
                "ubid": r.ubid
            })

    if not raw_records:
        return {"status": "No records to process"}

    # Normalize records
    logger.info(f"Normalizing {len(raw_records)} records...")
    normalized_records = [normalize_record(r) for r in raw_records]
    record_dict = {r["id"]: r for r in normalized_records}

    # 2. Run blocking
    logger.info("Running blocking engine...")
    blocker = BlockingEngine()
    candidate_pairs = blocker.generate_candidate_pairs(normalized_records)

    if not candidate_pairs:
        return {"status": "No candidate pairs generated"}

    # 3. Load Model and Initialize Engines
    model_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'ml', 'entity_resolution', 'saved_models', 'er_xgboost_calibrated.pkl')
    
    # Allow pipeline to run gracefully even if model isn't trained yet
    try:
        model = EntityResolutionModel(model_path)
    except Exception as e:
        logger.error(f"Failed to load model: {e}. Cannot score pairs.")
        return {"status": "Model missing or error", "error": str(e)}
        
    extractor = FeatureExtractor()
    decision_engine = DecisionEngine()

    scored_pairs = []
    
    # Score pairs and apply decision engine
    logger.info("Extracting features and scoring pairs...")
    for pair in candidate_pairs:
        r_a = record_dict[pair["record_a_id"]]
        r_b = record_dict[pair["record_b_id"]]
        signals = pair["blocking_signals"]
        
        features = extractor.extract_features(r_a, r_b, signals)
        vector = extractor.features_to_vector(features)
        
        # Get score and shap explanation
        explanation = model.predict_with_shap(vector, extractor.FEATURE_NAMES)
        score = explanation["score"]
        
        decision = decision_engine.decide(pair, score, features)
        
        scored_pairs.append({
            "record_a": r_a,
            "record_b": r_b,
            "record_a_id": pair["record_a_id"],
            "record_b_id": pair["record_b_id"],
            "score": score,
            "shap_values": explanation["shap_values"],
            "feature_vector": features,
            "blocking_signals": signals,
            "decision": decision
        })

    summary = decision_engine.process_batch(scored_pairs)
    logger.info(f"Pipeline Decisions: {summary}")

    # 4 & 5. Database updates for AUTO_LINK and QUEUE_REVIEW
    async with async_session_factory() as session:
        # Pre-fetch all relevant ORM records to update them
        # (For huge datasets, we'd batch this. Doing it in one go for the demo)
        record_ids = [p["record_a_id"] for p in scored_pairs] + [p["record_b_id"] for p in scored_pairs]
        db_records_res = await session.execute(select(DepartmentRecord).where(DepartmentRecord.id.in_(record_ids)))
        db_records = {str(r.id): r for r in db_records_res.scalars().all()}
        
        for sp in scored_pairs:
            r_a_id = sp["record_a_id"]
            r_b_id = sp["record_b_id"]
            decision = sp["decision"]["action"]
            
            db_r_a = db_records.get(r_a_id)
            db_r_b = db_records.get(r_b_id)
            
            if not db_r_a or not db_r_b:
                continue

            if decision == "AUTO_LINK":
                # Create or fetch UBID
                target_ubid = db_r_a.ubid or db_r_b.ubid
                if not target_ubid:
                    target_ubid = decision_engine.assign_ubid(
                        [sp["record_a"], sp["record_b"]], 
                        pan=sp["record_a"].get("pan") or sp["record_b"].get("pan"),
                        gstin=sp["record_a"].get("gstin") or sp["record_b"].get("gstin")
                    )
                    # Create new registry entry
                    new_registry = UbidRegistry(
                        ubid=target_ubid,
                        pan_anchor=sp["record_a"].get("pan") or sp["record_b"].get("pan"),
                        gstin_anchor=sp["record_a"].get("gstin") or sp["record_b"].get("gstin"),
                        status=RegistryStatus.ACTIVE,
                        status_confidence=sp["score"]
                    )
                    session.add(new_registry)
                
                # Update records
                db_r_a.ubid = target_ubid
                db_r_b.ubid = target_ubid
                
                # Insert AUTO_LINKED candidate pair
                cp = CandidatePair(
                    record_a_id=db_r_a.id,
                    record_b_id=db_r_b.id,
                    score=sp["score"],
                    blocking_signals=sp["blocking_signals"],
                    shap_values=sp["shap_values"],
                    feature_vector=sp["feature_vector"],
                    status=PairStatus.AUTO_LINKED
                )
                session.add(cp)
                
            elif decision == "QUEUE_REVIEW":
                # Insert PENDING_REVIEW candidate pair
                cp = CandidatePair(
                    record_a_id=db_r_a.id,
                    record_b_id=db_r_b.id,
                    score=sp["score"],
                    blocking_signals=sp["blocking_signals"],
                    shap_values=sp["shap_values"],
                    feature_vector=sp["feature_vector"],
                    status=PairStatus.PENDING_REVIEW
                )
                session.add(cp)
                
        await session.commit()
        
    return {"status": "success", "summary": summary}


@celery_app.task(bind=True, max_retries=1)
def run_entity_resolution_pipeline(self):
    """Celery wrapper for the async pipeline."""
    # Handle event loop for async sqlalchemy calls
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    result = loop.run_until_complete(_run_pipeline_async())
    return result
