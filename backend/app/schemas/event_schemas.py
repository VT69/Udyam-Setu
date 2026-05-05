"""
Udyam Setu — Pydantic Schemas for Event APIs
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

from app.models.enums import Department, AttributionStatus

class EventIngestRequest(BaseModel):
    department: Department
    original_record_id: str
    event_type: str
    event_time: datetime
    event_data: Dict[str, Any]

class EventIngestResponse(BaseModel):
    status: str
    attribution_status: str
    ubid: Optional[str] = None
    attribution_confidence: Optional[float] = None

class EventBatchIngestRequest(BaseModel):
    events: List[EventIngestRequest]

class EventBatchIngestResponse(BaseModel):
    attributed: int
    pending: int
    unattributable: int

class CandidateUbid(BaseModel):
    ubid: str
    score: float
    matched_name: Optional[str] = None

class AttributionQueueItem(BaseModel):
    event_id: UUID
    event_time: datetime
    department: str
    original_record_id: str
    event_type: str
    event_data: Dict[str, Any]
    candidate_ubids: List[CandidateUbid] = []

class AttributionQueueResponse(BaseModel):
    items: List[AttributionQueueItem]
    total: int
    page: int
    limit: int

class AttributeEventRequest(BaseModel):
    ubid: str
    reviewer_id: str

class TimelineEvent(BaseModel):
    event_id: UUID
    event_time: datetime
    event_type: str
    event_data: Dict[str, Any]
    attribution_confidence: Optional[float]

class TimelineResponse(BaseModel):
    ubid: str
    events: Dict[str, Dict[str, List[TimelineEvent]]] # {department: {event_type: [events]}}
