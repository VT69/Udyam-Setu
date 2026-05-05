"""
Udyam Setu — UBID Registry Model
"""

from datetime import datetime

from sqlalchemy import Column, String, Boolean, Float, DateTime, Enum, Index

from app.database import Base
from app.models.enums import RegistryStatus

class UbidRegistry(Base):
    """The golden record registry for businesses."""
    __tablename__ = "ubid_registry"

    ubid = Column(String(32), primary_key=True, index=True) # Format: KA-UBID-XXXXXXXX
    pan_anchor = Column(String(10), nullable=True, index=True)
    gstin_anchor = Column(String(15), nullable=True, index=True)
    anchor_pending = Column(Boolean, default=True)
    status = Column(Enum(RegistryStatus), default=RegistryStatus.UNCLASSIFIED)
    status_confidence = Column(Float, nullable=True)
    status_updated_at = Column(DateTime, nullable=True)
    linkage_pending = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_ubid_registry_pan_anchor", "pan_anchor"),
        Index("ix_ubid_registry_gstin_anchor", "gstin_anchor"),
    )

    def __repr__(self):
        return f"<UbidRegistry {self.ubid}>"
