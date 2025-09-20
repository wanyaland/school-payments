# tests/test_qbo_sync.py (add this test)
import pytest
from django.utils import timezone
from schools.models import School
from payments.models import Payment
from payments.enums import PaymentStatus

@pytest.mark.django_db
def test_qbo_payment_applied_to_invoice(monkeypatch, settings):
    settings.QBO_SYNC_ENABLED = True
    from schools.models import QBOConnection
    school = School.objects.create(name="NG", code="ng")
    QBOConnection.objects.create(
        school=school, realm_id="12345",
        access_token="at", refresh_token="rt",
        token_expires_at=timezone.now()
    )

    p = Payment.objects.create(
        school=school, provider="SUREPAY", external_txn_id="t-inv-1",
        provider_student_id="prov-001", amount="100.00", currency="UGX",
        status=PaymentStatus.SUCCEEDED.value, raw={},
        # assume we’ve discovered/mapped the student’s open invoice in a prior step
        qbo_invoice_id="INV-999",  # <-- drives invoice payment path
        qbo_customer_id="CUST-1",
    )

    called = {}
    from qbo.client import QBOClient
    monkeypatch.setattr(QBOClient, "ensure_token", lambda self: True)
    # Stub payment creation call (new method below)
    def fake_create_payment(self, payment, customer_id, invoice_id):
        assert customer_id == "CUST-1"
        assert invoice_id == "INV-999"
        called["ok"] = payment.external_txn_id
        return {"Id": "PAY-123", "TxnType": "Payment"}
    monkeypatch.setattr(QBOClient, "create_payment", fake_create_payment)

    from qbo.tasks import sync_payment_to_qbo
    sync_payment_to_qbo(payment_id=p.id)

    assert called.get("ok") == "t-inv-1"
    p.refresh_from_db()
    assert p.qbo_txn_id == "PAY-123"
    assert p.qbo_txn_type == "Payment"
