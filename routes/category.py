from app import db, app
from flask import jsonify, request
from models import Category

@app.route('/category/list', methods=['GET'])
def list_categories():
    categories = Category.query.all()
    result = []
    for c in categories:
        result.append({
            'id': c.id,
            'name': c.name,
            'created_at': c.created_at.strftime('%Y-%m-%d %I:%M %p')  # Changed format
        })
    return jsonify(result), 200


@app.route('/category/id/<int:id>', methods=['GET'])
def get_category_by_id(id):
    category = Category.query.get(id)
    if category:
        return jsonify({
            'id': category.id,
            'name': category.name,
            'created_at': category.created_at.strftime('%Y-%m-%d %I:%M %p')  # Changed format
        }), 200
    return jsonify({'error': 'Category not found'}), 404


@app.route('/category/create', methods=['POST'])
def create_category():
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({'error': 'Category name is required'}), 400

    existing_category = Category.query.filter_by(name=data['name']).first()
    if existing_category:
        return jsonify({'error': 'Category name already exists'}), 400

    new_category = Category(name=data['name'])
    db.session.add(new_category)
    db.session.commit()

    return jsonify({
        'status': 'Category created successfully!',
        'category': {
            'id': new_category.id,
            'name': new_category.name,
            'created_at': new_category.created_at.strftime('%B %d, %Y %I:%M %p')  # Changed format
        }
    }), 201


@app.route('/category/update', methods=['PUT', 'PATCH'])
def update_category():
    try:
        data = request.get_json(force=True)

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        if not data.get('id'):
            return jsonify({'error': 'Category id is required'}), 400

        if not data.get('name'):
            return jsonify({'error': 'Category name is required'}), 400
        try:
            category_id = int(data['id'])
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid category id'}), 400

        category = Category.query.get(category_id)
        if not category:
            return jsonify({'error': 'Category not found'}), 404

        duplicate = Category.query.filter(
            Category.name == data['name'],
            Category.id != category_id
        ).first()

        if duplicate:
            return jsonify({'error': 'Category name already exists'}), 400

        category.name = data['name']
        db.session.commit()

        return jsonify({
            'status': 'Category updated successfully!',
            'category': {
                'id': category.id,
                'name': category.name,
                'created_at': category.created_at.strftime('%Y-%m-%d %I:%M %p')
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/category/delete', methods=['DELETE'])
def delete_category():
    data = request.get_json()
    if not data or not data.get('id'):
        return jsonify({'error': 'Category id is required'}), 400

    category = Category.query.get(data['id'])
    if not category:
        return jsonify({'error': 'Category not found'}), 404

    db.session.delete(category)
    db.session.commit()
    return jsonify({
        'status': 'Category deleted successfully!',
        'deleted_category': {
            'id': category.id,
            'name': category.name,
            'created_at': category.created_at.strftime('%Y-%m-%d %I:%M %p')  # Changed format
        }
    }), 200