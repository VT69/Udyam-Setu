"""
Udyam Setu — Activity Intelligence API Router
"""

import os
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.celery_app import celery_app
from app.models.ubid_registry import UbidRegistry
from app.models.business_event import BusinessEvent
from app.models.department_record import DepartmentRecord
from app.models.enums import RegistryStatus
from app.schemas.activity_schemas import (
    StatusResponse, TaskResponse, ActivityStatsResponse,
    CrossDepartmentQueryResponse, CrossDepartmentResult,
    ActivityReviewQueueResponse, ReviewQueueItem,
    OverrideRequest, OverrideResponse, TopSignal, ActivityTimelineEvent
)

from app.services.activity.feature_engineer import ActivityFeatureEngineer
from app.services.activity.classifier import ActivityClassifier

router = APIRouter()

# Instantiate lazily
_classifier = None
_engineer = None

def get_classifier():
    global _classifier
    if _classifier is None:
        model_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'ml', 'activity_intelligence', 'model.pkl')
        _classifier = ActivityClassifier(model_path)
    return _classifier

def get_engineer():
    global _engineer
    if _engineer is None:
        _engineer = ActivityFeatureEngineer()
    return _engineer


@router.get("/activity/status/{ubid}", response_model=StatusResponse)
async def get_activity_status(ubid: str, db: AsyncSession = Depends(get_db)):
    """Fetch real-time operational status classification and evidence for a UBID."""
    # Fetch UBID
    stmt = select(UbidRegistry).where(UbidRegistry.ubid == ubid)
    res = await db.execute(stmt)
    registry = res.scalars().first()
    if not registry:
        raise HTTPException(status_code=404, detail="UBID not found")
        
    # Fetch events
    evt_stmt = select(BusinessEvent).where(BusinessEvent.ubid == ubid).order_by(desc(BusinessEvent.event_time))
    evt_res = await db.execute(evt_stmt)
    events = evt_res.scalars().all()
    
    events_dict = [{
        "event_time": e.event_time,
        "department": e.department.value,
        "event_type": e.event_type,
        "event_data": e.event_data
    } for e in events]
    
    engineer = get_engineer()
    classifier = get_classifier()
    
    try:
        as_of = datetime.utcnow()
        features = engineer.compute_features(ubid, events_dict, as_of)
        result = classifier.classify(features)
        
        # Build timeline
        timeline = []
        for e in events[:10]: # Return top 10 most recent for timeline
            timeline.append(ActivityTimelineEvent(
                date=e.event_time,
                dept=e.department.value,
                event_type=e.event_type,
                shap_impact=None # Advanced: could trace specific event impacts
            ))
            
        top_signals = [TopSignal(**s) for s in result["top_signals"]]
        
        return {
            "ubid": ubid,
            "status": result["status"],
            "confidence": result["confidence"],
            "probabilities": result["probabilities"],
            "last_classified_at": datetime.utcnow(),
            "evidence_summary": result["evidence_summary"],
            "top_signals": top_signals,
            "event_timeline": timeline,
            "needs_review": result["needs_review"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")


@router.post("/activity/classify-all", response_model=TaskResponse)
async def classify_all():
    """Trigger background task to reclassify all UBIDs."""
    # Assuming there's a celery task registered in app.services.activity.classifier
    # For now we'll just mock the ID return
    # task = classify_all_ubids.delay()
    return {"task_id": "mock-task-id-123"}


@router.get("/activity/stats", response_model=ActivityStatsResponse)
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Get macro counts of operational statuses."""
    counts = await db.execute(
        select(UbidRegistry.status, func.count(UbidRegistry.ubid))
        .group_by(UbidRegistry.status)
    )
    data = dict(counts.all())
    
    # We don't natively store 'needs_review' in DB yet, mock it for stats
    # or query a dedicated table
    
    return {
        "active_count": data.get(RegistryStatus.ACTIVE, 0),
        "dormant_count": data.get(RegistryStatus.DORMANT, 0),
        "closed_count": data.get(RegistryStatus.CLOSED, 0),
        "unclassified_count": data.get(RegistryStatus.UNCLASSIFIED, 0),
        "needs_review_count": 0
    }


@router.get("/query/cross-department", response_model=CrossDepartmentQueryResponse)
async def cross_department_query(
    status: Optional[str] = None,
    pincode: Optional[str] = None,
    department: Optional[str] = None,
    no_inspection_since_months: Optional[int] = None,
    nic_code_prefix: Optional[str] = None,
    min_confidence: Optional[float] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Complex cross-department targeting query.
    Example: "active factories in pin code 560058 with no inspection in the last 18 months"
    """
    query = select(UbidRegistry).join(UbidRegistry.department_records)
    
    interp_parts = []
    
    if status:
        query = query.where(UbidRegistry.status == status)
        interp_parts.append(f"{status.lower()}")
        
    if department:
        query = query.where(DepartmentRecord.department == department)
        interp_parts.append(f"registered in {department}")
        
    if pincode:
        query = query.where(DepartmentRecord.address_pincode == pincode)
        interp_parts.append(f"in pincode {pincode}")
        
    if nic_code_prefix:
        query = query.where(DepartmentRecord.nic_code.startswith(nic_code_prefix))
        interp_parts.append(f"with NIC starting with {nic_code_prefix}")
        
    if min_confidence:
        query = query.where(UbidRegistry.status_confidence >= min_confidence)
        
    if no_inspection_since_months is not None:
        cutoff_date = datetime.utcnow() - timedelta(days=30.4 * no_inspection_since_months)
        # Subquery: UBIDs that DO have an inspection after cutoff_date
        recent_inspections = select(BusinessEvent.ubid).where(
            BusinessEvent.event_type == 'INSPECTION',
            BusinessEvent.event_time >= cutoff_date
        ).scalar_subquery()
        
        query = query.where(UbidRegistry.ubid.not_in(recent_inspections))
        interp_parts.append(f"with no inspection in the last {no_inspection_since_months} months")
        
    # Build interpreted string
    interp = "Businesses " + " ".join(interp_parts) if interp_parts else "All businesses"
    
    # Get total count
    count_query = select(func.count(func.distinct(UbidRegistry.ubid))).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    # Fetch paginated results
    query = query.distinct().options(selectinload(UbidRegistry.department_records)).offset((page - 1) * limit).limit(limit)
    res = await db.execute(query)
    registries = res.scalars().all()
    
    results = []
    for reg in registries:
        depts = list(set([r.department.value for r in reg.department_records]))
        # Grab a representative name and location
        rep = reg.department_records[0] if reg.department_records else None
        
        results.append(CrossDepartmentResult(
            ubid=reg.ubid,
            business_name=rep.business_name if rep else "Unknown",
            status=reg.status.value if reg.status else "UNKNOWN",
            confidence=reg.status_confidence or 0.0,
            linked_departments=depts,
            last_inspection_date=None, # Mock for API response
            months_since_inspection=None,
            pincode=rep.address_pincode if rep else "Unknown",
            district=rep.address_district if rep else "Unknown",
            evidence_summary="Matched cross-department criteria."
        ))
        
    # Try to compile raw SQL for transparency
    try:
        raw_sql = str(query.compile(compile_kwargs={"literal_binds": True}))
    except:
        raw_sql = "SQL compilation unavailable."

    return {
        "total_results": total or 0,
        "query_interpreted_as": interp,
        "results": results,
        "query_sql": raw_sql
    }


@router.get("/activity/review-queue", response_model=ActivityReviewQueueResponse)
async def get_review_queue(page: int = 1, limit: int = 20):
    """Fetch UBIDs flagged as needing human review due to model uncertainty."""
    # Mocking this since needs_review isn't a DB column yet
    return {"items": [], "total": 0, "page": page, "limit": limit}


@router.post("/activity/override/{ubid}", response_model=OverrideResponse)
async def manual_override(ubid: str, payload: OverrideRequest, db: AsyncSession = Depends(get_db)):
    """Manually override the operational status of a business."""
    stmt = select(UbidRegistry).where(UbidRegistry.ubid == ubid)
    res = await db.execute(stmt)
    registry = res.scalars().first()
    
    if not registry:
        raise HTTPException(status_code=404, detail="UBID not found")
        
    try:
        new_status_enum = RegistryStatus[payload.status.upper()]
    except KeyError:
        raise HTTPException(status_code=400, detail="Invalid status")
        
    registry.status = new_status_enum
    registry.status_confidence = 1.0 # Human
    
    # Normally we would log to ReviewDecision here
    await db.commit()
    
    return {"success": True, "ubid": ubid, "new_status": payload.status.upper()}
