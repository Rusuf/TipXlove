from flask import Flask, redirect, url_for, render_template, make_response, g, session, send_from_directory
from flask_cors import CORS
from flask_migrate import Migrate
import os
from dotenv import load_dotenv
import logging
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect

# Import extensions
from .extensions import db, socketio, limiter, csrf

# Load environment variables from .env file
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
socketio = SocketIO()
limiter = Limiter(key_func=get_remote_address)
csrf = CSRFProtect()
migrate = Migrate()

def create_app(test_config=None):
    # Create and configure the app
    app = Flask(__name__, instance_relative_config=True, static_folder='../build', static_url_path='/')
    
    # Load configuration
    if test_config is None:
        # Load config from environment variables
        app.config.from_mapping(
            SECRET_KEY=os.environ.get('SECRET_KEY'),
            DATABASE=os.path.join(app.instance_path, 'streamtip.sqlite'),
            MPESA_API_URL=os.environ.get('MPESA_API_URL'),
            MPESA_INITIATOR_NAME=os.environ.get('MPESA_INITIATOR_NAME')
        )
    else:
        # Load the test config if passed in
        app.config.update(test_config)
        
    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # Configure database with absolute path
    db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'instance', 'streamtip.sqlite')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Configure session
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-for-development')
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour
    
    # Disable caching for all routes
    @app.after_request
    def add_header(response):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        return response
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Initialize M-Pesa configuration from environment
    app.config['MPESA_CONSUMER_KEY'] = os.environ.get('MPESA_CONSUMER_KEY', '')
    app.config['MPESA_CONSUMER_SECRET'] = os.environ.get('MPESA_CONSUMER_SECRET', '')
    app.config['MPESA_SHORTCODE'] = os.environ.get('MPESA_SHORTCODE', '')
    app.config['MPESA_PASSKEY'] = os.environ.get('MPESA_PASSKEY', '')
    app.config['MPESA_API_URL'] = os.environ.get('MPESA_API_URL', 'https://sandbox.safaricom.co.ke')
    
    # Add B2C specific configuration
    app.config['MPESA_INITIATOR_NAME'] = os.environ.get('MPESA_INITIATOR_NAME', 'testapi')
    app.config['MPESA_SECURITY_CREDENTIAL'] = os.environ.get('MPESA_SECURITY_CREDENTIAL', '')
    app.config['MPESA_B2C_SHORTCODE'] = os.environ.get('MPESA_B2C_SHORTCODE', app.config['MPESA_SHORTCODE'])
    app.config['MPESA_ENVIRONMENT'] = os.environ.get('MPESA_ENVIRONMENT', 'sandbox')
    
    # Set base URL for callbacks
    app.config['BASE_URL'] = os.environ.get('BASE_URL', 'http://localhost:5000')
    
    # Set test mode - use a single source of truth
    app.config['TEST_MODE'] = os.environ.get('TEST_MODE', 'true').lower() == 'true'
    app.config['MPESA_TEST_MODE'] = app.config['TEST_MODE']  # Sync with TEST_MODE
    
    # Debug log M-Pesa configuration
    logger.info("M-Pesa Configuration:")
    logger.info(f"Consumer Key: {app.config['MPESA_CONSUMER_KEY'][:10]}...")
    logger.info(f"Consumer Secret: {app.config['MPESA_CONSUMER_SECRET'][:10]}...")
    logger.info(f"Shortcode: {app.config['MPESA_SHORTCODE']}")
    logger.info(f"B2C Shortcode: {app.config['MPESA_B2C_SHORTCODE']}")
    logger.info(f"Initiator Name: {app.config['MPESA_INITIATOR_NAME']}")
    logger.info(f"Environment: {app.config['MPESA_ENVIRONMENT']}")
    logger.info(f"API URL: {app.config['MPESA_API_URL']}")
    logger.info(f"Test Mode: {app.config['TEST_MODE']}")
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)
    socketio.init_app(app, cors_allowed_origins="*")
    limiter.init_app(app)
    csrf.init_app(app)
    
    # Initialize M-Pesa client
    from .services.mpesa import MpesaClient
    app.mpesa = MpesaClient(app)
    
    # Import models
    from .models.user import Creator
    
    # Register blueprints
    from .routes.auth import auth_bp
    from .routes.dashboard import dashboard_bp, api
    from .routes.payments import payments_bp
    from .routes.withdrawals import withdrawals_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(api)
    app.register_blueprint(payments_bp)
    app.register_blueprint(withdrawals_bp)
    
    # Root route that can redirect based on authentication
    @app.before_request
    def load_logged_in_user():
        creator_id = session.get('creator_id')
        if creator_id is None:
            g.user = None
            g.creator = None
        else:
            creator = Creator.query.get(creator_id)
            if creator is None:
                g.user = None
                g.creator = None
                session.clear()
            else:
                g.user = creator  # For backward compatibility
                g.creator = creator
    
    # Root route
    @app.route('/')
    def index():
        # Always show the landing page regardless of login status
        return render_template('index.html')
        
    # Dashboard redirect
    @app.route('/go-to-dashboard')
    def go_to_dashboard():
        if g.creator or g.user:
            return redirect(url_for('dashboard.index'))
        else:
            return redirect(url_for('auth.login'))
    
    # Register CLI commands
    @app.cli.command('init-db')
    def init_db_command():
        """Initialize the database."""
        db.create_all()
        print('Initialized the database.')
    
    # Test endpoint
    @app.route('/api/test')
    def test():
        return {'message': 'Flask backend is running!'}
    
    # Serve React App
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve(path):
        if path != "" and os.path.exists(app.static_folder + '/' + path):
            return send_from_directory(app.static_folder, path)
        else:
            return send_from_directory(app.static_folder, 'index.html')
    
    return app 