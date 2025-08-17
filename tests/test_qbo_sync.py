# import pytest
# from decimal import Decimal
# from payments.models import AggregatorAccount, Payment
# from schools.models import School
# from django.conf import settings

# @pytest.mark.django_db
# def test_qbo_sync_on_succeeded(monkeypatch):
#     settings.QBO_SYNC_ENABLED = True
#     school = School.objects.create(name="Northgreen", code="ng")
#     AggregatorAccount.objects.create(school=school, provider="SUREPAY", webhook_secret="sek", is_active=True)
#     p = Payment.objects.create(school=school, provider="SUREPAY", external_txn_id="t100",
#                                amount=Decimal("250000"), currency="UGX", status="SUCCEEDED")

#     from qbo.client import QBOClient
#     called = {}
#     monkeypatch.setattr(
#     QBOClient,
#     "create_sales_receipt",
#     staticmethod(lambda pay: {"Id": "123", "TxnType": "SalesReceipt", "txn": called.setdefault("txn", pay.external_txn_id) or True}))


#     from qbo.tasks import sync_payment_to_qbo
#     sync_payment_to_qbo.run(payment_id=p.id)

#     p.refresh_from_db()
#     assert p.qbo_txn_id == "123"
#     assert p.qbo_txn_type == "SalesReceipt"
#     assert called["txn"] == "t100"


import pytest
from decimal import Decimal
from payments.models import AggregatorAccount, Payment
from schools.models import School

@pytest.mark.django_db
def test_qbo_sync_on_succeeded(monkeypatch):
    school = School.objects.create(name="Northgreen", code="ng")
    AggregatorAccount.objects.create(school=school, provider="SUREPAY", webhook_secret="sek", is_active=True)
    p = Payment.objects.create(school=school, provider="SUREPAY", external_txn_id="t100",
                               amount=Decimal("250000"), currency="UGX", status="SUCCEEDED")

    from qbo.client import QBOClient
    called = {}
    monkeypatch.setattr(
    QBOClient,
    "create_sales_receipt",
    staticmethod(lambda pay: {"Id": "123", "TxnType": "SalesReceipt", "txn": called.setdefault("txn", pay.external_txn_id) or True}))

    from qbo.tasks import sync_payment_to_qbo
    sync_payment_to_qbo.run(payment_id=p.id)

    p.refresh_from_db()
    assert p.qbo_txn_id == "123"
    assert p.qbo_txn_type == "SalesReceipt"
    assert called["txn"] == "t100"