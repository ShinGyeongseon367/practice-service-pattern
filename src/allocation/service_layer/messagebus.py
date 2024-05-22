from typing import List, Dict, Callable, Type
from allocation.adapters import email
from allocation.domain import events
from allocation.service_layer import handler
from allocation.service_layer.unit_of_work import AbstractUnitOfWork


def handle(event: events.Event, uow: AbstractUnitOfWork):
    results = []
    queue = [event]
    while queue:
        event = queue.pop(0)
        for handler in HANDLERS[type(event)]:
            results.append(handler(event, uow))
            queue.extend(uow.collect_new_events())
    return results


def send_out_of_stock_notification(event: events.OutOfStock, uow):
    # uow 파라미터 충족 위해서 일단 넣어둠
    email.send_mail(
        "stock@made.com",
        f"Out of stock for {event.sku}",
    )


HANDLERS = {
    events.OutOfStock: [send_out_of_stock_notification],
    events.AllocationRequired: [handler.allocate],
    events.BatchCreated: [handler.add_batch],
    events.BatchQuantityChanged: [handler.change_batch_quantity],
}  # type: Dict[Type[events.Event], List[Callable]]
