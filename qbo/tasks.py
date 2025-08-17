from celery import shared_task
from django.db import transaction
from payments.models import Payment
from payments.enums import PaymentStatus

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def sync_payment_to_qbo(self, payment_id: int):
    p = Payment.objects.get(id=payment_id)
    # idempotent: skip if already synced or not successful
    if p.qbo_txn_id or p.status != PaymentStatus.SUCCEEDED.value:
        return

    # In tests, QBOClient.create_sales_receipt is monkeypatched, so import locally
    from qbo.client import QBOClient
    client = QBOClient()
    result = client.create_sales_receipt(p)

    with transaction.atomic():
        p.qbo_txn_id = str(result.get("Id") or result.get("id"))
        p.qbo_txn_type = str(result.get("TxnType") or result.get("type") or "SalesReceipt")
        p.save(update_fields=["qbo_txn_id", "qbo_txn_type", "updated_at"])