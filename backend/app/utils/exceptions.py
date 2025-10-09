from __future__ import annotations
from typing import Any, Optional


class ExternalServiceError(Exception):
    """Error genérico para servicios externos (Odoo, Otras APIs, etc.)."""

    def __init__(
        self,
        message: str,
        *,
        service: str = "external",
        code: str = "external_error",
        status_code: int = 502,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.service = service
        self.code = code
        self.status_code = status_code
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "service": self.service,
            "code": self.code,
            "message": str(self),
            "details": self.details,
        }


class OdooServiceError(ExternalServiceError):
    def __init__(self, message: str, *, code: str = "odoo_error", status_code: int = 502, details: Optional[dict[str, Any]] = None):
        super().__init__(message, service="odoo", code=code, status_code=status_code, details=details)


# Eliminadas clases específicas de integraciones obsoletas (Plaid, Argus)
