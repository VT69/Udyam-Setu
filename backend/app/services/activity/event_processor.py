"""
Udyam Setu — Event Processor
Handles ingestion and attribution of timeseries activity signals.
"""

import uuid
from typing import Dict, Any, List
from rapidfuzz import fuzz
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import AttributionStatus, Department
from app.models.business_event import BusinessEvent
from app.models.department_record import DepartmentRecord
from app.models.ubid_registry import UbidRegistry
from app.schemas.event_schemas import EventIngestRequest


class EventProcessor:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def ingest_event(self, event: EventIngestRequest) -> Dict[str, Any]:
        """
        Ingests a raw event and assigns an initial attribution status.
        """
        # 1. Look up original_record_id
        stmt = select(DepartmentRecord).where(
            DepartmentRecord.original_record_id == event.original_record_id,
            DepartmentRecord.department == event.department
        )
        result = await self.db.execute(stmt)
        dept_record = result.scalars().first()

        attr_status = AttributionStatus.UNATTRIBUTABLE
        ubid = None
        confidence = None

        if dept_record:
            if dept_record.ubid:
                # 2. Found with high confidence (already resolved to a UBID)
                attr_status = AttributionStatus.ATTRIBUTED
                ubid = dept_record.ubid
                confidence = 1.0
            else:
                # 3. Found but no UBID yet
                attr_status = AttributionStatus.PENDING_REVIEW

        # Insert event
        new_event = BusinessEvent(
            id=uuid.uuid4(),
            event_time=event.event_time,
            department=event.department,
            original_record_id=event.original_record_id,
            event_type=event.event_type,
            event_data=event.event_data,
            attribution_status=attr_status,
            attribution_confidence=confidence,
            ubid=ubid
        )
        self.db.add(new_event)
        
        return {
            "status": "success",
            "attribution_status": attr_status.value,
            "ubid": ubid,
            "attribution_confidence": confidence
        }

    async def attribute_pending_events(self) -> Dict[str, int]:
        """
        Batch job to attempt auto-attribution of PENDING_REVIEW events.
        """
        stmt = select(BusinessEvent).where(BusinessEvent.attribution_status == AttributionStatus.PENDING_REVIEW)
        result = await self.db.execute(stmt)
        pending_events = result.scalars().all()

        if not pending_events:
            return {"auto_attributed": 0, "queued_review": 0, "unattributable": 0}

        auto_attributed = 0
        queued_review = 0
        unattributable = 0

        # Optimization: preload all active UBIDs and their records for matching
        # (In production, we would use Elasticsearch or Pinecone. Doing naive scan here)
        ubid_stmt = select(UbidRegistry).options(selectinload(UbidRegistry.department_records))
        ubid_res = await self.db.execute(ubid_stmt)
        all_ubids = ubid_res.scalars().all()

        for event in pending_events:
            # Get event's business details either from event_data or underlying department record
            evt_name = event.event_data.get("business_name")
            evt_pin = event.event_data.get("pincode")

            if not evt_name or not evt_pin:
                # Fallback to department record
                rec_stmt = select(DepartmentRecord).where(DepartmentRecord.original_record_id == event.original_record_id)
                rec_res = await self.db.execute(rec_stmt)
                dept_rec = rec_res.scalars().first()
                if dept_rec:
                    evt_name = dept_rec.business_name
                    evt_pin = dept_rec.address_pincode

            if not evt_name:
                event.attribution_status = AttributionStatus.UNATTRIBUTABLE
                unattributable += 1
                continue

            best_score = 0.0
            best_ubid = None

            for u in all_ubids:
                # Find max similarity against all records in this UBID
                for r in u.department_records:
                    if evt_pin and r.address_pincode != evt_pin:
                        continue # Pincode must match for this heuristic
                    
                    score = fuzz.token_set_ratio(evt_name.lower(), r.business_name.lower()) / 100.0
                    if score > best_score:
                        best_score = score
                        best_ubid = u.ubid

            if best_score > 0.75:
                event.attribution_status = AttributionStatus.ATTRIBUTED
                event.ubid = best_ubid
                event.attribution_confidence = best_score
                auto_attributed += 1
            elif best_score >= 0.50:
                # Keep as PENDING_REVIEW, but we know it's a borderline candidate
                queued_review += 1
            else:
                event.attribution_status = AttributionStatus.UNATTRIBUTABLE
                unattributable += 1

        await self.db.commit()
        
        return {
            "auto_attributed": auto_attributed,
            "queued_review": queued_review,
            "unattributable": unattributable
        }
