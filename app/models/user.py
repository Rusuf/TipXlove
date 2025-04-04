from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from .. import db
from sqlalchemy import Index, select, func, text
import uuid

class Creator(db.Model):
    """Model for content creators who can receive tips"""
    __tablename__ = 'creator'  # Explicitly set table name
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    phone_number = db.Column(db.String(20), unique=True, nullable=True)
    password_hash = db.Column(db.String(256), nullable=False)
    display_name = db.Column(db.String(80), nullable=True)
    active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    tip_link_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    # Relationships with explicit join conditions and back_populates
    transactions = db.relationship(
        'Transaction',
        back_populates='creator',
        lazy='dynamic',
        order_by='desc(Transaction.created_at)',
        cascade='all, delete-orphan'
    )
    
    withdrawals = db.relationship(
        'Withdrawal',
        backref='creator',
        lazy='dynamic',
        order_by='desc(Withdrawal.created_at)',
        cascade='all, delete-orphan'
    )
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_creator_username', 'username'),
        Index('idx_creator_tip_link', 'tip_link_id'),
        Index('idx_creator_phone', 'phone_number'),
        Index('idx_creator_email', 'email'),
    )

    def set_password(self, password):
        """Set hashed password"""
        if not password or len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if password matches hash"""
        if not password:
            return False
        return check_password_hash(self.password_hash, password)

    def update_last_login(self):
        """Update last login timestamp with transaction"""
        try:
            with db.session.begin_nested():
                self.last_login = datetime.utcnow()
                db.session.add(self)
        except:
            db.session.rollback()
            raise

    @staticmethod
    def format_phone_number(phone):
        """Format phone number to standard format"""
        if not phone:
            return None
            
        # Remove any spaces or special characters
        phone = ''.join(filter(str.isdigit, phone))
        
        # Handle different formats
        if phone.startswith('0'):  # Convert 07... to 2547...
            phone = '254' + phone[1:]
        elif not phone.startswith('254'):  # Add 254 prefix if not present
            phone = '254' + phone
            
        return phone if len(phone) == 12 else None

    @staticmethod
    def get_by_login(login):
        """Find user by either email or phone with proper escaping"""
        if not login:
            return None
            
        # Use parameterized queries to prevent SQL injection
        creator = Creator.query.filter(
            db.or_(
                Creator.email == login,
                Creator.phone_number == Creator.format_phone_number(login),
                Creator.username == login
            ),
            Creator.active == True
        ).first()
        
        return creator
        
    @property
    def display_name_or_username(self):
        """Get display name or fallback to username"""
        return self.display_name or self.username
        
    def get_balance_with_lock(self):
        """Calculate balances with proper transaction isolation"""
        with db.session.begin():
            # Lock the relevant transactions using SELECT FOR UPDATE
            stmt = text("""
                SELECT COALESCE(SUM(amount), 0) as completed
                FROM transaction 
                WHERE creator_id = :creator_id 
                AND status = 'completed' 
                AND withdrawn = false 
                FOR UPDATE
            """)
            completed_txns = db.session.execute(stmt, {'creator_id': self.id}).scalar() or 0
            
            stmt = text("""
                SELECT COALESCE(SUM(amount), 0) as withdrawn
                FROM withdrawal 
                WHERE creator_id = :creator_id 
                AND status = 'completed'
                FOR UPDATE
            """)
            withdrawn_amount = db.session.execute(stmt, {'creator_id': self.id}).scalar() or 0
            
            stmt = text("""
                SELECT COALESCE(SUM(amount), 0) as pending
                FROM transaction 
                WHERE creator_id = :creator_id 
                AND status = 'pending'
            """)
            pending_amount = db.session.execute(stmt, {'creator_id': self.id}).scalar() or 0
            
            return {
                'available': completed_txns - withdrawn_amount,
                'pending': pending_amount
            }
    
    @property
    def available_balance(self):
        """Calculate available balance with transaction isolation"""
        return self.get_balance_with_lock()['available']
        
    @property
    def pending_balance(self):
        """Calculate pending balance with transaction isolation"""
        return self.get_balance_with_lock()['pending']

    def __repr__(self):
        return f'<Creator {self.username}>' 