from .. import db
from datetime import datetime
from sqlalchemy import Index

class Withdrawal(db.Model):
    """Model for creator withdrawals"""
    __tablename__ = 'withdrawal'  # Explicitly set table name
    
    __table_args__ = (
        Index('idx_withdrawal_creator', 'creator_id'),
        Index('idx_withdrawal_status', 'status'),
        Index('idx_withdrawal_created', 'created_at'),
        Index('idx_withdrawal_mpesa_request', 'mpesa_request_id'),
        db.UniqueConstraint('mpesa_request_id', name='uq_withdrawal_mpesa_request_id'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('creator.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed
    mpesa_receipt = db.Column(db.String(50), unique=True, nullable=True)
    mpesa_request_id = db.Column(db.String(50), nullable=True)  # For tracking B2C requests
    failure_reason = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    @property
    def date(self):
        """Format the date for display"""
        return self.created_at.strftime('%Y-%m-%d %H:%M')

    @property
    def receipt(self):
        """Get receipt URL if available"""
        if self.mpesa_receipt and self.status == 'completed':
            return f"/payments/receipt/{self.mpesa_receipt}"
        return None

    @property
    def is_completed(self):
        """Check if withdrawal is completed"""
        return self.status == 'completed'
    
    @property
    def is_pending(self):
        """Check if withdrawal is pending"""
        return self.status == 'pending'
    
    @property
    def is_failed(self):
        """Check if withdrawal is failed"""
        return self.status == 'failed'

    def __repr__(self):
        return f'<Withdrawal {self.id}: {self.amount} KES - {self.status}>' 