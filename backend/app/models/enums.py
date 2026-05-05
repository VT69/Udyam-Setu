"""
Udyam Setu — Enums for ORM Models
"""

import enum

class Department(str, enum.Enum):
    SHOP_ESTABLISHMENT = "SHOP_ESTABLISHMENT"
    FACTORIES = "FACTORIES"
    LABOUR = "LABOUR"
    KSPCB = "KSPCB"
    BESCOM = "BESCOM"

class RegistryStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    DORMANT = "DORMANT"
    CLOSED = "CLOSED"
    UNCLASSIFIED = "UNCLASSIFIED"

class PairStatus(str, enum.Enum):
    PENDING_REVIEW = "PENDING_REVIEW"
    AUTO_LINKED = "AUTO_LINKED"
    REJECTED = "REJECTED"
    MERGED = "MERGED"
    KEPT_SEPARATE = "KEPT_SEPARATE"
    ESCALATED = "ESCALATED"

class Decision(str, enum.Enum):
    MERGE = "MERGE"
    KEEP_SEPARATE = "KEEP_SEPARATE"
    ESCALATE = "ESCALATE"

class UserRole(str, enum.Enum):
    REVIEWER = "REVIEWER"
    ADMIN = "ADMIN"
    VIEWER = "VIEWER"

class AttributionStatus(str, enum.Enum):
    ATTRIBUTED = "ATTRIBUTED"
    PENDING_REVIEW = "PENDING_REVIEW"
    UNATTRIBUTABLE = "UNATTRIBUTABLE"
