from flask import Blueprint, request, jsonify, render_template, url_for, current_app, abort, g, Response, make_response
from marshmallow import ValidationError
from typing import Dict, Any, Tuple, Optional

from .. import db, socketio
from ..models.user import Creator
from ..services.transaction_service import TransactionService
from ..services.socket_manager import SocketManager
from ..models.transaction import Transaction
from ..schemas import PaymentSchema
from ..security import verify_mpesa_signature, sanitize_payment_data, SecurityError
from ..extensions import limiter
from ..extensions import csrf
import json
import logging
from sqlalchemy.exc import SQLAlchemyError
from functools import wraps
from ..services.mpesa import MpesaClient

payments_bp = Blueprint('payments', __name__, url_prefix='/payments')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not g.creator:
            return jsonify({'status': 'error', 'message': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

@payments_bp.route('/tip_page/<string:link_id>', methods=['GET'])
def tip_page(link_id: str) -> Response | Tuple[Response, int]:
    """Display the tipping page for a creator by link ID."""
    creator: Optional[Creator] = Creator.query.filter_by(tip_link_id=link_id).first()
    if not creator:
        abort(404, description="Creator not found for this tip link.")
    return render_template('tip_page.html', creator=creator)

@payments_bp.route('/tip/<string:username>', methods=['GET'])
def tip_by_username(username: str) -> Response | Tuple[Response, int]:
    """Display the tipping page for a creator by username."""
    creator: Optional[Creator] = Creator.query.filter_by(username=username).first()
    if not creator:
        abort(404, description=f"Creator '{username}' not found.")
    return render_template('tip_page.html', creator=creator)

@payments_bp.route('/overlay/<int:creator_id>', methods=['GET'])
def overlay(creator_id: int) -> Response | Tuple[Response, int]:
    """Display the overlay for a creator's stream."""
    creator: Optional[Creator] = Creator.query.get_or_404(creator_id)
    return render_template('overlay.html', creator=creator)

@payments_bp.route('/initiate_tip', methods=['POST'])
@limiter.limit("5 per minute")
@csrf.exempt
def initiate_tip() -> Tuple[Response, int]:
    """Initiate a tip payment after validation."""
    response = make_response()
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    
    if request.method == 'OPTIONS':
        return response
        
    if not request.is_json:
        return jsonify({'status': 'error', 'message': 'Request must be JSON'}), 415

    schema = PaymentSchema()
    try:
        # Validate and deserialize input
        validated_data = schema.load(request.json)
    except ValidationError as err:
        logging.warning(f"Payment validation failed: {err.messages}")
        return jsonify({
            'status': 'error',
            'message': 'Validation failed',
            'errors': err.messages
        }), 400

    # Proceed with validated data
    creator_id = validated_data.get('creator_id')
    amount = validated_data.get('amount')
    phone_number = validated_data.get('phone_number')
    tipper_name = validated_data.get('tipper_name', 'Anonymous') # Schema should handle default? 
    message = validated_data.get('message', '') # Schema should handle default?

    transaction: Optional[Transaction] = None
    try:
        transaction = TransactionService.create_transaction(
            creator_id=creator_id,
            amount=amount,
            phone_number=phone_number,
            tipper_name=tipper_name,
            message=message
        )
    except ValueError as e: # Specific error from service (e.g., invalid amount)
        logging.warning(f"Transaction creation ValueError: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 400
    except SQLAlchemyError as e: # Catch potential DB errors during creation
        logging.error(f"Database error creating transaction: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({'status': 'error', 'message': 'Could not save transaction'}), 500
    except Exception as e: # Catch other unexpected errors during creation
        logging.error(f"Unexpected error creating transaction: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Could not create transaction'}), 500

    # Ensure transaction was created
    if not transaction:
        logging.error(f"Transaction object is None after creation attempt for creator {creator_id}")
        return jsonify({'status': 'error', 'message': 'Transaction creation failed unexpectedly'}), 500

    # Generate callback URL (consider making this a helper or part of config)
    base_url = current_app.config.get('BASE_URL', request.host_url.rstrip('/'))
    callback_url = f"{base_url}/payments/callback"

    try:
        # Initiate M-Pesa payment
        mpesa = current_app.mpesa # Get MpesaClient instance
        response: Dict[str, Any] = mpesa.stk_push(
            phone_number=phone_number,
            amount=int(amount), # Ensure amount is integer for M-Pesa
            callback_url=callback_url,
            account_reference=f"TIP{transaction.id}",
            transaction_desc=f"Tip for creator {transaction.creator_id}" # Use ID for consistency
        )

        # Handle test mode response directly from MpesaClient
        if response.get('test_mode'):
            logging.info(f"M-Pesa Test Mode response for Tx ID {transaction.id}")
            transaction = TransactionService.process_successful_payment(
                transaction,
                receipt_number=f'TEST-{transaction.id}',
                phone_number=phone_number
            )
            return jsonify({
                'status': 'success',
                'message': 'Test payment successful',
                'transaction_id': transaction.id,
                'test_mode': True,
                'mpesa_receipt': transaction.mpesa_receipt,
                'amount': float(transaction.amount),
                'phone_number': transaction.phone_number,
                'timestamp': transaction.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            }), 200

        # Handle real M-Pesa response
        checkout_request_id = response.get('CheckoutRequestID')
        mpesa_response_code = response.get('ResponseCode') # Check M-Pesa specific response code

        if mpesa_response_code == '0' and checkout_request_id:
            logging.info(f"M-Pesa STK Push accepted for Tx ID {transaction.id}, CheckoutReqID: {checkout_request_id}")
            TransactionService.update_transaction_status(
                transaction.id,
                Transaction.STATUS_PENDING,
                mpesa_request_id=checkout_request_id
            )
            return jsonify({
                'status': 'success',
                'message': 'Payment initiated successfully',
                'transaction_id': transaction.id,
                'checkout_request_id': checkout_request_id
            }), 200
        else:
            # M-Pesa rejected the request before STK Push
            error_message = response.get('errorMessage', 'M-Pesa rejected the STK push request.')
            logging.error(f"M-Pesa STK Push initiation failed for Tx ID {transaction.id}. Response: {response}")
            TransactionService.update_transaction_status(transaction.id, Transaction.STATUS_FAILED)
            return jsonify({
                'status': 'error',
                'message': error_message
            }), 500 # Or 4xx depending on M-Pesa error meaning

    except Exception as e:
        logging.error(f"Error initiating M-Pesa payment for Tx ID {transaction.id}: {e}", exc_info=True)
        TransactionService.update_transaction_status(transaction.id, Transaction.STATUS_FAILED)
        # Provide a more generic error message to the client
        return jsonify({'status': 'error', 'message': 'Could not initiate payment with provider'}), 500

def _parse_mpesa_callback_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Safely parses the nested M-Pesa callback data."""
    callback_data = {}
    try:
        stk_callback = data.get('Body', {}).get('stkCallback', {})
        callback_data['checkout_request_id'] = stk_callback.get('CheckoutRequestID')
        callback_data['result_code'] = stk_callback.get('ResultCode')
        callback_data['result_desc'] = stk_callback.get('ResultDesc', '')
        callback_data['mpesa_receipt'] = None

        metadata = stk_callback.get('CallbackMetadata')
        if metadata and isinstance(metadata.get('Item'), list):
            for item in metadata['Item']:
                if isinstance(item, dict) and item.get('Name') == 'MpesaReceiptNumber':
                    callback_data['mpesa_receipt'] = item.get('Value')
                    break # Found the receipt number
    except Exception as e:
        logging.error(f"Error parsing M-Pesa callback structure: {e}", exc_info=True)
        # Return potentially partial data, let caller handle None values

    return callback_data

@payments_bp.route('/callback', methods=['POST'])
def mpesa_callback() -> Tuple[Response, int]:
    """Handle M-Pesa callback notification."""
    if not request.is_json:
        logging.warning("Received non-JSON M-Pesa callback")
        return jsonify({'ResultCode': 1, 'ResultDesc': 'Invalid request format'}), 415 # M-Pesa expects specific responses?

    data = request.json
    logging.info(f"M-Pesa callback received: {json.dumps(data)}") # Log full callback

    parsed_data = _parse_mpesa_callback_data(data)
    checkout_request_id = parsed_data.get('checkout_request_id')
    result_code = parsed_data.get('result_code')
    result_desc = parsed_data.get('result_desc')
    receipt = parsed_data.get('mpesa_receipt')

    if not checkout_request_id:
        logging.error("Missing CheckoutRequestID in parsed M-Pesa callback data")
        return jsonify({'ResultCode': 1, 'ResultDesc': 'Invalid callback data'}), 400

    try:
        # Find transaction using the CheckoutRequestID
        transaction = TransactionService.find_by_mpesa_request(checkout_request_id)
        if not transaction:
            logging.error(f"Transaction not found for CheckoutRequestID: {checkout_request_id}. Callback data: {data}")
            # Don't reveal transaction not found to potential attackers
            return jsonify({'ResultCode': 0, 'ResultDesc': 'Accepted'}), 200 # Acknowledge receipt even if Tx unknown?

        # Only process if the transaction is currently pending
        if transaction.status != Transaction.STATUS_PENDING:
            logging.warning(f"Received callback for already processed Tx ID {transaction.id} (status: {transaction.status}). Ignoring.")
            return jsonify({'ResultCode': 0, 'ResultDesc': 'Accepted'}), 200

        # Process result based on M-Pesa ResultCode
        if result_code == 0:  # Success
            logging.info(f"M-Pesa callback success for Tx ID {transaction.id}. Receipt: {receipt}")
            transaction = TransactionService.process_successful_payment(
                transaction,
                receipt_number=receipt,
                phone_number=transaction.phone_number
            )
        else:
            # Payment failed or cancelled by user, etc.
            logging.warning(f"M-Pesa callback failure for Tx ID {transaction.id}. Code: {result_code}, Desc: {result_desc}")
            # Map M-Pesa failure codes to your internal statuses if needed (e.g., timeout vs explicit failure)
            transaction = TransactionService.process_failed_payment(
                transaction,
                reason=result_desc
            )

        # Acknowledge successful processing to M-Pesa
        return jsonify({'ResultCode': 0, 'ResultDesc': 'Accepted'}), 200

    except SQLAlchemyError as e:
        logging.error(f"Database error processing callback for CheckoutReqID {checkout_request_id}: {e}", exc_info=True)
        db.session.rollback()
        # Respond with error to M-Pesa? Check their spec.
        return jsonify({'ResultCode': 1, 'ResultDesc': 'Internal Server Error'}), 500
    except Exception as e:
        logging.error(f"Unexpected error processing callback for CheckoutReqID {checkout_request_id}: {e}", exc_info=True)
        # Respond with error to M-Pesa?
        return jsonify({'ResultCode': 1, 'ResultDesc': 'Internal Server Error'}), 500

@payments_bp.route('/check_status/<int:transaction_id>', methods=['GET'])
# @login_required? Or should this be public?
def check_status(transaction_id: int) -> Tuple[Response, int]:
    """Check the status of a transaction, optionally querying M-Pesa if pending."""
    try:
        transaction: Optional[Transaction] = Transaction.query.get(transaction_id)
        if not transaction:
            return jsonify({'status': 'error', 'message': 'Transaction not found'}), 404

        current_status = transaction.status
        receipt = transaction.mpesa_receipt

        # For final statuses, return immediately
        if current_status in [Transaction.STATUS_COMPLETED, Transaction.STATUS_FAILED, Transaction.STATUS_TIMEOUT]:
            logging.debug(f"Returning final status '{current_status}' for Tx ID {transaction_id}")
            return jsonify({
                'status': 'success',
                'transaction_status': current_status,
                'mpesa_receipt': receipt
            }), 200

        # If pending, try querying M-Pesa (rate limit this?)
        if current_status == Transaction.STATUS_PENDING and transaction.mpesa_request_id:
            logging.info(f"Status check for pending Tx ID {transaction_id}, querying M-Pesa.")
            try:
                mpesa = current_app.mpesa
                response = mpesa.query_transaction(transaction.mpesa_request_id)

                # Process the query result
                mpesa_result_code = response.get('ResultCode')
                mpesa_result_desc = response.get('ResultDescription', '')

                if mpesa_result_code == '0': # Transaction successful
                    logging.info(f"M-Pesa query confirms success for Tx ID {transaction_id}. Response: {response}")
                    # Receipt might be in response, double check M-Pesa docs for query response structure
                    queried_receipt = response.get('MpesaReceiptNumber') # Example field name
                    transaction = TransactionService.process_successful_payment(
                        transaction,
                        receipt_number=queried_receipt or transaction.mpesa_receipt,
                        phone_number=transaction.phone_number
                    )
                    current_status = Transaction.STATUS_COMPLETED # Update status for current response
                elif mpesa_result_code: # Any non-zero M-Pesa code indicates failure/issue
                    logging.warning(f"M-Pesa query indicates failure/issue for Tx ID {transaction_id}. Code: {mpesa_result_code}, Desc: {mpesa_result_desc}")
                    # Decide if this maps to 'failed' or 'timeout' or remains 'pending'
                    # For now, map to failed
                    transaction = TransactionService.process_failed_payment(
                        transaction,
                        reason=mpesa_result_desc
                    )
                    current_status = Transaction.STATUS_FAILED # Update status for current response
                else:
                    # M-Pesa query response format unexpected or indicates pending/unknown
                    logging.warning(f"Unexpected M-Pesa query response for Tx ID {transaction_id}: {response}")
                    # Keep status as pending

            except Exception as e:
                logging.error(f"Unexpected error querying M-Pesa status for Tx ID {transaction.id}: {e}", exc_info=True)
                # Don't update transaction status on query error, return current pending status

        # Return the potentially updated status with full transaction data
        return jsonify({
            'status': 'success',
            'transaction_status': current_status,
            'mpesa_receipt': transaction.mpesa_receipt,
            'amount': float(transaction.amount),
            'phone_number': transaction.phone_number,
            'timestamp': transaction.updated_at.strftime('%Y-%m-%d %H:%M:%S') if transaction.updated_at else None
        }), 200

    except SQLAlchemyError as e:
        logging.error(f"Database error checking status for Tx ID {transaction_id}: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Database error'}), 500
    except Exception as e:
        logging.error(f"Unexpected error checking status for Tx ID {transaction_id}: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'An unexpected server error occurred'}), 500

@payments_bp.route('/transactions/<int:creator_id>', methods=['GET'])
@login_required
def get_transactions(creator_id):
    """Get transactions for a creator with proper authentication"""
    if g.creator.id != creator_id:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
        
    try:
        transactions = TransactionService.get_recent_transactions(creator_id, limit=50)
        
        return jsonify({
            'status': 'success',
            'transactions': [{
                'id': t.id,
                'amount': t.amount,
                'status': t.status,
                'tipper_name': t.tipper_name,
                'message': t.message,
                'created_at': t.created_at.isoformat()
            } for t in transactions]
        }), 200
    
    except Exception as e:
        logging.error(f"Error getting transactions: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

@payments_bp.route('/stats/<int:creator_id>', methods=['GET'])
@login_required
def get_stats(creator_id):
    """Get payment statistics for a creator with proper authentication"""
    if g.creator.id != creator_id:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
        
    try:
        stats = TransactionService.get_transaction_stats(creator_id)
        return jsonify({
            'status': 'success',
            'stats': stats
        }), 200
    
    except Exception as e:
        logging.error(f"Error getting transaction stats: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

# Remove test endpoint in production
if current_app and current_app.config.get('TEST_MODE', False):
    @payments_bp.route('/test_callback/<transaction_id>', methods=['GET'])
    def test_callback(transaction_id):
        """Simulate an M-Pesa callback for testing"""
        abort(404)  # Disabled for security 