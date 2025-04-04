from flask import Blueprint, render_template, g, redirect, url_for, jsonify, session, request
from ..models.user import Creator
from ..models.transaction import Transaction
from ..services.transaction_service import TransactionService
from ..utils import login_required
from .. import db
import logging
from datetime import datetime, timedelta
import qrcode
import io
import base64
from ..models.withdrawal import Withdrawal
from ..services.withdrawal_service import WithdrawalService

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')
api = Blueprint('api', __name__, url_prefix='/api')

@dashboard_bp.route('/')
@login_required
def index():
    creator = g.creator or g.user
    if not creator:
        return redirect(url_for('auth.login'))
    
    # Get recent transactions    
    transactions = TransactionService.get_recent_transactions(creator.id, limit=10)
    
    # Debug log transactions
    logging.debug(f"Found {len(transactions)} transactions for creator {creator.id}")
    for t in transactions:
        logging.debug(f"Transaction {t.id}: amount={t.amount}, status={t.status}, created_at={t.created_at}")
    
    # Get transaction statistics
    stats = TransactionService.get_transaction_stats(creator.id)
    logging.debug(f"Transaction stats: {stats}")
    
    # Get withdrawal statistics
    withdrawal_stats = WithdrawalService.get_withdrawal_stats(creator.id)
    logging.debug(f"Withdrawal stats: {withdrawal_stats}")
    
    # Get recent withdrawals
    withdrawals = WithdrawalService.get_withdrawals(creator.id, limit=10)
    logging.debug(f"Found {len(withdrawals)} withdrawals for creator {creator.id}")
    
    # Calculate monthly stats
    monthly_stats = {
        'monthly_amount': 0,
        'monthly_count': 0
    }
    
    # Calculate average tip amount
    average_amount = 0
    if stats.get('total_tips', 0) > 0:
        average_amount = stats.get('total_amount', 0) / stats.get('total_tips', 1)
    
    # Generate tip link - use default if missing
    if hasattr(creator, 'tip_link_id') and creator.tip_link_id:
        tip_link = url_for('payments.tip_page', link_id=creator.tip_link_id, _external=True)
    else:
        tip_link = url_for('payments.tip_by_username', username=creator.username, _external=True)
    
    # Render dashboard template
    return render_template('dashboard/index.html',
                          transaction_history=transactions,
                          total_amount=stats.get('total_amount', 0),
                          transaction_count=stats.get('total_tips', 0),
                          monthly_amount=monthly_stats.get('monthly_amount', 0),
                          monthly_count=monthly_stats.get('monthly_count', 0),
                          average_amount=average_amount,
                          tip_link=tip_link,
                          withdrawals=withdrawals,
                          available_balance=withdrawal_stats['available_balance'],
                          pending_withdrawals=withdrawal_stats['pending_withdrawals'],
                          total_withdrawn=withdrawal_stats['total_withdrawn'])

@api.route('/transactions')
@login_required
def get_transactions():
    creator = g.creator or g.user
    if not creator:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Get transactions using service    
    transactions = TransactionService.get_recent_transactions(creator.id, limit=50)
    
    # Convert to JSON response
    return jsonify([{
        'id': t.id,
        'amount': t.amount,
        'status': t.status,
        'tipper_name': t.tipper_name,
        'message': t.message,
        'created_at': t.created_at.isoformat()
    } for t in transactions])

@api.route('/stats')
@login_required
def get_stats():
    creator = g.creator or g.user
    if not creator:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Get statistics using service
    stats = TransactionService.get_transaction_stats(creator.id)
    
    # Return JSON response
    return jsonify(stats)

@api.route('/overlay/info')
@login_required
def overlay_info():
    """Get overlay information for the creator"""
    creator = g.creator or g.user
    if not creator:
        return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401
    
    # Generate tip link
    if hasattr(creator, 'tip_link_id') and creator.tip_link_id:
        tip_link = url_for('payments.tip_page', link_id=creator.tip_link_id, _external=True)
    else:
        tip_link = url_for('payments.tip_by_username', username=creator.username, _external=True)
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(tip_link)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert QR code to base64
    buffer = io.BytesIO()
    img.save(buffer)
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    return jsonify({
        'status': 'success',
        'tipLink': tip_link,
        'qrCodeUrl': f"data:image/png;base64,{qr_code_base64}"
    }) 
    return jsonify(stats) 

@dashboard_bp.route('/withdrawals')
@login_required
def get_withdrawals():
    """Get updated withdrawals table HTML"""
    withdrawals = Withdrawal.query.filter_by(creator_id=g.creator.id).order_by(Withdrawal.created_at.desc()).all()
    return render_template('dashboard/_withdrawals_table.html', withdrawals=withdrawals) 