from flask import request, jsonify
from app import db, app
from models import Customer


@app.route('/customer/list', methods=['GET'])
def list_customers():
    customers = Customer.query.all()
    result = []
    for c in customers:
        result.append({
            'id': c.id,
            'name': c.name,
            'phone': c.phone,
            'email': c.email,
            'created_at': c.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    return jsonify(result), 200

@app.route('/customer/id/<int:id>', methods=['GET'])
def get_customer_by_id(id):
    customer = Customer.query.get(id)
    if customer:
        return jsonify({
            'id': customer.id,
            'name': customer.name,
            'phone': customer.phone,
            'email': customer.email,
            'created_at': customer.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }), 200
    return jsonify({'error': 'Customer not found'}), 404


@app.route('/customer/create', methods=['POST'])
def create_customer():
    data = request.get_json()
    if not data or not data.get('name') or not data.get('email'):
        return jsonify({'error': 'Name and email are required'}), 400

    existing = Customer.query.filter_by(email=data['email']).first()
    if existing:
        return jsonify({'error': 'Email already exists'}), 400

    new_customer = Customer(
        name=data['name'],
        email=data['email'],
        phone=data.get('phone')
    )
    db.session.add(new_customer)
    db.session.commit()

    return jsonify({
        'status': 'Customer created successfully!',
        'customer': {
            'id': new_customer.id,
            'name': new_customer.name,
            'phone': new_customer.phone,
            'email': new_customer.email,
            'created_at': new_customer.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    }), 201


@app.route('/customer/update', methods=['PUT'])
def update_customer():
    data = request.get_json()
    if not data or not data.get('id'):
        return jsonify({'error': 'Customer id is required'}), 400

    customer = Customer.query.get(data['id'])
    if not customer:
        return jsonify({'error': 'Customer not found'}), 404

    if data.get('name'):
        customer.name = data['name']
    if data.get('email'):
        if Customer.query.filter(Customer.email==data['email'], Customer.id!=data['id']).first():
            return jsonify({'error': 'Email already exists'}), 400
        customer.email = data['email']
    if data.get('phone'):
        customer.phone = data['phone']

    db.session.commit()

    return jsonify({
        'status': 'Customer updated successfully!',
        'customer': {
            'id': customer.id,
            'name': customer.name,
            'phone': customer.phone,
            'email': customer.email,
            'created_at': customer.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    }), 200


@app.route('/customer/delete', methods=['DELETE'])
def delete_customer():
    data = request.get_json()
    if not data or not data.get('id'):
        return jsonify({'error': 'Customer id is required'}), 400

    customer = Customer.query.get(data['id'])
    if not customer:
        return jsonify({'error': 'Customer not found'}), 404

    db.session.delete(customer)
    db.session.commit()

    return jsonify({
        'status': 'Customer deleted successfully!',
        'deleted_customer': {
            'id': customer.id,
            'name': customer.name,
            'phone': customer.phone,
            'email': customer.email,
            'created_at': customer.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    }), 200
