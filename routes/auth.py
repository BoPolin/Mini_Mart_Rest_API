from flask import request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app import app,db
from models import User



@app.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Username, email, and password are required'}), 400

    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 400

    user = User(
        username=data['username'],
        email=data['email'],
        role=data.get('role', 'user')
    )
    user.set_password(data['password'])

    db.session.add(user)
    db.session.commit()

    return jsonify({
        'message': 'User registered successfully',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role
        }
    }), 201


@app.route('/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()

        if not data or not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Username and password are required'}), 400
        user = User.query.filter_by(username=data['username']).first()

        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Invalid username or password'}), 401

        access_token = create_access_token(
            identity={
                'id': user.id,
                'username': user.username,
                'role': user.role
            }
        )
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'user': user.to_dict()
        })
    except Exception as e:
        return jsonify({'error': 'Login failed', 'details': str(e)}), 500


@app.route('/auth/logout', methods=['POST'])
@jwt_required()
def logout():
    try:
        current_user = get_jwt_identity()
        return jsonify({
            'message': 'Logout successful',
            'username': current_user.get('username')
        }), 200
    except Exception as e:
        return jsonify({'error': 'Logout failed', 'details': str(e)}), 500

@app.route('/auth/reset-password', methods=['POST'])
@jwt_required()
def reset_password():
    try:
        current_user = get_jwt_identity()
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400
        if not data.get('old_password'):
            return jsonify({'error': 'Old password is required'}), 400
        if not data.get('new_password'):
            return jsonify({'error': 'New password is required'}), 400

        user = User.query.get(current_user['id'])
        if not user:
            return jsonify({'error': 'User not found'}), 404

        if not user.check_password(data['old_password']):
            return jsonify({'error': 'Invalid old password'}), 401

        user.set_password(data['new_password'])
        db.session.commit()

        return jsonify({'message': 'Password reset successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Password reset failed', 'details': str(e)}), 500