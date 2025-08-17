import hmac, hashlib
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from django.conf import settings
from django.http import HttpRequest

def get_signature_header(request: HttpRequest) -> str | None:
    return request.headers.get("X-Signature") or request.META.get("HTTP_X_SIGNATURE")

def get_timestamp_header(request: HttpRequest) -> str | None:
    return request.headers.get("X-Timestamp") or request.headers.get("Date") or request.META.get("HTTP_X_TIMESTAMP")

def constant_time_equals(a: str, b: str) -> bool:
    return hmac.compare_digest(a.encode(), b.encode())

def verify_hmac(secret: str, body: bytes, provided: str | None) -> bool:
    if not secret or not provided: return False
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return constant_time_equals(digest, provided)

def _parse_ts(value: str | None):
    if not value: return None
    v = value.strip()
    if v.isdigit():
        try: return datetime.fromtimestamp(int(v), tz=timezone.utc)
        except Exception: return None
    try:
        dt = parsedate_to_datetime(v)
        return dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None

def verify_hmac_with_timestamp(secret: str, body: bytes, sig: str | None, ts: str | None) -> bool:
    if not verify_hmac(secret, body, sig):
        return False
    tol = int(getattr(settings, "WEBHOOK_TIMESTAMP_TOLERANCE", 300))
    dt = _parse_ts(ts)
    if dt is None:  # tolerate if provider doesn't send a timestamp
        return True
    return abs((datetime.now(timezone.utc) - dt).total_seconds()) <= tol