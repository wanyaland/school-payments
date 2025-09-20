# qbo/client.py
from django.utils import timezone
from django.conf import settings
from schools.models import QBOConnection
import qbo.oauth as qbo_oauth 
# Choose base by sandbox flag (optional for later)
API_BASE = "https://sandbox-quickbooks.api.intuit.com" if getattr(settings, "QBO_IS_SANDBOX", True) \
          else "https://quickbooks.api.intuit.com"

class QBOClient:
    def __init__(self, school):
        self.conn: QBOConnection = school.qbo

    def ensure_token(self):
        if not self.conn:
            return False
        if self.conn.token_expires_at and self.conn.token_expires_at > timezone.now():
            return True
        data = qbo_oauth.refresh_access_token(self.conn.refresh_token)  
        self.conn.access_token = data["access_token"]
        self.conn.refresh_token = data.get("refresh_token", self.conn.refresh_token)
        self.conn.token_expires_at = timezone.now() + timezone.timedelta(seconds=int(data.get("expires_in", 2500)))
        self.conn.save(update_fields=["access_token", "refresh_token", "token_expires_at"])
        return True

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.conn.access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def find_or_create_customer(self, payment) -> dict:
        return {"Id": getattr(payment, "qbo_customer_id", None) or "1"}

    def create_sales_receipt(self, payment, customer_id: str) -> dict:
        # Tests monkeypatch this. Keep raising by default.
        raise NotImplementedError()

    def create_payment(self, payment, customer_id: str, invoice_id: str) -> dict:
        # Create a payment against an invoice
        raise NotImplementedError()

    def find_open_invoices(self, customer_id: str) -> list:
        # Return list of open invoices for customer
        raise NotImplementedError()
