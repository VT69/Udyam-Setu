"""
Udyam Setu — Candidate Pair Model
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, Float, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.enums import PairStatus

class CandidatePair(Base):
    """Potential links identified by the ML resolution engine."""
    __tablename__ = "candidate_pairs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign keys to the two records being compared
    record_a_id = Column(UUID(as_uuid=True), ForeignKey("department_records.id"), nullable=False, index=True)
    record_b_id = Column(UUID(as_uuid=True), ForeignKey("department_records.id"), nullable=False, index=True)
    
    score = Column(Float, nullable=False)
    blocking_signals = Column(JSONB, nullable=False, default=dict)
    shap_values = Column(JSONB, nullable=True, default=dict)
    feature_vector = Column(JSONB, nullable=True, default=dict)
    
    status = Column(Enum(PairStatus), nullable=False, default=PairStatus.PENDING_REVIEW, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    record_a = relationship("DepartmentRecord", foreign_keys=[record_a_id])
    record_b = relationship("DepartmentRecord", foreign_keys=[record_b_id])

    def __repr__(self):
        return f"<CandidatePair {self.record_a_id} - {self.record_b_id} (Score: {self.score})>"
