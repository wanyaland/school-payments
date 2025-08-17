from celery import shared_task
from django.conf import settings
from payments.models import Payment
from payments.enums import PaymentStatus
from .client import QBOClient

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def sync_payment_to_qbo(self, payment_id: int):
    if not getattr(settings, "QBO_SYNC_ENABLED", False):
        return
    p = Payment.objects.select_related("school").get(id=payment_id)
    if p.qbo_txn_id or p.status != PaymentStatus.SUCCEEDED.value:
        return
    if not hasattr(p.school, "qbo"):
        return

    client = QBOClient(p.school)
    client.ensure_token()
    cust = client.find_or_create_customer(p)
    result = client.create_sales_receipt(p, customer_id=str(cust.get("Id")))

    p.qbo_txn_id = str(result.get("Id")) if isinstance(result, dict) else p.qbo_txn_id
    p.qbo_txn_type = str(result.get("TxnType") or "SalesReceipt") if isinstance(result, dict) else p.qbo_txn_type
    p.qbo_customer_id = str(cust.get("Id")) if isinstance(cust, dict) else p.qbo_customer_id
    p.save(update_fields=["qbo_txn_id","qbo_txn_type","qbo_customer_id","updated_at"])