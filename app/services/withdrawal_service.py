from datetime import datetime
from sqlalchemy import func
from .. import db
from ..models.withdrawal import Withdrawal
from ..models.transaction import Transaction

class WithdrawalService:
    @staticmethod
    def get_available_balance(creator_id):
        """Calculate available balance for withdrawal"""
        # Get total tips
        total_tips = db.session.query(func.sum(Transaction.amount))\
            .filter(Transaction.creator_id == creator_id)\
            .filter(Transaction.status == 'completed')\
            .scalar() or 0.0
            
        # Get total withdrawals
        total_withdrawals = db.session.query(func.sum(Withdrawal.amount))\
            .filter(Withdrawal.creator_id == creator_id)\
            .filter(Withdrawal.status.in_(['completed', 'pending']))\
            .scalar() or 0.0
            
        return total_tips - total_withdrawals
    
    @staticmethod
    def create_withdrawal(creator_id, amount, phone_number):
        """Create a new withdrawal request"""
        available_balance = WithdrawalService.get_available_balance(creator_id)
        
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")
            
        if amount > available_balance:
            raise ValueError("Insufficient balance")
            
        withdrawal = Withdrawal(
            creator_id=creator_id,
            amount=amount,
            phone_number=phone_number,
            status='pending'
        )
        
        db.session.add(withdrawal)
        db.session.commit()
        
        return withdrawal
    
    @staticmethod
    def get_withdrawals(creator_id, limit=50):
        """Get recent withdrawals for a creator"""
        return Withdrawal.query\
            .filter_by(creator_id=creator_id)\
            .order_by(Withdrawal.created_at.desc())\
            .limit(limit)\
            .all()
    
    @staticmethod
    def process_withdrawal(withdrawal_id, success=True, receipt=None, failure_reason=None, test_mode=False):
        """Process a withdrawal completion or failure"""
        withdrawal = Withdrawal.query.get(withdrawal_id)
        if not withdrawal:
            raise ValueError("Withdrawal not found")
            
        if withdrawal.status != 'pending':
            if test_mode:
                # Allow reprocessing in test mode
                pass
            else:
                raise ValueError("Withdrawal already processed")
            
        if success:
            withdrawal.status = 'completed'
            withdrawal.mpesa_receipt = receipt or (f'TEST-{withdrawal.id}' if test_mode else None)
            withdrawal.completed_at = datetime.utcnow()
        else:
            withdrawal.status = 'failed'
            withdrawal.failure_reason = failure_reason
            
        db.session.commit()
        return withdrawal
    
    @staticmethod
    def get_withdrawal_stats(creator_id):
        """Get withdrawal statistics for a creator"""
        total_withdrawn = db.session.query(func.sum(Withdrawal.amount))\
            .filter(Withdrawal.creator_id == creator_id)\
            .filter(Withdrawal.status == 'completed')\
            .scalar() or 0.0
            
        pending_withdrawals = db.session.query(func.sum(Withdrawal.amount))\
            .filter(Withdrawal.creator_id == creator_id)\
            .filter(Withdrawal.status == 'pending')\
            .scalar() or 0.0
            
        return {
            'total_withdrawn': total_withdrawn,
            'pending_withdrawals': pending_withdrawals,
            'available_balance': WithdrawalService.get_available_balance(creator_id)
        } 