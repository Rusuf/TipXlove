from flask import Blueprint, request, jsonify, g, current_app
from .. import db, limiter
from ..models.withdrawal import Withdrawal
from ..services.withdrawal_service import WithdrawalService
from ..extensions import csrf
from functools import wraps
import logging
import json
from datetime import datetime
import re
import time

withdrawals_bp = Blueprint('withdrawals', __name__, url_prefix='/withdrawals')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not g.creator:
            return jsonify({'status': 'error', 'message': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

@withdrawals_bp.route('/initiate', methods=['POST'])
@login_required
@limiter.limit("3 per minute")
@csrf.exempt
def initiate_withdrawal():
    """Initiate a withdrawal request"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400

        amount = data.get('amount')
        phone_number = data.get('phone_number')

        if not amount or not phone_number:
            return jsonify({'status': 'error', 'message': 'Amount and phone number are required'}), 400

        if amount <= 0:
            return jsonify({'status': 'error', 'message': 'Invalid amount'}), 400

        # Validate phone number format (should be 254XXXXXXXXX)
        if not re.match(r'^254[0-9]{9}$', phone_number):
            return jsonify({'status': 'error', 'message': 'Invalid phone number format'}), 400

        # Check available balance
        available_balance = WithdrawalService.get_available_balance(g.creator.id)
        if amount > available_balance:
            return jsonify({'status': 'error', 'message': 'Insufficient balance'}), 400

        # Create withdrawal record
        withdrawal = Withdrawal(
            creator_id=g.creator.id,
            amount=amount,
            phone_number=phone_number,
            status='pending'
        )
        db.session.add(withdrawal)
        db.session.commit()

        # Log withdrawal creation
        logging.info(f"Created withdrawal {withdrawal.id} for creator {g.creator.id}")
        logging.info(f"Amount: {amount}, Phone: {phone_number}")

        # Initiate M-Pesa B2C payment
        try:
            response = current_app.mpesa.b2c_payment(
                phone_number=phone_number,
                amount=int(amount),
                remarks=f"StreamTip withdrawal #{withdrawal.id}"
            )

            logging.info(f"M-Pesa B2C response: {json.dumps(response, indent=2)}")

            if response.get('test_mode', False):
                # Handle test mode response
                receipt = f'TEST-{withdrawal.id}'
                WithdrawalService.process_withdrawal(
                    withdrawal.id,
                    success=True,
                    receipt=receipt,
                    test_mode=True
                )

                return jsonify({
                    'status': 'success',
                    'message': 'Test withdrawal completed successfully',
                    'withdrawal_id': withdrawal.id,
                    'test_mode': True,
                    'receipt': receipt
                }), 200

            elif 'ConversationID' in response:
                # Store the conversation ID for callback matching
                withdrawal.mpesa_request_id = response['ConversationID']
                db.session.commit()

                return jsonify({
                    'status': 'success',
                    'message': 'Withdrawal initiated successfully',
                    'withdrawal_id': withdrawal.id
                }), 200
            else:
                # Invalid response from M-Pesa
                WithdrawalService.process_withdrawal(
                    withdrawal.id,
                    success=False,
                    failure_reason='Invalid response from M-Pesa'
                )
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to initiate withdrawal'
                }), 500

        except Exception as e:
            # Handle M-Pesa API errors
            WithdrawalService.process_withdrawal(
                withdrawal.id,
                success=False,
                failure_reason=str(e)
            )
            logging.error(f"M-Pesa API error: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': 'Failed to process M-Pesa payment'
            }), 500

    except Exception as e:
        logging.error(f"Error processing withdrawal request: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while processing your request'
        }), 500

@withdrawals_bp.route('/b2c/result', methods=['POST'])
def b2c_result():
    """Handle M-Pesa B2C result callback"""
    try:
        data = request.get_json()
        if not data:
            logging.error("B2C result callback received empty data")
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400

        # Log callback data (sanitized)
        logging.info(f"B2C result callback data: {json.dumps(data)}")

        # Extract relevant data
        result = data.get('Result', {})
        conversation_id = result.get('ConversationID')
        result_code = result.get('ResultCode')
        result_desc = result.get('ResultDesc')

        if not conversation_id:
            logging.error("B2C result callback missing ConversationID")
            return jsonify({'status': 'error', 'message': 'Invalid callback data'}), 400

        # Find the withdrawal with retries
        max_retries = 3
        retry_delay = 1
        withdrawal = None
        last_error = None

        for attempt in range(max_retries):
            try:
                withdrawal = Withdrawal.query.filter_by(mpesa_request_id=conversation_id).first()
                if withdrawal:
                    break
                logging.warning(f"Withdrawal not found for conversation_id {conversation_id}, attempt {attempt + 1}/{max_retries}")
                time.sleep(retry_delay)
                retry_delay *= 2
            except Exception as e:
                last_error = e
                logging.error(f"Database error on attempt {attempt + 1}: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                raise

        if not withdrawal:
            logging.error(f"Withdrawal not found after {max_retries} attempts for conversation_id {conversation_id}")
            return jsonify({'status': 'error', 'message': 'Withdrawal not found'}), 404

        # Extract transaction receipt if successful
        receipt = None
        if result_code == 0:  # Success
            params = result.get('ResultParameters', {}).get('ResultParameter', [])
            for param in params:
                if param.get('Key') == 'TransactionReceipt':
                    receipt = param.get('Value')
                    break

        try:
            # Process the result
            if result_code == 0:  # Success
                WithdrawalService.process_withdrawal(
                    withdrawal.id,
                    success=True,
                    receipt=receipt
                )
                logging.info(f"Successfully processed withdrawal {withdrawal.id}")
            else:
                WithdrawalService.process_withdrawal(
                    withdrawal.id,
                    success=False,
                    failure_reason=result_desc or 'Payment failed'
                )
                logging.error(f"Failed to process withdrawal {withdrawal.id}: {result_desc}")

            return jsonify({'status': 'success'}), 200

        except Exception as e:
            logging.error(f"Error processing withdrawal {withdrawal.id}: {str(e)}")
            # Don't expose internal errors to M-Pesa
            return jsonify({'status': 'error', 'message': 'Internal processing error'}), 500

    except Exception as e:
        logging.error(f"Error processing B2C result callback: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while processing the callback'
        }), 500

@withdrawals_bp.route('/b2c/timeout', methods=['POST'])
def b2c_timeout():
    """Handle M-Pesa B2C timeout callback"""
    try:
        data = request.get_json()
        if not data:
            logging.error("B2C timeout callback received empty data")
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400
            
        # Log callback data
        logging.info(f"B2C timeout callback data: {json.dumps(data)}")
        
        # Extract conversation ID
        result = data.get('Result', {})
        conversation_id = result.get('ConversationID')
        
        if not conversation_id:
            logging.error("B2C timeout callback missing ConversationID")
            return jsonify({'status': 'error', 'message': 'Invalid callback data'}), 400
            
        # Find the withdrawal with retries
        max_retries = 3
        retry_delay = 1
        withdrawal = None
        last_error = None

        for attempt in range(max_retries):
            try:
                withdrawal = Withdrawal.query.filter_by(mpesa_request_id=conversation_id).first()
                if withdrawal:
                    break
                logging.warning(f"Withdrawal not found for conversation_id {conversation_id}, attempt {attempt + 1}/{max_retries}")
                time.sleep(retry_delay)
                retry_delay *= 2
            except Exception as e:
                last_error = e
                logging.error(f"Database error on attempt {attempt + 1}: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                raise

        if not withdrawal:
            logging.error(f"Withdrawal not found after {max_retries} attempts for conversation_id {conversation_id}")
            return jsonify({'status': 'error', 'message': 'Withdrawal not found'}), 404
            
        try:
            # Mark as failed due to timeout
            WithdrawalService.process_withdrawal(
                withdrawal.id,
                success=False,
                failure_reason='Transaction timed out'
            )
            logging.info(f"Marked withdrawal {withdrawal.id} as failed due to timeout")
            
            return jsonify({'status': 'success'}), 200
            
        except Exception as e:
            logging.error(f"Error processing withdrawal timeout {withdrawal.id}: {str(e)}")
            # Don't expose internal errors to M-Pesa
            return jsonify({'status': 'error', 'message': 'Internal processing error'}), 500
            
    except Exception as e:
        logging.error(f"Error processing B2C timeout callback: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while processing the callback'
        }), 500

@withdrawals_bp.route('/<int:creator_id>', methods=['GET'])
@login_required
def get_withdrawals(creator_id):
    """Get withdrawals for a creator"""
    if g.creator.id != creator_id:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
        
    try:
        withdrawals = WithdrawalService.get_withdrawals(creator_id)
        
        return jsonify({
            'status': 'success',
            'withdrawals': [{
                'id': w.id,
                'amount': float(w.amount),
                'status': w.status,
                'created_at': w.created_at.isoformat(),
                'completed_at': w.completed_at.isoformat() if w.completed_at else None,
                'receipt': w.receipt,
                'failure_reason': w.failure_reason
            } for w in withdrawals]
        }), 200
        
    except Exception as e:
        logging.error(f"Error getting withdrawals: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

@withdrawals_bp.route('/stats/<int:creator_id>', methods=['GET'])
@login_required
def get_stats(creator_id):
    """Get withdrawal statistics for a creator"""
    if g.creator.id != creator_id:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
        
    try:
        stats = WithdrawalService.get_withdrawal_stats(creator_id)
        return jsonify({
            'status': 'success',
            'stats': stats
        }), 200
        
    except Exception as e:
        logging.error(f"Error getting withdrawal stats: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500 