# aggregators/base.py
from abc import ABC, abstractmethod
class AggregatorAdapter(ABC):
    def __init__(self, account):
        self.account = account
    @abstractmethod
    def verify_signature(self, body: bytes, signature: str | None) -> bool: ...
    @abstractmethod
    def parse_webhook(self, payload: dict) -> dict: ...