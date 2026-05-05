"""
Udyam Setu — Pydantic Schemas for Entity Resolution APIs
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class TaskResponse(BaseModel):
    task_id: str
    status: str

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None

class ERStatsResponse(BaseModel):
    total_records: int
    total_ubids: int
    auto_linked_pairs: int
    pending_review: int
    rejected_pairs: int
    records_without_ubid: int
    anchor_grade_ubids: int
    anchor_pending_ubids: int

class ReviewDecisionRequest(BaseModel):
    decision: str # "MERGE", "KEEP_SEPARATE", "ESCALATE"
    reason: str
    reviewer_id: str

class ReviewDecisionResponse(BaseModel):
    success: bool
    ubid_assigned: Optional[str] = None

# Detail view for the review queue
class CandidatePairReviewDetail(BaseModel):
    pair_id: UUID
    score: float
    record_a: Dict[str, Any]
    record_b: Dict[str, Any]
    shap_values: Dict[str, float]
    blocking_signals: List[str]
    feature_vector: Dict[str, float]
    status: str

class ReviewQueueResponse(BaseModel):
    items: List[CandidatePairReviewDetail]
    total: int
    page: int
    limit: int

class UBIDRecordDetail(BaseModel):
    ubid: str
    pan_anchor: Optional[str]
    gstin_anchor: Optional[str]
    status: str
    status_confidence: Optional[float]
    linked_records: List[Dict[str, Any]]

class UBIDLookupResponseItem(BaseModel):
    ubid: str
    confidence: float
    evidence: str

class UBIDLookupResponse(BaseModel):
    matches: List[UBIDLookupResponseItem]
