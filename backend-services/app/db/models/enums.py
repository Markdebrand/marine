from __future__ import annotations

from enum import Enum


class MemberRole(str, Enum):
    admin = "admin"
    member = "member"


class SubscriptionStatus(str, Enum):
    active = "active"
    canceled = "canceled"
    past_due = "past_due"


class SupportLevel(str, Enum):
    BASIC = "BASIC"
    STANDARD = "STANDARD"
    PRIORITY = "PRIORITY"
    DEDICATED = "DEDICATED"


class ReportStatus(str, Enum):
    draft = "draft"
    running = "running"
    ready = "ready"
    error = "error"


class ValidationStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    canceled = "canceled"
    error = "error"


class TxStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    failed = "failed"


__all__ = [
    "MemberRole",
    "SubscriptionStatus",
    "SupportLevel",
    "ReportStatus",
    "ValidationStatus",
    "TxStatus",
]
