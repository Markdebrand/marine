from typing import Callable, Any
from fastapi import Depends
from app.db import models as m
from app.core.auth.session_manager import get_current_user, get_token_payload as _get_token_payload


class CurrentUser:
    def __init__(self, sub: str):
        self.sub = sub


def get_token_payload() -> dict:
    # Re-export to keep imports stable if used elsewhere
    return _get_token_payload()  # type: ignore[misc]


def require_roles(*roles: str):
    def _dep(user: m.User = Depends(get_current_user)) -> m.User:
        return user
    return _dep
