from .base import AggregatorAdapter
from .schemas import CanonicalPaymentEvent
from payments.enums import PaymentStatus, PaymentNarration
from webhooks.validators import verify_hmac

class SurepayAdapter(AggregatorAdapter):
    def verify_signature(self, body: bytes, signature: str | None) -> bool:
        return verify_hmac(self.account.webhook_secret or "", body, signature)
    def parse_webhook(self, payload: dict) -> dict:
        status_map = {
            "SUCCESS": PaymentStatus.SUCCEEDED.value,
            "SUCCEEDED": PaymentStatus.SUCCEEDED.value,
            "FAILED":   PaymentStatus.FAILED.value,
            "PENDING":  PaymentStatus.PENDING.value,
            "REFUNDED": PaymentStatus.REFUNDED.value,
        }
        narration_map = {
            "fees": PaymentNarration.FEES,
            "sports": PaymentNarration.SPORTS,
            "transport": PaymentNarration.TRANSPORT,
            "meals": PaymentNarration.MEALS,
            "books": PaymentNarration.BOOKS,
            "uniform": PaymentNarration.UNIFORM,
            "other": PaymentNarration.OTHER,
        }
        model = CanonicalPaymentEvent(
            event_id=payload.get("event_id"),
            external_txn_id=payload.get("transaction_id"),
            provider_student_id=payload.get("student_id"),
            amount=payload.get("amount"),
            currency=(payload.get("currency") or "UGX"),
            status=status_map.get((payload.get("status") or "").upper(), PaymentStatus.PENDING.value),
            narration=narration_map.get((payload.get("narration") or "").lower(), PaymentNarration.OTHER),
            raw=payload,
        )
        return model.model_dump()
