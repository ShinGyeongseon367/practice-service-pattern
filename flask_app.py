from flask import app, Flask, render_template, request, jsonify

import model
import repository


def get_session():
    pass


def is_valid_sku(line, batches):
    return line.sku in {b.sku for b in batches}


@app.App.route('/allocate', methods=['GET', 'POST'])
def allocate_endpoint():
    if request.method == 'GET':
        pass
    elif request.method == 'POST':
        session = get_session()
        batches = repository.SqlAlchemyRepository(session).list()
        line = model.OrderLine[request.json.get('order_id'), request.json.get('sku'), request.json.get('qty'),]

        if not is_valid_sku(line, batches):
            return jsonify({'message': f'Invalid sku{line.sku}'}), 400

        try:
            batchref = model.allocate(line, batches)
        except model.OutOfStock as e:
            return jsonify({'message': str(e)}), 400

        session.commit()
        return jsonify({'batchref': batchref}), 201
