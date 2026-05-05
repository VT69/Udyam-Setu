"""
Udyam Setu — Pydantic Schemas for Activity APIs
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

class TopSignal(BaseModel):
    feature: str
    value: float
    contribution: float
    direction: Optional[str] = None

class ActivityTimelineEvent(BaseModel):
    date: datetime
    dept: str
    event_type: str
    shap_impact: Optional[float] = None

class StatusResponse(BaseModel):
    ubid: str
    status: str
    confidence: float
    probabilities: Dict[str, float]
    last_classified_at: Optional[datetime]
    evidence_summary: str
    top_signals: List[TopSignal]
    event_timeline: List[ActivityTimelineEvent]
    needs_review: bool

class TaskResponse(BaseModel):
    task_id: str

class ActivityStatsResponse(BaseModel):
    active_count: int
    dormant_count: int
    closed_count: int
    unclassified_count: int
    needs_review_count: int

class CrossDepartmentResult(BaseModel):
    ubid: str
    business_name: str
    status: str
    confidence: float
    linked_departments: List[str]
    last_inspection_date: Optional[datetime]
    months_since_inspection: Optional[int]
    pincode: str
    district: str
    evidence_summary: str

class CrossDepartmentQueryResponse(BaseModel):
    total_results: int
    query_interpreted_as: str
    results: List[CrossDepartmentResult]
    query_sql: str

class ReviewQueueItem(BaseModel):
    ubid: str
    status: str
    confidence: float
    evidence_summary: str

class ActivityReviewQueueResponse(BaseModel):
    items: List[ReviewQueueItem]
    total: int
    page: int
    limit: int

class OverrideRequest(BaseModel):
    status: str
    reason: str
    reviewer_id: str

class OverrideResponse(BaseModel):
    success: bool
    ubid: str
    new_status: str
