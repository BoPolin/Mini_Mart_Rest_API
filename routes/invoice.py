from flask import request, jsonify
from app import db, app
from models import Invoice
from datetime import datetime


@app.route('/invoice/list', methods=['GET'])
def list_invoices():
    invoices = Invoice.query.all()
    result = []
    for inv in invoices:
        result.append({
            'id': inv.id,
            'user_id': inv.user_id,
            'customer_id': inv.customer_id,
            'total_amount': inv.total_amount,
            'status': inv.status,
            'date_time': inv.date_time.strftime('%Y-%m-%d %H:%M:%S')
        })
    return jsonify(result), 200


@app.route('/invoice/id/<int:id>', methods=['GET'])
def get_invoice_by_id(id):
    inv = Invoice.query.get(id)
    if not inv:
        return jsonify({'error': 'Invoice not found'}), 404

    details = []
    for d in inv.details:
        details.append({
            'id': d.id,
            'product_id': d.product_id,
            'product_name': d.product.name if d.product else None,
            'price': d.price,
            'qty': d.qty,
            'total': d.total
        })

    return jsonify({
        'id': inv.id,
        'user_id': inv.user_id,
        'customer_id': inv.customer_id,
        'total_amount': inv.total_amount,
        'status': inv.status,
        'date_time': inv.date_time.strftime('%Y-%m-%d %H:%M:%S'),
        'details': details
    }), 200


@app.route('/invoice/create', methods=['POST'])
def create_invoice():
    data = request.get_json()
    if not data or not data.get('user_id') or not data.get('total_amount'):
        return jsonify({'error': 'user_id and total_amount are required'}), 400

    customer_id = data.get('customer_id')
    status = data.get('status', 'completed')

    invoice = Invoice(
        user_id=data['user_id'],
        customer_id=customer_id,
        total_amount=data['total_amount'],
        status=status,
        date_time=datetime.utcnow()
    )
    db.session.add(invoice)
    db.session.commit()

    return jsonify({
        'status': 'Invoice created successfully!',
        'invoice': {
            'id': invoice.id,
            'user_id': invoice.user_id,
            'customer_id': invoice.customer_id,
            'total_amount': invoice.total_amount,
            'status': invoice.status,
            'date_time': invoice.date_time.strftime('%Y-%m-%d %H:%M:%S')
        }
    }), 201


@app.route('/invoice/update', methods=['PUT'])
def update_invoice():
    data = request.get_json()
    if not data or not data.get('id'):
        return jsonify({'error': 'Invoice id is required'}), 400

    invoice = Invoice.query.get(data['id'])
    if not invoice:
        return jsonify({'error': 'Invoice not found'}), 404

    if data.get('user_id'):
        invoice.user_id = data['user_id']
    if data.get('customer_id'):
        invoice.customer_id = data['customer_id']
    if data.get('total_amount'):
        invoice.total_amount = data['total_amount']
    if data.get('status'):
        invoice.status = data['status']

    db.session.commit()

    return jsonify({
        'status': 'Invoice updated successfully!',
        'invoice': {
            'id': invoice.id,
            'user_id': invoice.user_id,
            'customer_id': invoice.customer_id,
            'total_amount': invoice.total_amount,
            'status': invoice.status,
            'date_time': invoice.date_time.strftime('%Y-%m-%d %H:%M:%S')
        }
    }), 200


@app.route('/invoice/delete', methods=['DELETE'])
def delete_invoice():
    data = request.get_json()
    if not data or not data.get('id'):
        return jsonify({'error': 'Invoice id is required'}), 400

    invoice = Invoice.query.get(data['id'])
    if not invoice:
        return jsonify({'error': 'Invoice not found'}), 404

    db.session.delete(invoice)
    db.session.commit()

    return jsonify({
        'status': 'Invoice deleted successfully!',
        'deleted_invoice': {
            'id': invoice.id,
            'user_id': invoice.user_id,
            'customer_id': invoice.customer_id,
            'total_amount': invoice.total_amount,
            'status': invoice.status,
            'date_time': invoice.date_time.strftime('%Y-%m-%d %H:%M:%S')
        }
    }), 200