"""
Udyam Setu — Advanced Seed Data Script (Karnataka / Bengaluru Focus)
Generates realistic MSME records across 4 departments with noise,
address variations, and 18 months of time-series business events.
"""

import sys
import os
import random
import uuid
import string
import asyncio
from datetime import datetime, timedelta, date

# Add the project root to sys.path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app.database import async_session_factory
from app.models.enums import Department, RegistryStatus, AttributionStatus
from app.models.department_record import DepartmentRecord
from app.models.ubid_registry import UbidRegistry
from app.models.business_event import BusinessEvent

# ─── Constants & Data Dictionaries ──────────────────────────────────────────────

PINCODES = {
    "560058": ["Peenya Industrial Area", "KIADB Indl Area, Phase 2, Peenya", "Laggere", "Hegganahalli", "Chokkasandra"],
    "560100": ["Electronic City Phase 1", "Electronic City Phase 2", "Bommasandra Industrial Area", "Veerasandra", "Doddatoguru"]
}

NICS = {"Textiles": "131", "Manufacturing": "282", "Foods": "107", "Technologies": "620", "Chemicals": "201", "Plastics": "222"}
BUSINESS_TYPES = list(NICS.keys())

LEGAL_SUFFIXES = ["Pvt Ltd", "Private Limited", "(P) Ltd", "Ltd", "LLP", "Enterprises", "Industries"]
PREFIXES = ["M/s ", "Sri ", "Shree ", ""]
NAMES_FIRST = ["Rajan", "Anand", "Karnataka", "Bengaluru", "Kaveri", "Mysore", "Namma", "Tech", "Global", "Indian", "Sunrise", "Apex", "Pioneer", "Srinivasa", "Venkateshwara", "Ganesh", "Bharath"]

def random_date(start_year=2005, end_year=2023):
    start_date = date(start_year, 1, 1)
    end_date = date(end_year, 12, 31)
    delta = end_date - start_date
    random_days = random.randrange(delta.days)
    return start_date + timedelta(days=random_days)

def generate_base_business():
    name_core = f"{random.choice(NAMES_FIRST)} {random.choice(BUSINESS_TYPES)}"
    suffix = random.choice(LEGAL_SUFFIXES)
    prefix = random.choice(PREFIXES)
    business_name = f"{prefix}{name_core} {suffix}".strip().replace("  ", " ")
    
    pincode = random.choice(list(PINCODES.keys()))
    locality = random.choice(PINCODES[pincode])
    door = f"No. {random.randint(1, 999)}/{random.choice(['A','B','C','D', ''])}"
    address_raw = f"{door}, {locality}, Bengaluru, Karnataka {pincode}".replace(" ,", ",")
    
    reg_date = random_date()
    
    # PAN / GSTIN rules (70% PAN, 60% of PAN have GSTIN)
    pan = None
    gstin = None
    if random.random() < 0.7 or reg_date.year > 2015:
        # Generate PAN
        c_char = "C" if "Ltd" in suffix else ("F" if suffix == "LLP" else "P")
        n_char = name_core[0].upper()
        pan = f"AA{random.choice(string.ascii_uppercase)}{c_char}{n_char}{random.randint(1000, 9999)}{random.choice(string.ascii_uppercase)}"
        
        if random.random() < 0.6:
            gstin = f"29{pan}1Z{random.choice(string.ascii_uppercase + string.digits)}"

    # Status: 15 closed, 30 dormant, rest active
    # We will set this externally later to ensure exact counts, but we default to ACTIVE
    
    return {
        "business_name": business_name,
        "address_raw": address_raw,
        "address_locality": locality,
        "address_pincode": pincode,
        "pan": pan,
        "gstin": gstin,
        "nic_code": NICS[[bt for bt in BUSINESS_TYPES if bt in name_core][0]] + str(random.randint(10, 99)),
        "registration_date": reg_date,
        "phone": f"+91 {random.randint(7000000000, 9999999999)}",
        "ubid": f"KA-UBID-{uuid.uuid4().hex[:8].upper()}"
    }

def apply_name_noise(name):
    variations = [
        lambda x: x.replace("Pvt Ltd", "(P) Ltd"),
        lambda x: x.replace("Private Limited", "Pvt. Ltd."),
        lambda x: x.replace("Manufacturing", "Mfg."),
        lambda x: x.replace("Industrial", "Indl."),
        lambda x: x.replace("Enterprises", "Ent."),
        lambda x: x.replace("M/s ", ""),
        lambda x: x.lower(),
        lambda x: x.upper(),
        lambda x: x + " " # Trailing space
    ]
    # Apply 1 or 2 random variations
    for _ in range(random.randint(1, 2)):
        name = random.choice(variations)(name)
    return name

