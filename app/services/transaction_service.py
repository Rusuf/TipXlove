from .. import db, socketio
from ..models.transaction import Transaction
from ..models.user import Creator
from .socket_manager import SocketManager
import logging
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError
import random

class TransactionService:
    """Service for handling transactions and payments"""
    
    @classmethod
    def create_transaction(cls, creator_id, amount, phone_number, tipper_name='Anonymous', message=''):
        """
        Create a new transaction
        
        Args:
            creator_id: ID of the creator receiving the tip
            amount: Amount in KES
            phone_number: M-Pesa phone number
            tipper_name: Name of the tipper (optional)
            message: Tip message (optional)
            
        Returns:
            Transaction: The created transaction
        """
        try:
            creator = Creator.query.get(creator_id)
            if not creator:
                raise ValueError(f"Creator {creator_id} not found")

            transaction = Transaction(
                creator_id=creator_id,
                amount=float(amount),
                phone_number=phone_number,
                tipper_name=tipper_name,
                message=message,
                status='pending'
            )
            
            db.session.add(transaction)
            db.session.commit()
            
            logging.info(f"Created transaction {transaction.id} for creator {creator_id}")
            return transaction
            
        except IntegrityError as e:
            db.session.rollback()
            logging.error(f"Database error creating transaction: {str(e)}")
            raise
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error creating transaction: {str(e)}")
            raise

    @classmethod
    def update_transaction_status(cls, transaction_id, status, mpesa_receipt=None, mpesa_request_id=None):
        """
        Update a transaction status
        
        Args:
            transaction_id: ID of the transaction
            status: New status (pending, completed, failed, timeout)
            mpesa_receipt: M-Pesa receipt number (optional)
            mpesa_request_id: M-Pesa checkout request ID (optional)
            
        Returns:
            Transaction: The updated transaction
        """
        try:
            transaction = Transaction.query.get(transaction_id)
            if not transaction:
                raise ValueError(f"Transaction {transaction_id} not found")

            old_status = transaction.status
            transaction.status = status
            transaction.updated_at = datetime.utcnow()
            
            if mpesa_receipt:
                transaction.mpesa_receipt = mpesa_receipt
            if mpesa_request_id:
                transaction.mpesa_request_id = mpesa_request_id
                
            db.session.commit()
            
            # Emit socket events
            cls._emit_transaction_events(transaction, old_status)
            
            logging.info(f"Updated transaction {transaction_id} status to {status}")
            return transaction
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error updating transaction {transaction_id}: {str(e)}")
            raise

    @classmethod
    def find_by_mpesa_request(cls, mpesa_request_id):
        """
        Find a transaction by M-Pesa request ID
        
        Args:
            mpesa_request_id: M-Pesa checkout request ID
            
        Returns:
            Transaction: The transaction or None if not found
        """
        return Transaction.query.filter_by(mpesa_request_id=mpesa_request_id).first()

    @classmethod
    def _emit_transaction_events(cls, transaction, old_status):
        """
        Emit appropriate events for transaction status changes
        
        Args:
            transaction: The transaction object
            old_status: The previous status
        """
        if transaction.status == 'completed' and old_status != 'completed':
            # Emit new tip event
            tip_data = {
                'name': transaction.tipper_name,
                'amount': transaction.amount,
                'message': transaction.message,
                'mpesa_receipt': transaction.mpesa_receipt,
                'timestamp': transaction.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            }
            SocketManager.emit_new_tip(transaction.creator_id, tip_data)
            
        # Always emit status update
        SocketManager.emit_tip_status(
            transaction.creator_id,
            transaction.id,
            transaction.status,
            transaction=transaction
        )
        
        logging.debug(f"Emitted events for Tx ID {transaction.id} status change: {old_status} -> {transaction.status}")

    @classmethod
    def get_pending_transactions(cls, creator_id=None, hours=24):
        """
        Get pending transactions, optionally filtered by creator and time
        
        Args:
            creator_id: Creator ID to filter by (optional)
            hours: Number of hours to look back (default 24)
            
        Returns:
            list: List of pending transactions
        """
        query = Transaction.query.filter_by(status='pending')
        
        if creator_id:
            query = query.filter_by(creator_id=creator_id)
            
        if hours:
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            query = query.filter(Transaction.created_at >= cutoff)
            
        return query.all()

    @classmethod
    def timeout_stale_transactions(cls, hours=1):
        """
        Mark old pending transactions as timed out
        
        Args:
            hours: Number of hours after which to timeout (default 1)
            
        Returns:
            int: Number of transactions timed out
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        stale_transactions = Transaction.query.filter_by(status='pending')\
            .filter(Transaction.created_at <= cutoff)\
            .all()
            
        count = 0
        for transaction in stale_transactions:
            try:
                cls.update_transaction_status(transaction.id, 'timeout')
                count += 1
            except Exception as e:
                logging.error(f"Error timing out transaction {transaction.id}: {str(e)}")
                continue
                
        return count
        
    @classmethod
    def generate_mpesa_receipt_number(cls):
        """Generate a unique M-PESA receipt number"""
        prefix = 'PGH'
        random_part = ''.join(random.choices('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=7))
        return f"{prefix}{random_part}"

    @classmethod
    def process_successful_payment(cls, transaction, receipt_number=None, phone_number=None):
        """
        Process a successful payment
        
        Args:
            transaction: The transaction object
            receipt_number: M-Pesa receipt number (optional)
            phone_number: Phone number used for payment (optional)
            
        Returns:
            Transaction: The updated transaction
        """
        if not transaction:
            raise ValueError("Transaction is required")
            
        transaction.status = 'completed'
        transaction.updated_at = datetime.utcnow()
        
        # Generate receipt number if not provided
        if not receipt_number:
            receipt_number = cls.generate_mpesa_receipt_number()
        
        transaction.mpesa_receipt = receipt_number
            
        if phone_number:
            transaction.phone_number = phone_number
            
        db.session.commit()
        
        # Emit socket events
        cls._emit_transaction_events(transaction, 'pending')
        
        logging.debug(f"Processed successful payment for transaction {transaction.id}")
        return transaction
        
    @classmethod
    def process_failed_payment(cls, transaction, reason=None):
        """
        Process a failed payment
        
        Args:
            transaction: The transaction object
            reason: Failure reason (optional)
            
        Returns:
            Transaction: The updated transaction
        """
        if not transaction:
            raise ValueError("Transaction is required")
            
        transaction.status = 'failed'
        transaction.updated_at = datetime.utcnow()
        
        if reason:
            # Store reason in message if empty, otherwise append
            if not transaction.message:
                transaction.message = f"Failed: {reason}"
            else:
                transaction.message += f" (Failed: {reason})"
            
        db.session.commit()
        
        # Emit status update event
        SocketManager.emit_tip_status(
            transaction.creator_id,
            transaction.id,
            'failed'
        )
        
        logging.debug(f"Processed failed payment for transaction {transaction.id}: {reason}")
        return transaction
        
    @classmethod
    def get_recent_transactions(cls, creator_id, limit=10):
        """
        Get recent transactions for a creator
        
        Args:
            creator_id: ID of the creator
            limit: Maximum number of transactions to return
            
        Returns:
            list: List of transactions
        """
        return Transaction.query.filter_by(creator_id=creator_id)\
            .order_by(Transaction.created_at.desc())\
            .limit(limit)\
            .all()
            
    @classmethod
    def get_transaction_stats(cls, creator_id):
        """
        Get transaction statistics for a creator
        
        Args:
            creator_id: ID of the creator
            
        Returns:
            dict: Dictionary with statistics
        """
        transactions = Transaction.query.filter_by(creator_id=creator_id).all()
        
        # Calculate statistics
        completed_transactions = [t for t in transactions if t.status == 'completed']
        total_amount = sum(t.amount for t in completed_transactions)
        total_tips = len(completed_transactions)
        
        return {
            'total_amount': total_amount,
            'total_tips': total_tips,
            'total_transactions': len(transactions)
        } 