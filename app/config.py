import os

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # M-Pesa API Configuration
    MPESA_CONSUMER_KEY = os.environ.get('MPESA_CONSUMER_KEY', '')
    MPESA_CONSUMER_SECRET = os.environ.get('MPESA_CONSUMER_SECRET', '')
    MPESA_SHORTCODE = os.environ.get('MPESA_SHORTCODE', '')
    MPESA_PASSKEY = os.environ.get('MPESA_PASSKEY', '')
    MPESA_ENVIRONMENT = os.environ.get('MPESA_ENVIRONMENT', 'sandbox')
    
    # B2C Payment Configuration
    MPESA_INITIATOR_NAME = os.environ.get('MPESA_INITIATOR_NAME', 'testapi')
    MPESA_SECURITY_CREDENTIAL = os.environ.get('MPESA_SECURITY_CREDENTIAL', '')
    MPESA_B2C_SHORTCODE = os.environ.get('MPESA_B2C_SHORTCODE', '')  # Can be different from STK Push shortcode
    
    # Base URL for callbacks
    BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5000')
    
    # Test mode switch
    TEST_MODE = os.environ.get('TEST_MODE', 'False') == 'True'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///dev.db')
    
    # Override some settings for development
    MPESA_ENVIRONMENT = 'sandbox'
    TEST_MODE = True
    
    # Development B2C credentials (sandbox)
    MPESA_INITIATOR_NAME = 'testapi'
    MPESA_SECURITY_CREDENTIAL = 'Safaricom999!*!'  # Default sandbox credential
    MPESA_B2C_SHORTCODE = '600999'  # Default sandbox B2C shortcode

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    
    # Force SSL in production
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    
    # Ensure all required settings are set
    @classmethod
    def init_app(cls, app):
        required_settings = [
            'MPESA_CONSUMER_KEY',
            'MPESA_CONSUMER_SECRET',
            'MPESA_SHORTCODE',
            'MPESA_PASSKEY',
            'MPESA_INITIATOR_NAME',
            'MPESA_SECURITY_CREDENTIAL',
            'MPESA_B2C_SHORTCODE',
            'BASE_URL'
        ]
        
        missing = [key for key in required_settings if not app.config.get(key)]
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    TEST_MODE = True
    WTF_CSRF_ENABLED = False
    
    # Test B2C credentials
    MPESA_INITIATOR_NAME = 'testapi'
    MPESA_SECURITY_CREDENTIAL = 'Safaricom999!*!'
    MPESA_B2C_SHORTCODE = '600999'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
} 