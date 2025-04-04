import hmac
import hashlib
import logging
import os

def verify_mpesa_signature(headers, payload, api_key):
    """Verify M-Pesa callback signature"""
    # Skip signature verification in sandbox mode
    if os.environ.get('MPESA_ENVIRONMENT') == 'sandbox':
        logging.debug("Skipping signature verification in sandbox mode")
        return True
        
    if 'x-mpesa-signature' not in headers:
        logging.warning("Missing M-Pesa signature in headers")
        return False
        
    received_signature = headers['x-mpesa-signature']
    calculated_signature = hmac.new(
        api_key.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    is_valid = hmac.compare_digest(received_signature, calculated_signature)
    if not is_valid:
        logging.warning("Invalid M-Pesa signature")
    
    return is_valid

def sanitize_payment_data(data):
    """Remove sensitive information from payment data before logging"""
    sensitive_fields = ['phone_number', 'account_number', 'security_credentials']
    sanitized = data.copy()
    
    for field in sensitive_fields:
        if field in sanitized:
            if isinstance(sanitized[field], str):
                sanitized[field] = '***' + sanitized[field][-4:] if len(sanitized[field]) > 4 else '****'
    
    return sanitized

class SecurityError(Exception):
    """Custom exception for security-related errors"""
    pass 