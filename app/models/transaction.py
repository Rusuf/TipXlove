from datetime import datetime
from .. import db
from sqlalchemy import Index

class Transaction(db.Model):
    """Model for tips/payments received by creators"""
    __tablename__ = 'transactions'
    
    # Status Constants
    STATUS_PENDING = 'pending'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'
    STATUS_TIMEOUT = 'timeout'
    
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('creator.id'), nullable=False)
    status = db.Column(db.String(20), default=STATUS_PENDING)  # Use constant for default
    mpesa_receipt = db.Column(db.String(50), unique=True, nullable=True)
    mpesa_request_id = db.Column(db.String(50), unique=True, nullable=True)
    phone_number = db.Column(db.String(20), nullable=True)
    tipper_name = db.Column(db.String(100), nullable=True, default='Anonymous')
    message = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    withdrawn = db.Column(db.Boolean, default=False)
    withdrawal_id = db.Column(db.Integer, db.ForeignKey('withdrawal.id'), nullable=True)
    
    # Relationships
    creator = db.relationship('Creator', back_populates='transactions')
    withdrawal = db.relationship('Withdrawal', backref='transactions')
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_transaction_creator', 'creator_id'),
        Index('idx_transaction_status', 'status'),
        Index('idx_transaction_created', 'created_at'),
        Index('idx_transaction_mpesa', 'mpesa_receipt'),
        Index('idx_transaction_mpesa_request', 'mpesa_request_id'),
    )
    
    @property
    def is_completed(self):
        """Check if transaction is completed"""
        return self.status == self.STATUS_COMPLETED # Use constant
    
    @property
    def is_pending(self):
        """Check if transaction is pending"""
        return self.status == self.STATUS_PENDING # Use constant
    
    @property
    def is_failed(self):
        """Check if transaction is failed"""
        return self.status == self.STATUS_FAILED # Use constant
    
    @property
    def is_timeout(self):
        """Check if transaction has timed out"""
        return self.status == self.STATUS_TIMEOUT # Use constant
    
    def to_dict(self):
        """Convert transaction to dictionary for API responses"""
        return {
            'id': self.id,
            'amount': float(self.amount),
            'creator_id': self.creator_id,
            'status': self.status,
            'mpesa_receipt': self.mpesa_receipt,
            'tipper_name': self.tipper_name,
            'message': self.message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Transaction {self.id}: {self.amount} KES for Creator {self.creator_id}>' 