def apply_address_noise(addr):
    variations = [
        lambda x: x.replace("Bengaluru", "Bangalore"),
        lambda x: x.replace("Karnataka ", ""),
        lambda x: x.split(", ", 1)[-1], # Remove door number
        lambda x: x.replace("Industrial Area", "Indl Area"),
        lambda x: x.replace("Phase 1", "Ph-1").replace("Phase 2", "Ph-2"),
    ]
    for _ in range(random.randint(0, 1)):
        addr = random.choice(variations)(addr)
    return addr

# ─── Main Generation Loop ───────────────────────────────────────────────────────

async def generate_and_seed():
    print("Generating base businesses...")
    
    # 1. Generate 180 standard businesses + 20 ambiguous pairs (10 base * 2) = 200 total
    base_businesses = [generate_base_business() for _ in range(180)]
    
    ambiguous_bases = [generate_base_business() for _ in range(10)]
    for ab in ambiguous_bases:
        ab1 = dict(ab)
        ab1["ubid"] = f"KA-UBID-{uuid.uuid4().hex[:8].upper()}"
        
        ab2 = dict(ab)
        ab2["ubid"] = f"KA-UBID-{uuid.uuid4().hex[:8].upper()}"
        # Same name, different pincode/locality
        new_pincode = "560100" if ab["address_pincode"] == "560058" else "560058"
        new_locality = random.choice(PINCODES[new_pincode])
        ab2["address_pincode"] = new_pincode
        ab2["address_locality"] = new_locality
        ab2["address_raw"] = f"Unit 2, {new_locality}, Bengaluru {new_pincode}"
        
        base_businesses.extend([ab1, ab2])

    # Assign statuses: 15 CLOSED, 30 DORMANT, 155 ACTIVE
    random.shuffle(base_businesses)
    for i, b in enumerate(base_businesses):
        if i < 15:
            b["status"] = RegistryStatus.CLOSED
        elif i < 45:
            b["status"] = RegistryStatus.DORMANT
        else:
            b["status"] = RegistryStatus.ACTIVE

    ubid_records = []
    dept_records = []
    events = []
    
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=18 * 30) # 18 months ago
    
    for bb in base_businesses:
        # Create UBID Registry entry
        ubid_records.append(UbidRegistry(
            ubid=bb["ubid"],
            pan_anchor=bb["pan"],
            gstin_anchor=bb["gstin"],
            anchor_pending=False,
            status=bb["status"],
            status_confidence=0.95
        ))
        
        # Decide which departments this business appears in (2 to 4)
        depts = random.sample(list(Department), random.randint(2, 4))
        
        for dept in depts:
            # Drop PAN/GSTIN sometimes based on department
            record_pan = bb["pan"] if random.random() < 0.9 else None
            record_gstin = bb["gstin"] if random.random() < 0.8 else None
            
            raw_data = {}
            if dept == Department.SHOP_ESTABLISHMENT:
                raw_data = {
                    "shop_number": f"SE/{bb['address_pincode']}/{random.randint(1000, 9999)}",
                    "establishment_type": "Commercial",
                    "employee_count": random.randint(2, 50)
                }
            elif dept == Department.FACTORIES:
                raw_data = {
                    "factory_licence": f"FL/{random.randint(10000, 99999)}",
                    "hazard_category": random.choice(["Low", "Medium", "High"]),
                    "floor_area_sqm": random.randint(500, 5000)
                }
            elif dept == Department.LABOUR:
                raw_data = {
                    "contractor_licence": f"CL-{random.randint(100, 999)}",
                    "worker_count": random.randint(10, 200),
                    "esi_number": f"47{random.randint(1000000000, 9999999999)}"
                }
            elif dept == Department.KSPCB:
                raw_data = {
                    "consent_number": f"KSPCB/AW/{random.randint(1000, 9999)}",
                    "pollution_category": random.choice(["Green", "Orange", "Red"])
                }
            elif dept == Department.BESCOM:
                raw_data = {
                    "rr_number": f"RR{random.choice(['E','W','N','S'])}{random.randint(1000, 9999)}",
                    "tariff_category": "HT-2A" if random.random() > 0.5 else "LT-5"
                }

            dept_records.append(DepartmentRecord(
                department=dept,
                original_record_id=str(uuid.uuid4()),
                business_name=bb["business_name"], # raw
                business_name_normalized=apply_name_noise(bb["business_name"]),
                address_raw=apply_address_noise(bb["address_raw"]),
                address_locality=bb["address_locality"],
                address_pincode=bb["address_pincode"],
                pan=record_pan,
                gstin=record_gstin,
                nic_code=bb["nic_code"],
                registration_date=bb["registration_date"],
                phone=bb["phone"] if random.random() < 0.8 else None,
                raw_data=raw_data,
                ubid=bb["ubid"] # Pre-linking them for ground truth
            ))

            # ─── Event Generation ───────────────────────────────────────────────
            
            # Events run from 18 months ago to now
            if dept == Department.BESCOM:
                # Monthly consumption
                for month_offset in range(18):
                    event_date = start_time + timedelta(days=month_offset * 30 + random.randint(1, 5))
                    
                    # Logic for CLOSED: zero consumption in last 6 months
                    consumption = random.randint(500, 15000)
                    if bb["status"] == RegistryStatus.CLOSED and month_offset >= 12:
                        consumption = 0
                        
                    events.append(BusinessEvent(
                        ubid=bb["ubid"],
                        department=Department.BESCOM,
                        original_record_id=f"B-EVT-{uuid.uuid4().hex[:6]}",
                        event_type="CONSUMPTION",
                        event_time=event_date,
                        event_data={"units_consumed": consumption, "billed_amount": consumption * 8},
                        attribution_status=AttributionStatus.ATTRIBUTED,
                        attribution_confidence=1.0
                    ))

            elif dept == Department.FACTORIES:
                if bb["status"] == RegistryStatus.ACTIVE:
                    # 1-3 inspections randomly in the 18 months
                    for _ in range(random.randint(1, 3)):
                        event_date = start_time + timedelta(days=random.randint(0, 18 * 30))
                        events.append(BusinessEvent(
                            ubid=bb["ubid"],
                            department=Department.FACTORIES,
                            original_record_id=f"F-EVT-{uuid.uuid4().hex[:6]}",
                            event_type="INSPECTION",
                            event_time=event_date,
                            event_data={"inspector_id": f"INS-{random.randint(100, 999)}", "violations_found": random.randint(0, 2)},
                            attribution_status=AttributionStatus.ATTRIBUTED
                        ))

            elif dept == Department.KSPCB and raw_data.get("pollution_category") in ["Red", "Orange"]:
                if bb["status"] == RegistryStatus.ACTIVE:
                    # Annual renewal
                    event_date = start_time + timedelta(days=random.randint(100, 200))
                    events.append(BusinessEvent(
                        ubid=bb["ubid"],
                        department=Department.KSPCB,
                        original_record_id=f"K-EVT-{uuid.uuid4().hex[:6]}",
                        event_type="RENEWAL",
                        event_time=event_date,
                        event_data={"fee_paid": True, "validity_years": 1},
                        attribution_status=AttributionStatus.ATTRIBUTED
                    ))

            elif dept == Department.SHOP_ESTABLISHMENT:
                if bb["status"] in [RegistryStatus.ACTIVE, RegistryStatus.DORMANT]:
                    # Dormant might miss renewal, Active mostly renews
                    if bb["status"] == RegistryStatus.ACTIVE or random.random() > 0.5:
                        event_date = start_time + timedelta(days=random.randint(50, 300))
                        events.append(BusinessEvent(
                            ubid=bb["ubid"],
                            department=Department.SHOP_ESTABLISHMENT,
                            original_record_id=f"S-EVT-{uuid.uuid4().hex[:6]}",
                            event_type="RENEWAL",
                            event_time=event_date,
                            event_data={"fee_paid": True},
                            attribution_status=AttributionStatus.ATTRIBUTED
                        ))

    # Print Summary Statistics
    print("\n--- SYNTHETIC DATA GENERATION SUMMARY ---")
    print(f"Total Golden Records (UBIDs): {len(ubid_records)}")
    status_counts = {"ACTIVE": 0, "DORMANT": 0, "CLOSED": 0}
    for u in ubid_records: status_counts[u.status.value] += 1
    print(f"  - Active: {status_counts['ACTIVE']}")
    print(f"  - Dormant: {status_counts['DORMANT']}")
    print(f"  - Closed: {status_counts['CLOSED']}")
    
    print(f"\nTotal Department Records: {len(dept_records)}")
    dept_counts = {d.value: 0 for d in Department}
    for d in dept_records: dept_counts[d.department.value] += 1
    for k, v in dept_counts.items(): print(f"  - {k}: {v}")
    
    print(f"\nTotal Business Events (18 months): {len(events)}")
    evt_counts = {}
    for e in events: evt_counts[e.event_type] = evt_counts.get(e.event_type, 0) + 1
    for k, v in evt_counts.items(): print(f"  - {k}: {v}")
    
    print("\nInserting data into PostgreSQL / TimescaleDB...")
    
    # Bulk insert using SQLAlchemy
    async with async_session_factory() as session:
        # 1. Insert UBID Registry
        session.add_all(ubid_records)
        await session.flush()
        
        # 2. Insert Department Records
        # Process in chunks to avoid huge memory usage
        chunk_size = 500
        for i in range(0, len(dept_records), chunk_size):
            session.add_all(dept_records[i:i+chunk_size])
        await session.flush()
        
        # 3. Insert Events
        for i in range(0, len(events), chunk_size):
            session.add_all(events[i:i+chunk_size])
        
        await session.commit()

    print("Data seeded successfully!")

if __name__ == "__main__":
    # Workaround for Windows asyncio loop if needed
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(generate_and_seed())
