"""
Udyam Setu — Entity Resolution API Router
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from celery.result import AsyncResult

from app.database import get_db
from app.celery_app import celery_app
from app.schemas.er_schemas import (
    TaskResponse, TaskStatusResponse, ERStatsResponse, 
    ReviewDecisionRequest, ReviewDecisionResponse, 
    ReviewQueueResponse, CandidatePairReviewDetail,
    UBIDRecordDetail, UBIDLookupResponse, UBIDLookupResponseItem
)
from app.models.department_record import DepartmentRecord
from app.models.candidate_pair import CandidatePair
from app.models.ubid_registry import UbidRegistry
from app.models.review_decision import ReviewDecision
from app.models.enums import PairStatus, RegistryStatus, Decision
from app.services.entity_resolution.pipeline import run_entity_resolution_pipeline
from app.services.entity_resolution.decision_engine import DecisionEngine

router = APIRouter()

# ─── Pipeline Triggers ───────────────────────────────────────────────────

@router.post("/run-pipeline", response_model=TaskResponse)
async def trigger_pipeline():
    """Trigger the async entity resolution pipeline via Celery."""
    task = run_entity_resolution_pipeline.delay()
    return {"task_id": task.id, "status": "started"}

@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """Check the status of a Celery task."""
    task_result = AsyncResult(task_id, app=celery_app)
    
    response = {
        "task_id": task_id,
        "status": task_result.status,
    }
    
    if task_result.ready():
        if task_result.successful():
            response["result"] = task_result.result
        else:
            response["result"] = {"error": str(task_result.result)}
            
    return response

# ─── Statistics ──────────────────────────────────────────────────────────

@router.get("/stats", response_model=ERStatsResponse)
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Fetch macro statistics for the Entity Resolution engine."""
    
    total_records = await db.scalar(select(func.count(DepartmentRecord.id)))
    total_ubids = await db.scalar(select(func.count(UbidRegistry.ubid)))
    
    auto_linked = await db.scalar(select(func.count(CandidatePair.id)).where(CandidatePair.status == PairStatus.AUTO_LINKED))
    pending_review = await db.scalar(select(func.count(CandidatePair.id)).where(CandidatePair.status == PairStatus.PENDING_REVIEW))
    rejected = await db.scalar(select(func.count(CandidatePair.id)).where(CandidatePair.status == PairStatus.REJECTED))
    
    records_without_ubid = await db.scalar(select(func.count(DepartmentRecord.id)).where(DepartmentRecord.ubid == None))
    
    anchor_grade_ubids = await db.scalar(select(func.count(UbidRegistry.ubid)).where(or_(UbidRegistry.pan_anchor != None, UbidRegistry.gstin_anchor != None)))
    anchor_pending_ubids = await db.scalar(select(func.count(UbidRegistry.ubid)).where(and_(UbidRegistry.pan_anchor == None, UbidRegistry.gstin_anchor == None)))
    
    return {
        "total_records": total_records or 0,
        "total_ubids": total_ubids or 0,
        "auto_linked_pairs": auto_linked or 0,
        "pending_review": pending_review or 0,
        "rejected_pairs": rejected or 0,
        "records_without_ubid": records_without_ubid or 0,
        "anchor_grade_ubids": anchor_grade_ubids or 0,
        "anchor_pending_ubids": anchor_pending_ubids or 0
    }

# ─── Human in the Loop (Review Queue) ────────────────────────────────────

