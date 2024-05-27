import logging
from typing import List, Dict, Callable, Type, Union
from allocation.adapters import email
from allocation.domain import events, commands
from allocation.service_layer import handlers, unit_of_work
from allocation.service_layer.unit_of_work import AbstractUnitOfWork

logger = logging.getLogger(__name__)

Message = Union[commands.Command, events.Event]


def handle_event(
        event: events.Event,
        queue: List[Message],
        uow: unit_of_work.AbstractUnitOfWork
):
    for handler in EVENT_HANDERS[type(event)]:
        try:
            logger.debug('handling event %s with handler %s', event, handler)
            handler(event, uow)
            queue.extend(uow.collect_new_events())
        except Exception as e:
            logger.exception('Exception handling event %s with handler %s', event, handler)
            continue


def handle_command(command: commands.Command, queue: List[commands.Command], uow: unit_of_work.AbstractUnitOfWork):
    logger.debug('handling command %s', command)
    try:
        handler = COMMAND_HANDERS[type(command)]
        result = handler(command, uow)
        queue.extend(uow.collect_new_events())
        return result
    except Exception as e:
        logger.exception('Exception handling command %s', command)
        raise


def handle(message: Message, uow: AbstractUnitOfWork):
    results = []
    queue = [message]
    while queue:
        message = queue.pop(0)
        if isinstance(message, events.Event):
            handle_event(message, queue, uow)
        elif isinstance(message, commands.Command):
            cmd_reuslt = handle_command(message, queue, uow)
            results.append(cmd_reuslt)
        else:
            raise Exception(f'{message} was not an Event or Command')

    return results


def send_out_of_stock_notification(event: events.OutOfStock, uow):
    # uow 파라미터 충족 위해서 일단 넣어둠
    email.send_mail(
        "stock@made.com",
        f"Out of stock for {event.sku}",
    )


EVENT_HANDERS = {
    events.OutOfStock: [handlers.send_out_of_stock_notification],
}  # type: Dict[Type[events.Event, List[Callable]]]


COMMAND_HANDERS = {
    commands.Command: [handlers.send_command],
    commands.Allocate: handlers.allocate,
    commands.CreateBatch: handlers.add_batch,
    commands.ChangeBatchQuantity: handlers.change_batch_quantity,

}  # type: Dict[Type[commands.Command], Callable]