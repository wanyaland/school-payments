# qbo/oauth.py
import requests
from django.conf import settings

TOKEN_URL = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"


def exchange_code_for_tokens(code: str) -> dict:
    """
    Authorization Code -> Access/Refresh tokens
    """
    auth = (settings.QBO_CLIENT_ID, settings.QBO_CLIENT_SECRET)
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.QBO_REDIRECT_URI,
    }
    r = requests.post(TOKEN_URL, data=data, auth=auth, timeout=20)
    r.raise_for_status()
    return r.json()

def refresh_access_token(refresh_token: str) -> dict:
    """
    Refresh token -> New access/refresh tokens
    """
    auth = (settings.QBO_CLIENT_ID, settings.QBO_CLIENT_SECRET)
    data = {"grant_type": "refresh_token", "refresh_token": refresh_token}
    r = requests.post(TOKEN_URL, data=data, auth=auth, timeout=20)
    r.raise_for_status()
    return r.json()
