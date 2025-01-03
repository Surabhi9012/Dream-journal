from functools import wraps
from flask import request, jsonify
import jwt
from models import User, db_session

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'message': 'Invalid token format'}), 401
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
            
        try:
            from app import app  # Import app here to avoid circular import
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = db_session.query(User).filter_by(username=data['username']).first()
            if not current_user:
                return jsonify({'message': 'User not found'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401
        except Exception as e:
            return jsonify({'message': f'Error: {str(e)}'}), 401
            
        return f(current_user, *args, **kwargs)
    
    return decorated