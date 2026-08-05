"""Smoke test: package imports and core functions work."""

from axiara.core.costing import CostItem, total_cost
from axiara.core.quote import generate_quotation
from axiara.core.storage import DataLayer, LocalStorage, create_storage


def test_total_cost() -> None:
    items = [CostItem(name="steel", unit_cost=10.0, quantity=2)]
    assert total_cost(items) == 20.0


def test_generate_quotation() -> None:
    items = [CostItem(name="steel", unit_cost=10.0)]
    q = generate_quotation(items)
    assert q.cost == 10.0
    assert q.price == 10.0


def test_local_storage(tmp_path) -> None:
    store = LocalStorage(root=tmp_path)
    store.write(DataLayer.MARKET, "steel.json", '{"price": 12}')
    assert store.list(DataLayer.MARKET) == ["steel.json"]
    assert store.read(DataLayer.MARKET, "steel.json") == '{"price": 12}'


def test_storage_factory() -> None:
    store = create_storage("local")
    assert isinstance(store, LocalStorage)
