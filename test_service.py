import model


def test_returns_allocation():
    line = model.OrderLine('01', 'COMPLICATED-LAMP', 10)
    batch = model.Batch('b1', 'COMPLICATED-LAMP', 10, eta='2011-01-01')
    FakeRepository()
    pass


def test_error_for_invalid_sku():
    pass
