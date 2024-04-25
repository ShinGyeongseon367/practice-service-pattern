import pytest

import model
from repository import FakeRepository


class FakeSession:
    committed = False

    def commit(self):
        self.committed = True

def test_returns_allocation():
    line = model.OrderLine('01', 'COMPLICATED-LAMP', 10)
    batch = model.Batch('b1', 'COMPLICATED-LAMP', 10, eta='2011-01-01')
    fake_repository = FakeRepository([batch])

    allocate = service.allocate(line, fake_repository, FakeSession())
    assert allocate == 'b1'


def test_error_for_invalid_sku():
    line = model.OrderLine("o1", "NONEXISTENTSKU", 10)
    batch = model.Batch("b1", "AREALSKU", 100, eta=None)
    repo = FakeRepository([batch])
    with pytest.raises(services.InvalidSku, match="Invalid sku NONEXISTENTSKU"):
        services.allocate(line, repo, FakeSession())


def test_commits():
    line = model.OrderLine('o1', 'OMINOUS-MIRROR', 10)
    batch = model.Batch('b1', 'OMINOUS-MIRROR', 100, eta=None)
    repo = FakeRepository([batch]) # 여기서 repo를 어떻게 사용하는건지 , 어떻게 동작하는건지 이게 가능함 ?
    session = FakeSession()
    services.allocate(line, repo, session)
    assert session.committed is True