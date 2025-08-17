import pytest
from django.urls import reverse
from django.core import signing
from schools.models import School, QBOConnection

@pytest.mark.django_db
def test_qbo_authorize_redirect_builds_intuit_url(client, settings):
    settings.QBO_CLIENT_ID = "cid"
    settings.QBO_REDIRECT_URI = "https://app.local/api/qbo/callback"

    school = School.objects.create(name="NG", code="ng")

    url = reverse("qbo-authorize") + f"?school=ng"
    res = client.get(url)
    assert res.status_code == 302
    assert "intuit.com" in res["Location"]
    assert "client_id=cid" in res["Location"]

@pytest.mark.django_db
def test_qbo_callback_exchanges_code_and_stores_tokens(client, settings, monkeypatch):
    settings.QBO_CLIENT_ID = "cid"
    settings.QBO_CLIENT_SECRET = "secret"
    settings.QBO_REDIRECT_URI = "https://app.local/api/qbo/callback"

    school = School.objects.create(name="NG", code="ng")

    # stub token exchange
    def fake_exchange(code):
        assert code == "authcode"
        return {
            "access_token":"at-new",
            "refresh_token":"rt-new",
            "expires_in": 3600,
        }
    monkeypatch.setattr("qbo.oauth.exchange_code_for_tokens", lambda code: fake_exchange(code))

    # build signed state with school
    state = signing.dumps({"school":"ng"}, salt="qbo")

    url = reverse("qbo-callback") + f"?code=authcode&state={state}&realmId=12345"
    res = client.get(url)
    assert res.status_code == 200

    conn = QBOConnection.objects.get(school=school)
    assert conn.realm_id == "12345"
    assert conn.access_token == "at-new"
    assert conn.refresh_token == "rt-new"