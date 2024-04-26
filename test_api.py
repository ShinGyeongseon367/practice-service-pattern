import pytest
import requests

import config


def random_sku():
    pass


def random_batchref(param):
    pass


def random_orderid(param):
    pass


@pytest.mark.usefixtures('restart_api')
def test_user_restart(add_stock):
    sku = random_sku()
    batchref1 = random_batchref(1)
    batchref2 = random_batchref(2)

    orderid1 = random_orderid(1)
    orderid2 = random_orderid(2)

    add_stock([(batchref1, sku, 10, '2011-01-01'), (batchref2, sku, 10, '2011-01-01')])

    line1 = {'orderid': orderid1, 'sku': sku, 'qty': 10}
    line2 = {'orderid': orderid2, 'sku': sku, 'qty': 10}
    url = config.get_api_url()

    r = requests.post(f'{url}/allocate', json=line1)
    assert r.status_code == 201
    assert r.json()['batchref'] == batchref1

    r = requests.post(f'{url}/allocate', json=line2)
    assert r.status_code == 201
    assert r.json()['batchref'] == batchref2


@pytest.mark.usefixtures('restart_api')
def test_400_message_for_out_of_stock(add_stock):
    sku, small_batch, large_order = random_sku(), random_batchref(), random_orderid()
    add_stock([(small_batch, sku, 10, '2011-01-01')])
    data = {'orderid': large_order, 'sku': sku, 'qty': 20}
    url = config.get_api_url()
    response = requests.post(f'{url}/allocate', json=data)
    assert response.status_code == 400
    assert response.json()['message'] == f"Out of stock for sku {sku}"


@pytest.mark.usefixtures('restart_api')
def test_400_message_for_invalid_sku(add_stock):
    sku, batch, order_id = random_sku(), random_batchref(), random_orderid()
    data = {'orderid': order_id, 'sku': sku, 'qty': 20}
    url = config.get_api_url()
    response = requests.post(f'{url}/allocate', json=data)
    assert response.status_code == 400
    assert response.json()['message'] == f"Invalid sku {sku}"


@pytest.mark.usefixtures('restart_api')
def test_happy_path_returns_201_and_allocated_batch(add_stock):
    sku = random_sku()
    earlybatch = random_batchref(1)
    laterbatch = random_batchref(2)
    otherbatch = random_batchref(3)

    add_stock([
        (laterbatch, sku, 100, '2011-01-02'),
        (earlybatch, sku, 100, '2011-01-02'),
        (otherbatch, sku, 100, '2011-01-02')
    ])

    data = {'orderid': random_orderid(), 'sku': sku, 'qty': 3}

    url = config.get_api_url()
    r = requests.post(f'{url}/allocate', json=data)

    assert r.status_code == 201
    assert r.json()['batchref'] == earlybatch


@pytest.mark.usefixtures('restart_api')
def test_unhappy_path_and_return_400_and_error_message():
    unkown_sku = random_sku()
    orderid = random_orderid()
    data = {'orderid': orderid, 'sku': unkown_sku}
    url = config.get_api_url()
    r = requests.post(f'{url}/allocate', json=data)
    assert r.status_code == 400
    assert r.json()['message'] == f'Invalid sku {unkown_sku}'
