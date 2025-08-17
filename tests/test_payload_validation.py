import json, hmac, hashlib
import pytest
from django.urls import reverse
from payments.enums import Aggregator
from payments.models import AggregatorAccount
from schools.models import School

@pytest.mark.django_db
def test_invalid_payload_schema_returns_400(client):
    school = School.objects.create(name="Schema HS", code="schema")
    acct = AggregatorAccount.objects.create(
        school=school, provider=Aggregator.SUREPAY.value, webhook_secret="sekret", is_active=True
    )
    # missing required keys -> fails pydantic validation
    bad = {"foo": "bar"}
    body = json.dumps(bad).encode()
    sig = hmac.new(acct.webhook_secret.encode(), body, hashlib.sha256).hexdigest()

    url = reverse("payment-webhook", kwargs={"provider": "SUREPAY"})
    res = client.post(
    url, data=body, content_type="application/json",
    HTTP_X_SIGNATURE=sig, HTTP_X_SCHOOL_CODE=school.code,)
    
    assert res.status_code == 400
    assert "schema" in res.data["detail"].lower()   