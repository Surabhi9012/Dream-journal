from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
import bcrypt
import jwt
import datetime
from flask import make_response
from models import User, DreamEntry, db_session
from functools import wraps
import os
import json
from dream_routes import dream_bp
from mood_insights import MoodInsights
from database import init_db
import logging
from sqlalchemy.exc import SQLAlchemyError

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__, 
    static_url_path='/static',
    static_folder='static',
    template_folder='templates')

# Configure CORS
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Generate secret key
app.config['SECRET_KEY'] = os.urandom(24)

# Initialize database
init_db()

# Register blueprints
app.register_blueprint(dream_bp)

# Explicit static file handling
@app.route('/static/<path:filename>')
def serve_static(filename):
    try:
        return send_from_directory(app.static_folder, filename)
    except Exception as e:
        logger.error(f"Error serving static file {filename}: {str(e)}")
        return f"Error serving static file: {str(e)}", 404

# Replace @app.before_first_request with this:
@app.before_request
def check_static_files():
    if not hasattr(app, '_static_files_checked'):
        required_files = ['main.js', 'style.css']
        for file in required_files:
            file_path = os.path.join(app.static_folder, file)
            if not os.path.exists(file_path):
                logger.warning(f"Static file {file} not found at {file_path}")
        app._static_files_checked = True
        
# Log static file requests
@app.after_request
def after_request(response):
    if request.path.startswith('/static/'):
        logger.info(f"Static file request: {request.path} - Status: {response.status_code}")
    return response

# Database session cleanup
@app.teardown_appcontext
def cleanup(resp_or_exc):
    db_session.remove()

# Authentication decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        new_token = None
        
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
                data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
                
                # Increase buffer time to 30 minutes
                exp_timestamp = datetime.datetime.fromtimestamp(data['exp'])
                time_until_expiry = exp_timestamp - datetime.datetime.utcnow()
                
                if time_until_expiry < datetime.timedelta(minutes=30):
                    # Generate new token with longer expiration
                    new_token = jwt.encode({
                        'username': data['username'],
                        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24),
                        'iat': datetime.datetime.utcnow()
                    }, app.config['SECRET_KEY'])
                
                current_user = db_session.query(User).filter_by(username=data['username']).first()
                if not current_user:
                    return jsonify({'message': 'User not found'}), 401
                    
                response = make_response(f(current_user, *args, **kwargs))
                if new_token:
                    response.headers['New-Token'] = new_token
                    response.headers['Access-Control-Expose-Headers'] = 'New-Token'
                return response
                
            except jwt.ExpiredSignatureError:
                return jsonify({'message': 'Token has expired'}), 401
            except jwt.InvalidTokenError:
                return jsonify({'message': 'Invalid token'}), 401
            except Exception as e:
                return jsonify({'message': str(e)}), 401
                
        return jsonify({'message': 'Token is missing'}), 401
    
    return decorated

# Routes
@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error rendering index: {str(e)}")
        return f"Error loading page: {str(e)}", 500

@app.route('/register', methods=['GET'])
def register_page():
    try:
        return render_template('register.html')
    except Exception as e:
        logger.error(f"Error rendering register page: {str(e)}")
        return f"Error loading page: {str(e)}", 500

@app.route('/register', methods=['POST'])
def register_user():
    try:
        data = request.get_json()
        
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({'message': 'Missing username or password'}), 400
            
        if db_session.query(User).filter_by(username=data['username']).first():
            return jsonify({'message': 'Username already exists'}), 400
            
        hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
        
        new_user = User(
            username=data['username'],
            password_hash=hashed_password
        )
        
        db_session.add(new_user)
        db_session.commit()
        logger.info(f"User created successfully: {new_user.username}")
        return jsonify({'message': 'User created successfully', 'user_id': new_user.user_id}), 201
        
    except Exception as e:
        db_session.rollback()
        logger.error(f"Error in register: {str(e)}")
        return jsonify({'message': f'Error creating user: {str(e)}'}), 500

