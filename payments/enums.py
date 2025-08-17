from enum import Enum

class StrEnum(str, Enum):
    def __str__(self) -> str:
        return str(self.value)

class Currency(StrEnum):
    UGX = "UGX"
    USD = "USD"
class PaymentStatus(StrEnum):
    PENDING = "PENDING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"
class Aggregator(StrEnum):
    SUREPAY = "SUREPAY"