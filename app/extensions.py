from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
socketio = SocketIO() 
limiter = Limiter(
    key_func=get_remote_address,
    # Consider adding sensible default rate limits here
    # default_limits=["200 per day", "50 per hour"] 
)
csrf = CSRFProtect() 