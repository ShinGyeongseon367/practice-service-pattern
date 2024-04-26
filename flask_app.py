from flask import app, Flask, render_template, request, jsonify

import model
import repository
import services


def get_session():
    pass


@app.App.route('/allocate', methods=['GET', 'POST'])
def allocate_endpoint():
    if request.method == 'GET':
        pass
    elif request.method == 'POST':
        session = get_session()
        repo = repository.SqlAlchemyRepository(session)
        line = model.OrderLine(
            request.json['orderid'],
            request.json['sku'],
            request.json['qty']
        )

        try:
            batchref = services.allocate(line, repo, session)
        except (model.OutOfStock, services.InvalidSku) as e:
            return jsonify({'message': str(e)}), 400

        return jsonify({'batchref': batchref}), 201
