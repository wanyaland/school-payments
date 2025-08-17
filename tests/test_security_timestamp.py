import json, hmac, hashlib, pytest
from datetime import datetime, timezone
from django.urls import reverse
from schools.models import School
from payments.models import AggregatorAccount

@pytest.mark.django_db
def test_replay_protection_by_timestamp(client, settings):
    settings.WEBHOOK_TIMESTAMP_TOLERANCE = 60
    school = School.objects.create(name="Replay HS", code="replay")
    AggregatorAccount.objects.create(school=school, provider="SUREPAY", webhook_secret="sek", is_active=True)

    payload = {"event_id":"eold","transaction_id":"t","amount":1,"currency":"UGX","status":"SUCCESS","student_id":"stu-1"}
    body = json.dumps(payload).encode()
    sig = hmac.new(b"sek", body, hashlib.sha256).hexdigest()
    old_ts = str(int(datetime.now(timezone.utc).timestamp()) - 120)

    url = reverse("payment-webhook", kwargs={"provider":"SUREPAY"})
    res = client.post(url, data=body, content_type="application/json",
                      HTTP_X_SIGNATURE=sig, HTTP_X_SCHOOL_CODE=school.code, HTTP_X_TIMESTAMP=old_ts)
    assert res.status_code == 400
    assert "timestamp" in res.data["detail"].lower()