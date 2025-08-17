from importlib import import_module
from typing import Type
from .base import AggregatorAdapter
from .surepay import SurepayAdapter

_STATIC = {"SUREPAY": SurepayAdapter}

def _load_from_settings(provider: str) -> Type[AggregatorAdapter] | None:
    from django.conf import settings
    mapping = getattr(settings, "WEBHOOK_ADAPTERS", {}) or {}
    dotted = mapping.get(provider)
    if not dotted:
        return None
    module_path, cls_name = dotted.rsplit(".", 1)
    mod = import_module(module_path)
    return getattr(mod, cls_name)

def get_adapter_class(provider: str) -> Type[AggregatorAdapter]:
    key = (provider or "").upper()
    cls = _STATIC.get(key) or _load_from_settings(key)
    if not cls:
        raise ValueError(f"Unsupported provider: {provider}")
    return cls