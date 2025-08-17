import json, hmac, hashlib, pytest
from django.urls import reverse
from schools.models import School, SchoolDirectoryConnection, Student, StudentIdMap
from payments.models import AggregatorAccount, Payment

@pytest.mark.django_db
def test_webhook_enriches_and_links_student_via_directory(client, monkeypatch):
    school = School.objects.create(name="Northgreen", code="ng")
    AggregatorAccount.objects.create(school=school, provider="SUREPAY", webhook_secret="sek", is_active=True)
    SchoolDirectoryConnection.objects.create(school=school, base_url="https://dir.example.com", api_key="k")

    # Stub the directory HTTP client to return a canonical id + name, using ONLY provider_student_id
    from school_api import client as dir_client
    def fake_get_by_provider_student_id(self, provider_student_id):
        assert provider_student_id == "prov-001"
        return {"school_student_id":"SCH-123","full_name":"Jane Doe"}
    monkeypatch.setattr(dir_client.SchoolAPIClient, "get_by_provider_student_id", fake_get_by_provider_student_id)

    payload = {"event_id":"e1","transaction_id":"t1","amount":250000,"currency":"UGX","status":"SUCCESS","student_id":"prov-001"}
    body = json.dumps(payload).encode()
    sig = hmac.new(b"sek", body, hashlib.sha256).hexdigest()

    url = reverse("payment-webhook", kwargs={"provider":"SUREPAY"})
    res = client.post(url, data=body, content_type="application/json",
                      HTTP_X_SIGNATURE=sig, HTTP_X_SCHOOL_CODE=school.code)
    assert res.status_code == 200

    # After the async task runs (Celery eager), the Payment should carry the canonical id and student link
    p = Payment.objects.get(external_txn_id="t1")
    assert p.school_student_id == "SCH-123"
    assert p.student and p.student.full_name == "Jane Doe"
    # Mapping table created for future fast lookups (no provider needed in key)
    assert StudentIdMap.objects.filter(school=school, provider_student_id="prov-001", student__school_student_id="SCH-123").exists()