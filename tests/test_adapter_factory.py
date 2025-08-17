import pytest
from payments.enums import Aggregator
from aggregators.factory import get_adapter_class

@pytest.mark.parametrize("provider,klass", [
    (Aggregator.SUREPAY.value, "SurepayAdapter"),
])
def test_adapter_factory(provider, klass):
    cls = get_adapter_class(provider)
    assert cls.__name__ == klass