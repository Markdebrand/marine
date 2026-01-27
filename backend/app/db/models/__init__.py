"""Modelos de base de datos organizados por contexto.

Este paquete reexporta los modelos para permitir `from app.db.models import User, ...`.
"""
from __future__ import annotations

from .user import User, SessionToken
from .plan import Plan, Subscription
from .rbac import Role, Permission, RolePermission, UserRole
from .usage import UsageCounter
from .activation import ActivationToken
from .password_reset_token import PasswordResetToken
from .enums import (
    MemberRole,
    SubscriptionStatus,
    SupportLevel,
    ReportStatus,
    ValidationStatus,
    TxStatus,
)
from .release import Release, ReleaseSection
from .user_preferences import UserPreference

# HSOMarine domain models
from .res_user import ResUser
from .marine_port import MarinePort
from .marine_vessel import MarineVessel
from .vessel_state import VesselState
from .vessel_snapshot import VesselSnapshot
from .marine_watchlist import MarineWatchlist
from .marine_alert import MarineAlert
from .marine_provider_contract import MarineProviderContract
from .marine_audit import MarineAudit

__all__ = [
    "User",
    "Plan",
    "Subscription",
    "Role",
    "Permission",
    "RolePermission",
    "UserRole",
    "SessionToken",
    "UsageCounter",
    "ActivationToken",
    "PasswordResetToken",
    "MemberRole",
    "SubscriptionStatus",
    "SupportLevel",
    "ReportStatus",
    "ValidationStatus",
    "TxStatus",
    "Release",
    "ReleaseSection",
    "UserPreference",
    # HSOMarine
    "ResUser",
    "MarinePort",
    "MarineVessel",
    "VesselState",
    "VesselSnapshot",
    "MarineWatchlist",
    "MarineAlert",
    "MarineProviderContract",
    "MarineAudit",
]
