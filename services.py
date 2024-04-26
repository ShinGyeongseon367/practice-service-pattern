from typing import List

import model
import repository
from model import OrderLine, Batch
from orm import batches


class InvalidSku(Exception):
    pass


def is_valid_sku(sku: str, batches: List[model.Batch]) -> bool:
    return sku in {batch.sku for batch in batches}


def allocate(line: OrderLine, repo: repository.AbstractRepository, session) -> str :
    batches: list[Batch] = repo.list()

    if is_valid_sku(line.sku):
        raise InvalidSku(f'invalid sku {line.sku}')

    batchref: str = model.allocate(line, batches)
    session.commit()
    return batchref
