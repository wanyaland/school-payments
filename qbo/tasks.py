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
    customer_id = str(cust.get("Id"))

    if p.qbo_invoice_id:
        # Pay existing invoice
        result = client.create_payment(p, customer_id, p.qbo_invoice_id)
        p.qbo_txn_type = "Payment"
    else:
        # Check for matching open invoice
        open_invoices = client.find_open_invoices(customer_id)
        matching_invoice = None
        for inv in open_invoices:
            if (inv.get("Balance", 0) == float(p.amount) and
                inv.get("Line", [{}])[0].get("Description", "").lower() == p.narration.lower()):
                matching_invoice = inv
                break
        if matching_invoice:
            p.qbo_invoice_id = str(matching_invoice["Id"])
            result = client.create_payment(p, customer_id, p.qbo_invoice_id)
            p.qbo_txn_type = "Payment"
        else:
            # Create sales receipt
            result = client.create_sales_receipt(p, customer_id)
            p.qbo_txn_type = "SalesReceipt"

    p.qbo_txn_id = str(result.get("Id")) if isinstance(result, dict) else p.qbo_txn_id
    p.qbo_customer_id = customer_id
    p.save(update_fields=["qbo_txn_id","qbo_txn_type","qbo_invoice_id","qbo_customer_id","updated_at"])