"""
Udyam Setu — BusinessEntity ORM Model
Represents a business identity record ingested from regulatory sources.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    Float,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class BusinessEntity(Base):
    """A single business identity record (pre-resolution)."""

    __tablename__ = "business_entities"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )

    # ── Identifiers ───────────────────────────────────────────
    udyam_number = Column(String(32), unique=True, nullable=True, index=True)
    pan = Column(String(10), nullable=True, index=True)
    gstin = Column(String(15), nullable=True, index=True)

    # ── Business details ──────────────────────────────────────
    business_name = Column(String(512), nullable=False)
    business_type = Column(String(64), nullable=True)
    nic_code = Column(String(10), nullable=True)
    state = Column(String(64), nullable=True)
    district = Column(String(128), nullable=True)
    address = Column(Text, nullable=True)

    # ── Financial ─────────────────────────────────────────────
    investment = Column(Float, nullable=True)
    turnover = Column(Float, nullable=True)

    # ── Source metadata ───────────────────────────────────────
    source_system = Column(String(64), nullable=True)
    ingested_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ── Resolution ────────────────────────────────────────────
    cluster_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    match_confidence = Column(Float, nullable=True)

    __table_args__ = (
        Index("ix_entity_name_trgm", "business_name"),
    )

    def __repr__(self) -> str:
        return f"<BusinessEntity {self.udyam_number or self.business_name}>"
