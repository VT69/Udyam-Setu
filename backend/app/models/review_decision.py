"""
Udyam Setu — Review Decision Model
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Float, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.enums import Decision

class ReviewDecision(Base):
    """Human reviewer decisions on candidate pairs."""
    __tablename__ = "review_decisions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    pair_id = Column(UUID(as_uuid=True), ForeignKey("candidate_pairs.id"), nullable=False, index=True)
    
    # reviewer_id could be a string if we don't strictly enforce foreign keys to users in this service,
    # but since we have a User model, we'll make it a foreign key. 
    # If the user strictly wants a string, we can still use String but it conceptually links to the user.
    # The prompt specified "(string)". I will use String(128) to accommodate either a UUID string or a username.
    reviewer_id = Column(String(128), ForeignKey("users.id"), nullable=False, index=True)
    
    decision = Column(Enum(Decision), nullable=False)
    reason = Column(String(1024), nullable=False) # Min length 10 enforced at API/schema level
    decided_at = Column(DateTime, default=datetime.utcnow)
    score_at_decision = Column(Float, nullable=False)

    # Relationships
    candidate_pair = relationship("CandidatePair", backref="review_decisions")
    reviewer = relationship("User", backref="decisions")

    def __repr__(self):
        return f"<ReviewDecision {self.decision.value} for Pair {self.pair_id}>"
