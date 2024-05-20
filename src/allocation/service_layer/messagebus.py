from typing import List, Dict, Callable, Type
from allocation.adapters import email
from allocation.domain import events
from allocation.service_layer.unit_of_work import AbstractUnitOfWork


def handle(event: events.Event, uow: AbstractUnitOfWork):
    queue = [event]
    while queue:
        event = queue.pop(0)
        for handler in HANDLERS[type(event)]:
            handler(event, uow=uow)
            queue.extend(uow.collect_new_events)



def send_out_of_stock_notification(event: events.OutOfStock):
    email.send_mail(
        "stock@made.com",
        f"Out of stock for {event.sku}",
    )


HANDLERS = {
    events.OutOfStock: [send_out_of_stock_notification],
}  # type: Dict[Type[events.Event], List[Callable]]
