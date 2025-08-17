import pytest
from payments.models import Payment
from payments.enums import PaymentStatus
from schools.models import School
from payments.models import AggregatorAccount
from django.utils import timezone

@pytest.mark.django_db
def test_qbo_sales_receipt_on_succeeded(monkeypatch, settings):
    settings.QBO_SYNC_ENABLED = True
    # Arrange: school + qbo connection
    from schools.models import QBOConnection
    school = School.objects.create(name="NG", code="ng")
    AggregatorAccount.objects.create(school=school, provider="SUREPAY", webhook_secret="sek", is_active=True)
    QBOConnection.objects.create(school=school, realm_id="12345", access_token="at", refresh_token="rt", token_expires_at=timezone.now())

    p = Payment.objects.create(
        school=school, provider="SUREPAY", external_txn_id="t1",
        provider_student_id="prov-001", amount=250000, currency="UGX",
        status=PaymentStatus.SUCCEEDED.value, raw={}
    )

    called = {}
    from qbo.client import QBOClient
    monkeypatch.setattr(QBOClient, "ensure_token", lambda self: True)
    monkeypatch.setattr(QBOClient, "find_or_create_customer", lambda self, pay: {"Id": "C1"})
    monkeypatch.setattr(QBOClient, "create_sales_receipt", lambda self, pay, customer_id: called.setdefault("ok", pay.external_txn_id) or {"Id":"SR1","TxnType":"SalesReceipt"})

    from qbo.tasks import sync_payment_to_qbo
    sync_payment_to_qbo(payment_id=p.id)

    assert called.get("ok") == "t1"

@pytest.mark.django_db
def test_qbo_skips_if_not_succeeded(settings):
    settings.QBO_SYNC_ENABLED = True
    from schools.models import QBOConnection
    school = School.objects.create(name="NG", code="ng")
    QBOConnection.objects.create(school=school, realm_id="12345", access_token="at", refresh_token="rt", token_expires_at=timezone.now())

    p = Payment.objects.create(
        school=school, provider="SUREPAY", external_txn_id="t2",
        provider_student_id="prov-002", amount=1000, currency="UGX",
        status="PENDING", raw={}
    )

    from qbo.tasks import sync_payment_to_qbo
    sync_payment_to_qbo(payment_id=p.id)  # should not error

    assert p.qbo_txn_id is None