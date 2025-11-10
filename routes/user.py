import re

from app import db, app
from sqlalchemy import text
from flask import jsonify, request
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from werkzeug.security import generate_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity



@app.route('/user/list')
def get_user():
    sql = text("SELECT id, username, email, password, role, created_at FROM user")
    result = db.session.execute(sql).fetchall()
    rows = []
    for row in result:
        rows.append({
            'id': row[0],
            'username': row[1],
            'email': row[2],
            'password': row[3],
            'role': row[4],
            'created_at': row[5]
        })
    return jsonify(rows)


# ===== GET USER BY ID =====
@app.route('/user/id/<int:id>')
def get_user_by_id(id):
    sql = text("SELECT id, username, email, password, role, created_at FROM user WHERE id = :id")
    result = db.session.execute(sql, {'id': id}).fetchone()
    if result:
        return {
            'id': result[0],
            'username': result[1],
            'email': result[2],
            'password': result[3],
            'role': result[4],
            'created_at': result[5]
        }
    return jsonify({'message': 'User not found'}), 404


# ===== CREATE USER =====
@app.post('/user/create')
def create_user():
    user = request.get_json()
    if not user:
        return jsonify({'error': 'No user data provided'}), 400

    username = user.get('username')
    email = user.get('email')
    password = user.get('password')
    role = user.get('role', 'user')

    # Basic validation
    if not username or not email or not password:
        return jsonify({'error': 'username, email, and password are required'}), 400

    # Check for existing username or email first
    check_sql = text("SELECT id FROM user WHERE email = :email OR username = :username")
    existing_user = db.session.execute(check_sql, {'email': email, 'username': username}).fetchone()
    if existing_user:
        return jsonify({'error': 'Username or email already exists'}), 400

    # Password validation (at least 8 chars, with uppercase, lowercase, number, special char)
    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters long'}), 400
    if not re.search(r'[A-Z]', password):
        return jsonify({'error': 'Password must contain at least one uppercase letter'}), 400
    if not re.search(r'[a-z]', password):
        return jsonify({'error': 'Password must contain at least one lowercase letter'}), 400
    if not re.search(r'\d', password):
        return jsonify({'error': 'Password must contain at least one number'}), 400
    if not re.search(r'[@$!%*?&]', password):
        return jsonify({'error': 'Password must contain at least one special character (@$!%*?&)'}), 400

    # Hash the password
    password_hash = generate_password_hash(password)

    # Insert user
    insert_sql = text("""
        INSERT INTO user (username, email, password, role, created_at)
        VALUES (:username, :email, :password, :role, :created_at)
        RETURNING id, username, email, role, created_at
    """)
    result = db.session.execute(insert_sql, {
        'username': username,
        'email': email,
        'password': password_hash,
        'role': role,
        'created_at': datetime.utcnow()
    })

    new_user = result.fetchone()
    db.session.commit()

    user_data = {
        'id': new_user.id,
        'username': new_user.username,
        'email': new_user.email,
        'role': new_user.role,
        'created_at': new_user.created_at
    }

    return jsonify({'status': 'User created successfully!', 'user': user_data}), 201

# ===== UPDATE USER =====
@app.put('/user/update')
def update_user():
    user = request.get_json()
    if not user or not user.get('id'):
        return jsonify({'message': 'User ID is required!'}), 400

    user_id = user.get('id')
    username = user.get('username')
    email = user.get('email')
    password = user.get('password')
    role = user.get('role')

    # Check if user exists
    check_sql = text("SELECT id FROM user WHERE id = :id")
    if not db.session.execute(check_sql, {'id': user_id}).fetchone():
        return jsonify({'message': 'User not found!'}), 404

    # Build dynamic update
    update_fields = []
    params = {'id': user_id}
    if username:
        update_fields.append("username = :username")
        params['username'] = username
    if email:
        update_fields.append("email = :email")
        params['email'] = email
    if password:
        update_fields.append("password = :password")
        params['password'] = generate_password_hash(password)
    if role:
        update_fields.append("role = :role")
        params['role'] = role

    if not update_fields:
        return jsonify({'message': 'At least one field to update is required!'}), 400

    sql = text(f"UPDATE user SET {', '.join(update_fields)} WHERE id = :id")
    try:
        db.session.execute(sql, params)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({'message': 'Username or email already exists!'}), 400

    updated_user = get_user_by_id(user_id)
    return jsonify({'status': 'User updated successfully!', 'user': updated_user})


# ===== DELETE USER =====
@app.delete('/user/delete')
def delete_user():
    user = request.get_json()
    if not user or not user.get('id'):
        return jsonify({'message': 'User ID is required!'}), 400

    user_id = user.get('id')

    # Check if user exists
    check_sql = text("SELECT id FROM user WHERE id = :id")
    if not db.session.execute(check_sql, {'id': user_id}).fetchone():
        return jsonify({'message': 'User not found!'}), 404

    # Get user data before deletion
    user_info = get_user_by_id(user_id)

    # Delete user
    delete_sql = text("DELETE FROM user WHERE id = :id")
    db.session.execute(delete_sql, {'id': user_id})
    db.session.commit()

    return jsonify({'status': 'User deleted successfully!', 'user': user_info})
