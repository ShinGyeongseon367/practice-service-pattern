import datetime
from typing import List
from unittest import mock
import pytest
from allocation.adapters import repository
from allocation.domain import events
from allocation.service_layer import handlers, unit_of_work, messagebus


class FakeRepository(repository.AbstractRepository):
    def __init__(self, products):
        super().__init__()
        self._products = set(products)

    def _add(self, product):
        self._products.add(product)

    def _get(self, sku):
        return next((p for p in self._products if p.sku == sku), None)

    def _get_by_batchref(self, batchref):
        return next((
            p for p in self._products for b in p.batches
            if b.reference == batchref
        ), None)


class FakeUnitOfWork(unit_of_work.AbstractUnitOfWork):
    def __init__(self):
        self.products = FakeRepository([])
        self.committed = False

    def _commit(self):
        self.committed = True

    def rollback(self):
        pass


class FakeUnitOfWorkWithFakeMessageBus(FakeUnitOfWork):
    def __init__(self):
        super().__init__()
        self.events_published = [] # type: List[events.Event]

    def events_publish(self):
        for product in self.products.seen:
            while product.events:
                self.events_published.append(product.events.pop(0))



class TestAddBatch:
    def test_add_batch_for_new_product(self):
        uow = FakeUnitOfWork()
        # services.add_batch("b1", "CRUNCHY-ARMCHAIR", 100, None, uow)
        messagebus.handle(
            events.BatchCreated("b1", "CRUNCHY-ARMCHAIR", 100, None), uow
        )
        assert uow.products.get("CRUNCHY-ARMCHAIR") is not None
        assert uow.committed


    def test_add_batch_for_existing_product(self):
        uow = FakeUnitOfWork()
        # services.add_batch("b1", "GARISH-RUG", 100, None, uow)
        # services.add_batch("b2", "GARISH-RUG", 99, None, uow)
        messagebus.handle(events.BatchCreated("b1", "GARISH-RUG", 100, None), uow)
        messagebus.handle(events.BatchCreated("b2", "GARISH-RUG", 99, None), uow)
        assert "b2" in [b.reference for b in uow.products.get("GARISH-RUG").batches]


class TestAllocate:
    def test_allocate_returns_allocation(self):
        uow = FakeUnitOfWork()
        batch_created = events.BatchCreated("batch1", "COMPLICATED-LAMP", 100, None)
        handlers.add_batch(batch_created, uow)

        created_allocate = events.AllocationRequired("o1", "COMPLICATED-LAMP", 10)
        result = handlers.allocate(created_allocate, uow)
        assert result == "batch1"

    def test_allocate_errors_for_invalid_sku(self):
        uow = FakeUnitOfWork()
        handlers.add_batch(events.BatchCreated("b1", "AREALSKU", 100, None), uow)

        with pytest.raises(handlers.InvalidSku, match="Invalid sku NONEXISTENTSKU"):
            created_allocation = events.AllocationRequired("o1", "NONEXISTENTSKU", 10)
            handlers.allocate(created_allocation, uow)


def test_allocate_commits():
    uow = FakeUnitOfWork()
    created_batch_event = events.BatchCreated("b1", "OMINOUS-MIRROR", 100, None)
    handlers.add_batch(created_batch_event, uow)

    created_allocation_event = events.AllocationRequired("o1", "OMINOUS-MIRROR", 10)
    handlers.allocate(created_allocation_event, uow)
    assert uow.committed


def test_sends_email_on_out_of_stock_error():
    uow = FakeUnitOfWork()
    created_batch_event = events.BatchCreated("b1", "POPULAR-CURTAINS", 9, None)
    handlers.add_batch(created_batch_event, uow)

    with mock.patch("allocation.adapters.email.send_mail") as mock_send_mail:
        created_allocate_event = events.AllocationRequired("o1", "POPULAR-CURTAINS", 10)
        messagebus.handle(created_allocate_event, uow)
        assert mock_send_mail.call_args == mock.call(
            "stock@made.com",
            "Out of stock for POPULAR-CURTAINS",
        )


class TestCahngeBatchQuantity:
    def test_changes_available_quantity(self):
        uow = FakeUnitOfWork()
        messagebus.handle(
            # events.BatchQuantityChanged("batch1", "ADORABLE-SETTEE")
            events.BatchCreated("batch1", "ADORABLE-SETTEE", 100, None), uow
        )
        [batch] = uow.products._get("ADORABLE-SETTEE").batches
        assert batch.available_quantity == 100

        messagebus.handle(events.BatchQuantityChanged("batch1", 50), uow)
        assert batch.available_quantity == 50

    def test_reallocates_if_necessary(self):
        uow = FakeUnitOfWork()
        event_history = [
            events.BatchCreated("batch1", "INDIFFERENT-TABLE", 50, None),
            events.BatchCreated("batch2", "INDIFFERENT-TABLE", 50, datetime.date.today()),
            events.AllocationRequired("order1", "INDIFFERENT-TABLE", 20),
            events.AllocationRequired("order2", "INDIFFERENT-TABLE", 20),
        ]
        for e in event_history:
            messagebus.handle(e, uow)
        [batch1, batch2] = uow.products._get("INDIFFERENT-TABLE").batches
        assert batch1.available_quantity == 10
        assert batch2.available_quantity == 50

        messagebus.handle(events.BatchQuantityChanged("batch1", 25), uow)
        assert batch1.available_quantity == 5
        assert batch2.available_quantity == 30


def test_reallocate_if_necessary_isolated():
    uow = FakeUnitOfWorkWithFakeMessageBus()

    event_history = [
        events.BatchCreated("batch1", "INDIFFERENT-TABLE", 50, None),
        events.BatchCreated("batch2", "INDIFFERENT-TABLE", 50, datetime.date.today()),
        events.AllocationRequired("order1", "INDIFFERENT-TABLE", 20),
        events.AllocationRequired("order2", "INDIFFERENT-TABLE", 20),
    ]
    for e in event_history:
        messagebus.handle(e, uow)
    [batch1, batch2] = uow.products.get(sku="INDIFFERENT-TABLE").batches
    assert batch1.available_quantity == 10
    assert batch2.available_quantity == 50

    messagebus.handle(events.BatchQuantityChanged("batch1", 25), uow)

    uow.events_publish()
    [reallocation_event] = uow.events_published

    assert isinstance(reallocation_event, events.AllocationRequired)
    assert reallocation_event.orderid in {'order1', 'order2'}
    assert reallocation_event.sku == "INDIFFERENT-TABLE"
