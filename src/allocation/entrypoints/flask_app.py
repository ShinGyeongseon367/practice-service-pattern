from datetime import datetime
from flask import Flask, request

from allocation.adapters import orm
from allocation.domain import events
from allocation.service_layer import handlers, unit_of_work, messagebus

app = Flask(__name__)
orm.start_mappers()


@app.route("/add_batch", methods=["POST"])
def add_batch():
    eta = request.json["eta"]

    if eta is not None:
        eta = datetime.fromisoformat(eta).date()

    event = events.BatchCreated(
        request.json["ref"],
        request.json["sku"],
        request.json["qty"],
        eta,
    )
    messagebus.handle(event, unit_of_work.SqlAlchemyUnitOfWork())
    return "OK", 201


@app.route("/allocate", methods=["POST"])
def allocate_endpoint():
    try:
        event = events.AllocationRequired(orderid=request.json["orderid"], sku=request["sku"], qty=request.json["qty"])
        results = messagebus.handle(event, unit_of_work.SqlAlchemyUnitOfWork())
        batch_ref = results.pop(0)
    except handlers.InvalidSku as e:
        return {"message": str(e)}, 400

    return {"batchref": batch_ref}, 201
