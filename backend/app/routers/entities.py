"""
Udyam Setu — Entity Router (CRUD)
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.business_entity import BusinessEntity
from app.schemas import BusinessEntityCreate, BusinessEntityRead, BusinessEntityUpdate

router = APIRouter()


# ── List entities ─────────────────────────────────────────────
@router.get("/entities", response_model=List[BusinessEntityRead])
async def list_entities(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Return a paginated list of business entities."""
    stmt = select(BusinessEntity).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


# ── Get single entity ────────────────────────────────────────
@router.get("/entities/{entity_id}", response_model=BusinessEntityRead)
async def get_entity(
    entity_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve a single business entity by ID."""
    entity = await db.get(BusinessEntity, entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity


# ── Create entity ────────────────────────────────────────────
@router.post("/entities", response_model=BusinessEntityRead, status_code=201)
async def create_entity(
    payload: BusinessEntityCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new business entity record."""
    entity = BusinessEntity(**payload.model_dump())
    db.add(entity)
    await db.flush()
    await db.refresh(entity)
    return entity


# ── Update entity ────────────────────────────────────────────
@router.patch("/entities/{entity_id}", response_model=BusinessEntityRead)
async def update_entity(
    entity_id: UUID,
    payload: BusinessEntityUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Partially update a business entity."""
    entity = await db.get(BusinessEntity, entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(entity, field, value)

    await db.flush()
    await db.refresh(entity)
    return entity


# ── Delete entity ─────────────────────────────────────────────
@router.delete("/entities/{entity_id}", status_code=204)
async def delete_entity(
    entity_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a business entity."""
    entity = await db.get(BusinessEntity, entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    await db.delete(entity)
