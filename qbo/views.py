from urllib.parse import urlencode
from django.http import HttpResponseRedirect, JsonResponse, HttpResponseBadRequest
from django.conf import settings
from django.core import signing
from django.utils import timezone
from schools.models import School, QBOConnection
import qbo.oauth as qbo_oauth

SCOPES = ["com.intuit.quickbooks.accounting"]
AUTH_URL = "https://appcenter.intuit.com/connect/oauth2"

def qbo_authorize(request):
    school_code = request.GET.get("school")
    if not school_code:
        return HttpResponseBadRequest("missing school")
    try:
        school = School.objects.get(code=school_code)
    except School.DoesNotExist:
        return HttpResponseBadRequest("invalid school")

    state = signing.dumps({"school": school.code}, salt="qbo")
    q = {
        "client_id": settings.QBO_CLIENT_ID,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "redirect_uri": settings.QBO_REDIRECT_URI,
        "state": state,
    }
    return HttpResponseRedirect(f"{AUTH_URL}?{urlencode(q)}")

def qbo_callback(request):
    code = request.GET.get("code")
    state = request.GET.get("state")
    realm_id = request.GET.get("realmId")
    if not (code and state and realm_id):
        return HttpResponseBadRequest("missing params")
    try:
        data = signing.loads(state, salt="qbo")
        school = School.objects.get(code=data["school"])
    except Exception:
        return HttpResponseBadRequest("bad state")

    tokens = qbo_oauth.exchange_code_for_tokens(code)
    expires = timezone.now() + timezone.timedelta(seconds=int(tokens.get("expires_in", 3600)))
    conn, _ = QBOConnection.objects.update_or_create(
        school=school,
        defaults={
            "realm_id": realm_id,
            "access_token": tokens["access_token"],
            "refresh_token": tokens.get("refresh_token", ""),
            "token_expires_at": expires,
        },
    )
    return JsonResponse({"detail": "connected", "school": school.code, "realm_id": conn.realm_id})