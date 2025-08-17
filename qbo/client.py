from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict
from django.utils import timezone as dj_tz

@dataclass
class QBOAuth:
    realm_id: str
    access_token: str
    refresh_token: str
    token_expires_at: datetime

class QBOClient:
    def __init__(self, auth: QBOAuth | None = None, mapping: dict[str, Any] | None = None):
        self.auth = auth
        self.mapping = mapping or {}
    def is_expired(self) -> bool:
        return bool(self.auth and self.auth.token_expires_at <= dj_tz.now())
    def refresh(self) -> None:
        raise NotImplementedError
    def create_sales_receipt(self, payment) -> Dict[str, Any]:
        """Intentionally unimplemented; tests monkeypatch this method."""
        raise NotImplementedError