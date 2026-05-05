"""
Udyam Setu — Events API Router
"""

from typing import Dict, Any, List
from uuid import UUID
from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.business_event import BusinessEvent
from app.models.enums import AttributionStatus
from app.services.activity.event_processor import EventProcessor
from app.schemas.event_schemas import (
    EventIngestRequest, EventIngestResponse,
    EventBatchIngestRequest, EventBatchIngestResponse,
    AttributionQueueResponse, AttributionQueueItem,
    AttributeEventRequest, TimelineResponse, TimelineEvent
)

router = APIRouter()

# ─── Ingestion ────────────────────────────────────────────────────────────

@router.post("/ingest", response_model=EventIngestResponse)
async def ingest_event(
    payload: EventIngestRequest,
    db: AsyncSession = Depends(get_db)
):
    """Ingest a single event and attempt initial attribution."""
    processor = EventProcessor(db)
    result = await processor.ingest_event(payload)
    await db.commit()
    return result

@router.post("/ingest-batch", response_model=EventBatchIngestResponse)
async def ingest_batch(
    payload: EventBatchIngestRequest,
    db: AsyncSession = Depends(get_db)
):
    """Batch ingest multiple events."""
    processor = EventProcessor(db)
    
    attributed = 0
    pending = 0
    unattributable = 0
    
    for event_payload in payload.events:
        res = await processor.ingest_event(event_payload)
        status = res["attribution_status"]
        if status == AttributionStatus.ATTRIBUTED.value:
            attributed += 1
        elif status == AttributionStatus.PENDING_REVIEW.value:
            pending += 1
        else:
            unattributable += 1
            
    await db.commit()
    
    return {
        "attributed": attributed,
        "pending": pending,
        "unattributable": unattributable
    }

# ─── Attribution Human-in-the-Loop ────────────────────────────────────────

@router.get("/attribution-queue", response_model=AttributionQueueResponse)
async def get_attribution_queue(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Fetch paginated events pending human attribution."""
    skip = (page - 1) * limit
    
    stmt = (
        select(BusinessEvent)
        .where(BusinessEvent.attribution_status == AttributionStatus.PENDING_REVIEW)
        .order_by(BusinessEvent.event_time.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    events = result.scalars().all()
    
    total = await db.scalar(select(func.count(BusinessEvent.id)).where(BusinessEvent.attribution_status == AttributionStatus.PENDING_REVIEW))
    
    items = []
    for evt in events:
        # In a full implementation, we'd query the best candidates here dynamically
        # For the demo API schema compliance, returning empty candidates list.
        items.append(AttributionQueueItem(
            event_id=evt.id,
            event_time=evt.event_time,
            department=evt.department.value,
            original_record_id=evt.original_record_id,
            event_type=evt.event_type,
            event_data=evt.event_data,
            candidate_ubids=[] 
        ))
        
    return {"items": items, "total": total or 0, "page": page, "limit": limit}

@router.post("/attribute/{event_id}")
async def attribute_event(
    event_id: UUID,
    payload: AttributeEventRequest,
    db: AsyncSession = Depends(get_db)
):
    """Manually attribute an event to a UBID."""
    stmt = select(BusinessEvent).where(BusinessEvent.id == event_id)
    result = await db.execute(stmt)
    event = result.scalars().first()
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    event.ubid = payload.ubid
    event.attribution_status = AttributionStatus.ATTRIBUTED
    event.attribution_confidence = 1.0 # Human confirmed
    
    await db.commit()
    return {"success": True, "event_id": event_id, "ubid": payload.ubid}

# ─── Timeline ─────────────────────────────────────────────────────────────

@router.get("/timeline/{ubid}", response_model=TimelineResponse)
async def get_timeline(ubid: str, db: AsyncSession = Depends(get_db)):
    """Fetch all events for a UBID grouped by department and event_type."""
    
    stmt = (
        select(BusinessEvent)
        .where(BusinessEvent.ubid == ubid)
        .order_by(desc(BusinessEvent.event_time))
    )
    result = await db.execute(stmt)
    events = result.scalars().all()
    
    # Grouping structure: {department: {event_type: [events]}}
    grouped = defaultdict(lambda: defaultdict(list))
    
    for evt in events:
        dept_str = evt.department.value
        type_str = evt.event_type
        grouped[dept_str][type_str].append(TimelineEvent(
            event_id=evt.id,
            event_time=evt.event_time,
            event_type=evt.event_type,
            event_data=evt.event_data,
            attribution_confidence=evt.attribution_confidence
        ))
        
    return {
        "ubid": ubid,
        "events": grouped
    }
