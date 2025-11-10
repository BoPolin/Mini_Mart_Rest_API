import os
from werkzeug.utils import secure_filename
from flask import request, jsonify, send_from_directory
from datetime import datetime
from app import app, db
from sqlalchemy import text


UPLOAD_FOLDER = 'static/uploads/products'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/product/list')
def list_products():
    sql = text("SELECT * FROM product")
    results = db.session.execute(sql).fetchall()
    products = []

    for row in results:
        row_dict = dict(row._mapping)

        if row_dict.get('image'):
            row_dict['image_url'] = f"http://127.0.0.1:5000/static/{row_dict['image']}"

        if row_dict.get('created_at'):
            created_at_value = row_dict['created_at']
            if isinstance(created_at_value, datetime):
                row_dict['created_at'] = created_at_value.strftime('%Y-%m-%d %I:%M %p')
            elif isinstance(created_at_value, str):
                try:
                    parsed_dt = datetime.fromisoformat(created_at_value)
                    row_dict['created_at'] = parsed_dt.strftime('%Y-%m-%d %I:%M %p')
                except ValueError:
                    row_dict['created_at'] = created_at_value

        products.append(row_dict)

    return jsonify({'total': len(products), 'products': products})


@app.route('/product/id/<int:id>')
def get_product_by_id(product_id):
    sql = text("SELECT * FROM product WHERE id = :id")
    result = db.session.execute(sql, {'id': product_id}).fetchone()

    if not result:
        return {'error': 'Product not found'}

    row_dict = dict(result._mapping)
    if row_dict.get('image'):
        row_dict['image_url'] = f"http://127.0.0.1:5000/static/{row_dict['image']}"
    return row_dict



@app.post('/product/create')
def create_product():
    name = request.form.get('name')
    category_id = request.form.get('category_id')
    price = request.form.get('price')
    stock = request.form.get('stock', 0)
    description = request.form.get('description')

    if not name:
        return jsonify({'error': 'Product name is required'}), 400
    if not category_id:
        return jsonify({'error': 'Category ID is required'}), 400
    if not price:
        return jsonify({'error': 'Product price is required'}), 400

    category_check = text("SELECT id FROM category WHERE id = :id")
    if not db.session.execute(category_check, {'id': category_id}).fetchone():
        return jsonify({'error': 'Category not found'}), 400

    image_filename = None
    if 'image' in request.files:
        file = request.files['image']
        if file and allowed_file(file.filename):
            timestamp_str = datetime.now().strftime('%Y%M%d_%H%M')
            filename = secure_filename(f"{timestamp_str}_{file.filename}")
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            image_filename = f"uploads/products/{filename}"
        elif file.filename != '':
            return jsonify({'error': 'Invalid file type'}), 400
    now = datetime.now()

    sql = text("""
        INSERT INTO product(name, price, stock, description, category_id, image, created_at)
        VALUES(:name, :price, :stock, :description, :category_id, :image, :created_at)
    """)
    result = db.session.execute(sql, {
        'name': name,
        'price': price,
        'stock': stock,
        'description': description,
        'category_id': category_id,
        'image': image_filename,
        'created_at': now
    })
    db.session.commit()

    last_id = result.lastrowid
    last_product = get_product_by_id(last_id)

    return jsonify({'status': 'Product created successfully', 'product': last_product}), 201

@app.put('/product/update')
def update_product():
    product_id = request.form.get('id')
    if not product_id:
        return jsonify({'error': 'Product id is required'}), 400

    existing_product = get_product_by_id(int(product_id))
    if existing_product.get('error'):
        return jsonify({'error': 'Product not found'}), 404

    update_fields = []
    params = {'id': product_id}

    for field in ['name', 'price', 'stock', 'description', 'category_id']:
        value = request.form.get(field)
        if value is not None:
            if field == 'category_id':
                category_check = text("SELECT id FROM category WHERE id = :id")  # Changed from 'categories' to 'category'
                if not db.session.execute(category_check, {'id': value}).fetchone():
                    return jsonify({'error': 'Category not found'}), 400
            update_fields.append(f"{field} = :{field}")
            params[field] = value

    if 'image' in request.files:
        file = request.files['image']
        if file and allowed_file(file.filename):
            old_image = existing_product.get('image')
            if old_image and os.path.exists(os.path.join('static', old_image)):
                os.remove(os.path.join('static', old_image))

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = secure_filename(f"{timestamp}_{file.filename}")
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            image_filename = f"uploads/products/{filename}"
            update_fields.append("image = :image")
            params['image'] = image_filename
        elif file.filename != '':
            return jsonify({'error': 'Invalid file type'}), 400

    if not update_fields:
        return jsonify({'error': 'No fields to update'}), 400

    sql = text(f"UPDATE product SET {', '.join(update_fields)} WHERE id = :id")  # Changed from 'products' to 'product'
    db.session.execute(sql, params)
    db.session.commit()

    updated_product = get_product_by_id(int(product_id))
    return jsonify({'status': 'Product updated successfully', 'product': updated_product})


@app.delete('/product/delete')
def delete_product():
    data = request.get_json(force=True)
    product_id = data.get('id') if data else None
    if not product_id:
        return jsonify({'error': 'Product id is required'}), 400

    product = get_product_by_id(int(product_id))
    if product.get('error'):
        return jsonify({'error': 'Product not found'}), 404

    if product.get('image'):
        image_path = os.path.join('static', product['image'])
        if os.path.exists(image_path):
            os.remove(image_path)

    sql = text("DELETE FROM product WHERE id = :id")
    db.session.execute(sql, {'id': int(product_id)})
    db.session.commit()

    return jsonify({'status': 'Product deleted successfully', 'product': product})


@app.route('/uploads/products/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)