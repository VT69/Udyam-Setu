"""
Udyam Setu — Department Record Model
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Float, DateTime, Date, Enum, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.enums import Department

class DepartmentRecord(Base):
    """Raw record ingested from a specific department."""
    __tablename__ = "department_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    department = Column(Enum(Department), nullable=False, index=True)
    original_record_id = Column(String(128), nullable=False)
    
    business_name = Column(String(512), nullable=False)
    business_name_normalized = Column(String(512), nullable=False, index=True)
    
    address_raw = Column(String(1024), nullable=False)
    address_street = Column(String(512), nullable=True)
    address_locality = Column(String(512), nullable=True)
    address_pincode = Column(String(10), nullable=False, index=True)
    address_district = Column(String(128), nullable=True)
    address_lat = Column(Float, nullable=True)
    address_lng = Column(Float, nullable=True)
    
    pan = Column(String(10), nullable=True, index=True)
    gstin = Column(String(15), nullable=True, index=True)
    nic_code = Column(String(10), nullable=True)
    registration_date = Column(Date, nullable=True)
    
    phone = Column(String(32), nullable=True)
    email = Column(String(256), nullable=True)
    signatory_name = Column(String(256), nullable=True)
    
    raw_data = Column(JSONB, nullable=False, default=dict)
    ingested_at = Column(DateTime, default=datetime.utcnow)
    
    # Foreign key to ubid_registry (nullable, filled after resolution)
    ubid = Column(String(32), ForeignKey("ubid_registry.ubid"), nullable=True, index=True)

    # Relationships
    ubid_registry = relationship("UbidRegistry", backref="department_records")

    __table_args__ = (
        Index("ix_department_records_pan", "pan"),
        Index("ix_department_records_gstin", "gstin"),
        Index("ix_department_records_address_pincode", "address_pincode"),
    )

    def __repr__(self):
        return f"<DepartmentRecord {self.department.value} - {self.original_record_id}>"