@router.get("/review-queue", response_model=ReviewQueueResponse)
async def get_review_queue(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Fetch paginated candidate pairs awaiting human review."""
    skip = (page - 1) * limit
    
    stmt = (
        select(CandidatePair)
        .where(CandidatePair.status == PairStatus.PENDING_REVIEW)
        .options(selectinload(CandidatePair.record_a), selectinload(CandidatePair.record_b))
        .order_by(CandidatePair.score.desc()) # Highest scores first
        .offset(skip)
        .limit(limit)
    )
    
    result = await db.execute(stmt)
    pairs = result.scalars().all()
    
    total = await db.scalar(select(func.count(CandidatePair.id)).where(CandidatePair.status == PairStatus.PENDING_REVIEW))
    
    items = []
    for p in pairs:
        items.append({
            "pair_id": p.id,
            "score": p.score,
            "record_a": {c.name: getattr(p.record_a, c.name) for c in p.record_a.__table__.columns},
            "record_b": {c.name: getattr(p.record_b, c.name) for c in p.record_b.__table__.columns},
            "shap_values": p.shap_values,
            "blocking_signals": p.blocking_signals,
            "feature_vector": p.feature_vector,
            "status": p.status.value
        })
        
    return {"items": items, "total": total, "page": page, "limit": limit}

@router.post("/review/{pair_id}", response_model=ReviewDecisionResponse)
async def submit_review(
    pair_id: UUID,
    payload: ReviewDecisionRequest,
    db: AsyncSession = Depends(get_db)
):
    """Submit a human decision for a candidate pair."""
    stmt = select(CandidatePair).where(CandidatePair.id == pair_id).options(
        selectinload(CandidatePair.record_a), 
        selectinload(CandidatePair.record_b)
    )
    result = await db.execute(stmt)
    pair = result.scalars().first()
    
    if not pair:
        raise HTTPException(status_code=404, detail="Candidate pair not found")
        
    if pair.status != PairStatus.PENDING_REVIEW:
        raise HTTPException(status_code=400, detail="Pair is not pending review")
        
    decision_enum = Decision[payload.decision]
    
    # 1. Record decision
    review_dec = ReviewDecision(
        pair_id=pair.id,
        reviewer_id=payload.reviewer_id,
        decision=decision_enum,
        reason=payload.reason,
        score_at_decision=pair.score
    )
    db.add(review_dec)
    
    engine = DecisionEngine()
    ubid_assigned = None
    
    # 2. Apply logic
    if decision_enum == Decision.MERGE:
        pair.status = PairStatus.MERGED
        
        target_ubid = pair.record_a.ubid or pair.record_b.ubid
        if not target_ubid:
            target_ubid = engine.assign_ubid(
                [pair.record_a.__dict__, pair.record_b.__dict__],
                pan=pair.record_a.pan or pair.record_b.pan,
                gstin=pair.record_a.gstin or pair.record_b.gstin
            )
            # Register UBID
            new_registry = UbidRegistry(
                ubid=target_ubid,
                pan_anchor=pair.record_a.pan or pair.record_b.pan,
                status=RegistryStatus.ACTIVE,
                status_confidence=1.0 # 100% human confidence
            )
            db.add(new_registry)
            
        pair.record_a.ubid = target_ubid
        pair.record_b.ubid = target_ubid
        ubid_assigned = target_ubid
        
    elif decision_enum == Decision.KEEP_SEPARATE:
        pair.status = PairStatus.KEPT_SEPARATE
        
    elif decision_enum == Decision.ESCALATE:
        pair.status = PairStatus.ESCALATED
        
    await db.commit()
    return {"success": True, "ubid_assigned": ubid_assigned}

# ─── UBID Queries ────────────────────────────────────────────────────────

@router.get("/ubid/{ubid}", response_model=UBIDRecordDetail)
async def get_ubid(ubid: str, db: AsyncSession = Depends(get_db)):
    """Fetch full details of a UBID including all linked department records."""
    stmt = select(UbidRegistry).where(UbidRegistry.ubid == ubid).options(selectinload(UbidRegistry.department_records))
    result = await db.execute(stmt)
    registry = result.scalars().first()
    
    if not registry:
        raise HTTPException(status_code=404, detail="UBID not found")
        
    linked = []
    for r in registry.department_records:
        linked.append({c.name: getattr(r, c.name) for c in r.__table__.columns})
        
    return {
        "ubid": registry.ubid,
        "pan_anchor": registry.pan_anchor,
        "gstin_anchor": registry.gstin_anchor,
        "status": registry.status.value,
        "status_confidence": registry.status_confidence,
        "linked_records": linked
    }

@router.get("/ubid/lookup", response_model=UBIDLookupResponse)
async def lookup_ubid(
    pan: Optional[str] = None,
    gstin: Optional[str] = None,
    name: Optional[str] = None,
    pincode: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Lookup UBIDs matching given identifiers or attributes."""
    if not any([pan, gstin, name, pincode]):
        raise HTTPException(status_code=400, detail="Provide at least one search parameter")
        
    query = select(UbidRegistry).join(UbidRegistry.department_records)
    
    filters = []
    if pan:
        filters.append(UbidRegistry.pan_anchor == pan)
        filters.append(DepartmentRecord.pan == pan)
    if gstin:
        filters.append(UbidRegistry.gstin_anchor == gstin)
        filters.append(DepartmentRecord.gstin == gstin)
    if name:
        filters.append(DepartmentRecord.business_name.ilike(f"%{name}%"))
    if pincode:
        filters.append(DepartmentRecord.address_pincode == pincode)
        
    if filters:
        query = query.where(or_(*filters))
        
    query = query.distinct()
    result = await db.execute(query)
    registries = result.scalars().all()
    
    matches = []
    for reg in registries:
        matches.append({
            "ubid": reg.ubid,
            "confidence": reg.status_confidence or 0.0,
            "evidence": f"Matched via search parameters"
        })
        
    return {"matches": matches}
