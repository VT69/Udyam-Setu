"""
Udyam Setu — Business Event Model (TimescaleDB Hypertable)
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Float, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.database import Base
from app.models.enums import Department, AttributionStatus

class BusinessEvent(Base):
    """
    Time-series event data representing activity signals.
    Configured as a TimescaleDB hypertable on `event_time`.
    """
    __tablename__ = "business_events"

    # TimescaleDB requires the partitioning column to be part of any unique/primary index.
    # Therefore, we make both `event_time` and `id` the primary key.
    event_time = Column(DateTime, primary_key=True, index=True)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    ubid = Column(String(32), ForeignKey("ubid_registry.ubid"), nullable=True, index=True)
    department = Column(Enum(Department), nullable=False)
    original_record_id = Column(String(128), nullable=False)
    
    # E.g., INSPECTION, RENEWAL, LICENCE_ISSUED, CONSUMPTION, COMPLIANCE_FILING, CLOSURE_ORDER, SIGNATORY_CHANGE
    event_type = Column(String(128), nullable=False, index=True)
    
    event_data = Column(JSONB, nullable=False, default=dict)
    
    attribution_status = Column(Enum(AttributionStatus), nullable=False, default=AttributionStatus.UNATTRIBUTABLE)
    attribution_confidence = Column(Float, nullable=True)

    def __repr__(self):
        return f"<BusinessEvent {self.event_type} at {self.event_time}>"
