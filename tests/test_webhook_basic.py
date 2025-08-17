import json, hmac, hashlib, pytest
from django.urls import reverse
from schools.models import School
from payments.models import AggregatorAccount, WebhookEvent, Payment

@pytest.mark.django_db
def test_webhook_accepts_signed_payload_and_writes_event(client):
    school = School.objects.create(name="Northgreen", code="ng")
    acct = AggregatorAccount.objects.create(school=school, provider="SUREPAY", webhook_secret="sek", is_active=True)

    payload = {"event_id":"e1","transaction_id":"t1","amount":250000,"currency":"UGX","status":"SUCCESS","student_id":"prov-001"}
    body = json.dumps(payload).encode()
    sig = hmac.new(acct.webhook_secret.encode(), body, hashlib.sha256).hexdigest()

    url = reverse("payment-webhook", kwargs={"provider":"SUREPAY"})
    res = client.post(url, data=body, content_type="application/json",
                      HTTP_X_SIGNATURE=sig, HTTP_X_SCHOOL_CODE=school.code)
    assert res.status_code == 200
    assert WebhookEvent.objects.filter(event_id="e1", aggregator_account=acct).exists()

@pytest.mark.django_db
def test_missing_provider_student_id_returns_400(client):
    school = School.objects.create(name="Northgreen", code="ng")
    acct = AggregatorAccount.objects.create(school=school, provider="SUREPAY", webhook_secret="sek", is_active=True)
    bad = {"event_id":"e1","transaction_id":"t1","amount":1000,"currency":"UGX","status":"SUCCESS"}
    body = json.dumps(bad).encode()
    sig = hmac.new(acct.webhook_secret.encode(), body, hashlib.sha256).hexdigest()

    url = reverse("payment-webhook", kwargs={"provider":"SUREPAY"})
    res = client.post(url, data=body, content_type="application/json",
                      HTTP_X_SIGNATURE=sig, HTTP_X_SCHOOL_CODE=school.code)
    assert res.status_code == 400
    assert "provider_student_id" in res.data["detail"].lower()