@app.route('/login', methods=['GET'])
def login_page():
    try:
        return render_template('login.html')
    except Exception as e:
        logger.error(f"Error rendering login page: {str(e)}")
        return f"Error loading page: {str(e)}", 500

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        logger.debug(f"Login attempt for user: {data.get('username')}")
        
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({'message': 'Missing username or password'}), 400
            
        user = db_session.query(User).filter_by(username=data['username']).first()
        
        if user and bcrypt.checkpw(data['password'].encode('utf-8'), user.password_hash):
            token = jwt.encode({
                'username': user.username,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            }, app.config['SECRET_KEY'])
            
            logger.info(f"Successful login for user: {user.username}")
            return jsonify({
                'message': 'Login successful',
                'token': token,
                'user_id': user.user_id
            })
        
        logger.warning(f"Failed login attempt for user: {data.get('username')}")
        return jsonify({'message': 'Invalid credentials'}), 401
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({'message': f'Error during login: {str(e)}'}), 500

@app.route('/add_dream', methods=['POST'])
@token_required
def add_dream(current_user):
    try:
        data = request.get_json()
        
        if not data or 'dream_text' not in data:
            return jsonify({'message': 'Dream text is required'}), 400
            
        new_dream = DreamEntry(
            user_id=current_user.user_id,
            dream_text=data['dream_text'],
            mood_score=data.get('mood_score', 0.0)
        )
        
        try:
            db_session.add(new_dream)
            db_session.commit()
            logger.info(f"Dream added for user: {current_user.username}")
            
            response = jsonify({
                'message': 'Dream added successfully',
                'dream_id': new_dream.dream_id
            })
            return response, 201
            
        except SQLAlchemyError as e:
            db_session.rollback()
            logger.error(f"Database error while adding dream: {str(e)}")
            return jsonify({'message': 'Database error occurred'}), 500
            
    except Exception as e:
        db_session.rollback()
        logger.error(f"Error adding dream: {str(e)}")
        return jsonify({'message': 'An error occurred while saving the dream'}), 500
    
@app.route('/get_dreams', methods=['GET'])
@token_required
def get_dreams(current_user):
    try:
        dreams = db_session.query(DreamEntry).filter_by(user_id=current_user.user_id).all()
        logger.info(f"Retrieved dreams for user: {current_user.username}")
        return jsonify({
            'dreams': [{
                'dream_id': dream.dream_id,
                'dream_text': dream.dream_text,
                'mood_score': dream.mood_score,
                'timestamp': dream.timestamp.isoformat()
            } for dream in dreams]
        })
        
    except Exception as e:
        logger.error(f"Error retrieving dreams: {str(e)}")
        return jsonify({'message': f'Error retrieving dreams: {str(e)}'}), 500

@app.route('/get_insights', methods=['GET'])
@token_required
def get_insights(current_user):
    try:
        insights = MoodInsights(current_user.user_id)
        
        # Convert complex objects to JSON serializable formats if needed
        mood_trends = insights.get_mood_trends()
        if not isinstance(mood_trends, str):
            mood_trends = json.dumps(mood_trends)  # Serialize if it's an object/dict

        themes = insights.find_recurring_themes()
        if not isinstance(themes, str):
            themes = json.dumps(themes)  # Serialize if it's an object/dict

        feedback = insights.generate_feedback()
        if not isinstance(feedback, str):
            feedback = str(feedback)  # Convert to string as fallback
        
        logger.info(f"Generated insights for user: {current_user.username}")
        return jsonify({
            'mood_trends': mood_trends,
            'themes': themes,
            'feedback': feedback
        })
    except Exception as e:
        logger.error(f"Error generating insights: {str(e)}")
        return jsonify({'message': f'Error generating insights: {str(e)}'}), 500

@app.route('/refresh_token', methods=['POST'])
@token_required
def refresh_token(current_user):
    try:
        new_token = jwt.encode({
            'username': current_user.username,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1),
            'iat': datetime.datetime.utcnow()
        }, app.config['SECRET_KEY'])

        return jsonify({
            'token': new_token,
            'message': 'Token refreshed successfully'
        })
    except Exception as e:
        return jsonify({'message': str(e)}), 401
    
if __name__ == '__main__':
    # Ensure static folder exists
    os.makedirs(app.static_folder, exist_ok=True)

    # Start the app, bind to the correct host and port
    port = int(os.environ.get('PORT', 10000))  # Get port from environment variable or default to 10000
    app.run(host='0.0.0.0', port=port, debug=True)
