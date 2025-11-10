from app import db, app
from sqlalchemy import text
from flask import jsonify, request
from sqlalchemy.exc import IntegrityError



@app.route('/invoice_detail/list')
def get_invoice_detail():
    sql = text("SELECT * FROM invoice_detail")
    result = db.session.execute(sql).fetchall()
    rows = []
    for row in result:
        rows.append({
            'id': row[0],
            'invoice_id': row[1],
            'product_id': row[2],
            'price': float(row[3]),
            'qty': row[4],
            'total': float(row[5])
        })
    return jsonify(rows)


@app.route('/invoice_detail/id/<path:id>')
def get_invoice_detail_by_id(id):
    sql = text("SELECT * FROM invoice_detail WHERE id = :id")
    result = db.session.execute(sql, {'id': id}).fetchone()
    if result:
        return {
            'id': result[0],
            'invoice_id': result[1],
            'product_id': result[2],
            'price': float(result[3]),
            'qty': result[4],
            'total': float(result[5])
        }
    return None


@app.post('/invoice_detail/create')
def create_invoice_detail():
    data = request.get_json()
    invoice_id = data.get('invoice_id')
    product_id = data.get('product_id')
    price = data.get('price')
    qty = data.get('qty')
    total = price * qty if price is not None and qty is not None else None

    if not data:
        return jsonify({'error': 'No invoice_detail data provided'}), 400
    if not invoice_id:
        return jsonify({'error': 'Invoice ID is required'}), 400
    if not product_id:
        return jsonify({'error': 'Product ID is required'}), 400
    if price is None:
        return jsonify({'error': 'Price is required'}), 400
    if qty is None:
        return jsonify({'error': 'Quantity is required'}), 400

    sql = text(
        "INSERT INTO invoice_detail(invoice_id, product_id, price, qty, total) "
        "VALUES(:invoice_id, :product_id, :price, :qty, :total)"
    )
    result = db.session.execute(sql, {
        'invoice_id': invoice_id,
        'product_id': product_id,
        'price': price,
        'qty': qty,
        'total': total
    })
    db.session.commit()
    last_id = result.lastrowid
    last_invoice_detail = get_invoice_detail_by_id(id=last_id)
    return jsonify({
        'status': 'created invoice_detail successfully!',
        'create_invoice_detail': last_invoice_detail
    })


@app.put('/invoice_detail/update')
def update_invoice_detail():
    data = request.get_json()
    if not data or not data.get('id'):
        return jsonify({'message': 'InvoiceDetail id is required!'}), 400

    # Check if invoice_detail exists
    check_sql = text("SELECT id FROM invoice_detail WHERE id = :id")
    existing = db.session.execute(check_sql, {'id': data['id']}).fetchone()
    if not existing:
        return jsonify({'message': 'InvoiceDetail not found!'}), 404

    update_fields = []
    params = {'id': data['id']}

    for field in ['invoice_id', 'product_id', 'price', 'qty']:
        if data.get(field) is not None:
            update_fields.append(f"{field} = :{field}")
            params[field] = data[field]

    if 'price' in data or 'qty' in data:
        price = data.get('price')
        qty = data.get('qty')
        if price is None or qty is None:
            current = db.session.execute(
                text("SELECT price, qty FROM invoice_detail WHERE id = :id"),
                {'id': data['id']}
            ).fetchone()
            price = price or current[0]
            qty = qty or current[1]
        update_fields.append("total = :total")
        params['total'] = price * qty

    sql = text(f"UPDATE invoice_detail SET {', '.join(update_fields)} WHERE id = :id")
    try:
        db.session.execute(sql, params)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({'message': 'Invalid foreign key (invoice_id or product_id)'}), 400

    updated_invoice_detail = get_invoice_detail_by_id(id=data['id'])
    return jsonify({
        'status': 'updated invoice_detail successfully!',
        'updated_invoice_detail': updated_invoice_detail
    })


@app.delete('/invoice_detail/delete')
def delete_invoice_detail():
    data = request.get_json()
    if not data or not data.get('id'):
        return jsonify({'message': 'InvoiceDetail id is required!'}), 400

    check_sql = text("SELECT id FROM invoice_detail WHERE id = :id")
    existing = db.session.execute(check_sql, {'id': data['id']}).fetchone()
    if not existing:
        return jsonify({'message': 'InvoiceDetail not found!'}), 404

    invoice_detail_info = get_invoice_detail_by_id(id=data['id'])
    sql = text("DELETE FROM invoice_detail WHERE id = :id")
    db.session.execute(sql, {'id': data['id']})
    db.session.commit()

    return jsonify({
        'status': 'invoice_detail deleted successfully!',
        'deleted_invoice_detail': invoice_detail_info
    })
