# aggregators/schemas.py
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator

class CanonicalPaymentEvent(BaseModel):
    event_id: str = Field(min_length=1)
    external_txn_id: str = Field(min_length=1)
    provider_student_id: str = Field(min_length=1)
    amount: Decimal
    currency: str = Field(min_length=3, max_length=3)
    status: str
    raw: dict

    @field_validator("amount")
    @classmethod
    def amount_decimal(cls, v):
        from decimal import Decimal as D
        try: return D(str(v))
        except Exception as e: raise ValueError("amount must be a number") from e

    @field_validator("currency")
    @classmethod
    def currency_upper_3(cls, v):
        u = (v or "").upper()
        if len(u) != 3: raise ValueError("currency must be 3 letters")
        return u