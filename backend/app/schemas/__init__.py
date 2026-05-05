"""
Udyam Setu — Pydantic Schemas (request / response models)
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ── Base ──────────────────────────────────────────────────────
class BusinessEntityBase(BaseModel):
    """Fields shared across create / update / read."""

    business_name: str = Field(..., max_length=512)
    udyam_number: Optional[str] = Field(None, max_length=32)
    pan: Optional[str] = Field(None, max_length=10)
    gstin: Optional[str] = Field(None, max_length=15)
    business_type: Optional[str] = None
    nic_code: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    address: Optional[str] = None
    investment: Optional[float] = None
    turnover: Optional[float] = None
    source_system: Optional[str] = None


# ── Create ────────────────────────────────────────────────────
class BusinessEntityCreate(BusinessEntityBase):
    """Schema for creating a new business entity."""
    pass


# ── Update ────────────────────────────────────────────────────
class BusinessEntityUpdate(BaseModel):
    """Partial update — all fields optional."""

    business_name: Optional[str] = None
    udyam_number: Optional[str] = None
    pan: Optional[str] = None
    gstin: Optional[str] = None
    business_type: Optional[str] = None
    nic_code: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    address: Optional[str] = None
    investment: Optional[float] = None
    turnover: Optional[float] = None
    source_system: Optional[str] = None


# ── Read (response) ──────────────────────────────────────────
class BusinessEntityRead(BusinessEntityBase):
    """Schema returned from API — includes server-generated fields."""

    id: UUID
    cluster_id: Optional[UUID] = None
    match_confidence: Optional[float] = None
    ingested_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Health ────────────────────────────────────────────────────
class HealthResponse(BaseModel):
    status: str
    service: str
