import requests
import base64
from datetime import datetime
import logging
from functools import wraps
import uuid
import time
import os
import json

def handle_api_errors(func):
    """Decorator to handle M-Pesa API errors consistently"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.RequestException as e:
            logging.error(f"Network error in {func.__name__}: {str(e)}")
            raise Exception(f"Network error while processing payment: {str(e)}")
        except Exception as e:
            logging.error(f"Error in {func.__name__}: {str(e)}")
            raise
    return wrapper

class MpesaClient:
    """Client for interacting with M-Pesa API"""
    
    def __init__(self, app=None):
        self.app = app
        self.token = None
        self.token_expiry = None
        
        # Credentials and configuration
        self.consumer_key = None
        self.consumer_secret = None
        self.business_shortcode = None
        self.passkey = None
        self.environment = None
        self.test_mode = None
        self.base_url = None
        self.callback_base_url = None
        
        # B2C payment specific settings
        self.initiator_name = None
        self.security_credential = None
        self.b2c_shortcode = None
        self.b2c_queue_timeout_url = None
        self.b2c_result_url = None
        
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Initialize the M-Pesa client with Flask app config"""
        self.consumer_key = app.config['MPESA_CONSUMER_KEY']
        self.consumer_secret = app.config['MPESA_CONSUMER_SECRET']
        self.business_shortcode = app.config['MPESA_SHORTCODE']
        self.passkey = app.config['MPESA_PASSKEY']
        self.environment = app.config.get('MPESA_ENVIRONMENT', 'sandbox')
        self.test_mode = app.config.get('TEST_MODE', False)
        
        # Fix the base URL and endpoints
        if self.environment == 'sandbox':
            self.base_url = 'https://sandbox.safaricom.co.ke'
        else:
            self.base_url = 'https://api.safaricom.co.ke'
            
        self.auth_url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
        self.stkpush_url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
        self.b2c_url = f"{self.base_url}/mpesa/b2c/v1/paymentrequest"

        # Get the callback base URL from config
        self.callback_base_url = app.config.get('BASE_URL', 'http://localhost:5000')
        
        # Get B2C specific settings
        self.initiator_name = app.config.get('MPESA_INITIATOR_NAME')
        self.security_credential = app.config.get('MPESA_SECURITY_CREDENTIAL')
        self.b2c_shortcode = app.config.get('MPESA_B2C_SHORTCODE', self.business_shortcode)
        
        # Set up B2C callback URLs
        self.b2c_queue_timeout_url = f"{self.callback_base_url}/withdrawals/b2c/timeout"
        self.b2c_result_url = f"{self.callback_base_url}/withdrawals/b2c/result"
        
        # Log configuration
        logging.info("M-Pesa Client Configuration:")
        logging.info(f"Environment: {self.environment}")
        logging.info(f"Test Mode: {self.test_mode}")
        logging.info(f"Base URL: {self.base_url}")
        logging.info(f"B2C Result URL: {self.b2c_result_url}")
        logging.info(f"B2C Timeout URL: {self.b2c_queue_timeout_url}")
        
        app.mpesa = self

    def get_auth_token(self):
        """Get OAuth token, using cached version if still valid"""
        if self.token and self.token_expiry and time.time() < self.token_expiry:
            return self.token

        auth_string = base64.b64encode(
            f"{self.consumer_key}:{self.consumer_secret}".encode()
        ).decode()

        try:
            response = requests.get(
                self.auth_url,
                headers={'Authorization': f'Basic {auth_string}'},
                timeout=10
            )
            response.raise_for_status()
            result = response.json()
            
            self.token = result['access_token']
            self.token_expiry = time.time() + (result['expires_in'] - 60)  # Buffer of 60s
            
            return self.token
            
        except Exception as e:
            logging.error(f"Error getting auth token: {str(e)}")
            raise Exception("Could not authenticate with M-Pesa")

    @handle_api_errors
    def stk_push(self, phone_number, amount, callback_url, account_reference=None, transaction_desc=None):
        """
        Initiate STK Push payment
        
        Args:
            phone_number: Customer phone number (format: 254XXXXXXXXX)
            amount: Amount to charge
            callback_url: URL for M-Pesa to send payment notification
            account_reference: Reference for the transaction (optional)
            transaction_desc: Description of the transaction (optional)
            
        Returns:
            dict: M-Pesa API response
        """
        try:
            # Get access token
            access_token = self.get_auth_token()
            if not access_token:
                logging.error("Failed to get M-Pesa access token")
                raise Exception("Could not authenticate with M-Pesa")

            # Generate password and timestamp
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            password = base64.b64encode(
                (self.business_shortcode + self.passkey + timestamp).encode()
            ).decode('utf-8')

            # Prepare headers
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }

            logging.info(f"Initiating STK push for amount {amount} to {phone_number}")
            logging.debug(f"Using callback URL: {callback_url}")

            payload = {
                "BusinessShortCode": self.business_shortcode,
                "Password": password,
                "Timestamp": timestamp,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": int(float(amount)),  # Ensure integer amount
                "PartyA": phone_number,
                "PartyB": self.business_shortcode,
                "PhoneNumber": phone_number,
                "CallBackURL": callback_url,
                "AccountReference": account_reference or f"TIP{int(time.time())}",
                "TransactionDesc": transaction_desc or "StreamTip Payment"
            }

            # Make request with retries
            max_retries = 2
            retry_delay = 1
            last_error = None

            for attempt in range(max_retries + 1):
                try:
                    logging.info(f"STK push attempt {attempt + 1}/{max_retries + 1}")
                    response = requests.post(
                        self.stkpush_url,
                        json=payload,
                        headers=headers,
                        timeout=30
                    )
                    
                    logging.debug(f"M-Pesa response status: {response.status_code}")
                    logging.debug(f"M-Pesa response headers: {dict(response.headers)}")
                    
                    try:
                        response_text = response.text
                        logging.debug(f"M-Pesa response body: {response_text}")
                    except Exception as e:
                        logging.error(f"Could not read response text: {e}")
                    
                    response.raise_for_status()
                    result = response.json()

                    if 'CheckoutRequestID' not in result:
                        logging.error(f"Invalid M-Pesa response: {result}")
                        raise Exception("Invalid response from M-Pesa: missing CheckoutRequestID")

                    logging.info(f"STK push successful: {result['CheckoutRequestID']}")
                    return result

                except requests.exceptions.RequestException as e:
                    last_error = e
                    logging.error(f"Network error on attempt {attempt + 1}: {e}")
                    if attempt < max_retries:
                        logging.info(f"Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        retry_delay *= 2
                        continue
                    break
                except Exception as e:
                    last_error = e
                    logging.error(f"Error on attempt {attempt + 1}: {e}")
                    if attempt < max_retries:
                        logging.info(f"Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        retry_delay *= 2
                        continue
                    break

            error_msg = str(last_error) if last_error else "Unknown error"
            logging.error(f"All STK push attempts failed: {error_msg}")
            raise last_error or Exception("Failed to process STK push")
            
        except Exception as e:
            logging.error(f"STK push failed: {e}", exc_info=True)
            raise

    @handle_api_errors
    def query_transaction(self, checkout_request_id):
        """
        Query the status of a transaction
        
        Args:
            checkout_request_id: M-Pesa checkout request ID
            
        Returns:
            dict: Transaction status from M-Pesa
        """
        if self.test_mode:
            return {
                'test_mode': True,
                'ResponseCode': '0',
                'ResponseDescription': 'The service request has been accepted successsfully',
                'MerchantRequestID': 'test_merchant_id',
                'CheckoutRequestID': checkout_request_id,
                'ResultCode': '0',
                'ResultDesc': 'The service request is processed successfully.'
            }

        # Generate password and timestamp
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password_str = f"{self.business_shortcode}{self.passkey}{timestamp}"
        password = base64.b64encode(password_str.encode()).decode()

        headers = {
            'Authorization': f'Bearer {self.get_auth_token()}',
            'Content-Type': 'application/json'
        }

        payload = {
            "BusinessShortCode": self.business_shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "CheckoutRequestID": checkout_request_id
        }

        response = requests.post(
            f"{self.base_url}/mpesa/stkpushquery/v1/query",
            json=payload,
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        
        return response.json()

    def _generate_password(self):
        """Generate password for STK push"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password_str = f"{self.business_shortcode}{self.passkey}{timestamp}"
        return base64.b64encode(password_str.encode()).decode('utf-8'), timestamp

    def _validate_phone_number(self, phone_number):
        """Validate and format phone number"""
        if not phone_number:
            raise ValueError("Phone number is required")
            
        # Remove any spaces
        phone_number = phone_number.replace(" ", "")
        
        # Handle different formats
        if phone_number.startswith('+254'):
            phone_number = phone_number[1:]
        elif phone_number.startswith('0'):
            phone_number = '254' + phone_number[1:]
        elif not phone_number.startswith('254'):
            phone_number = '254' + phone_number
            
        # Validate length and format
        if not phone_number.isdigit() or len(phone_number) != 12:
            raise ValueError("Invalid phone number format. Use format: 254XXXXXXXXX")
            
        return phone_number

    @handle_api_errors
    def parse_callback_data(self, callback_data):
        """Parse M-Pesa callback data and extract relevant information"""
        if not callback_data:
            raise ValueError("Callback data cannot be empty")
        
        # Handle test mode - generate a fake successful callback response
        if self.test_mode and isinstance(callback_data, dict) and 'test_checkout_request_id' in callback_data:
            checkout_request_id = callback_data['test_checkout_request_id']
            fake_receipt = f"OGH{str(uuid.uuid4())[:6].upper()}"
            
            logging.debug(f"Test mode: Generating fake callback for {checkout_request_id}")
            
            return {
                'checkout_request_id': checkout_request_id,
                'result_code': 0,
                'result_desc': 'The service request is processed successfully.',
                'receipt_number': fake_receipt,
                'phone_number': callback_data.get('phone_number', '254722000000'),
                'transaction_date': datetime.now().strftime('%Y%m%d%H%M%S'),
                'amount': callback_data.get('amount', 100),
                'is_successful': True
            }
            
        body = callback_data.get('Body', {})
        stk_callback = body.get('stkCallback', {})
        
        checkout_request_id = stk_callback.get('CheckoutRequestID')
        result_code = stk_callback.get('ResultCode')
        result_desc = stk_callback.get('ResultDesc', '')
        
        if not checkout_request_id:
            raise ValueError("Invalid callback data: Missing CheckoutRequestID")
            
        receipt_number = None
        phone_number = None
        transaction_date = None
        amount = None
        
        # Extract metadata if success
        if result_code == 0 and 'CallbackMetadata' in stk_callback:
            items = stk_callback['CallbackMetadata'].get('Item', [])
            
            for item in items:
                name = item.get('Name')
                value = item.get('Value')
                
                if name == 'MpesaReceiptNumber':
                    receipt_number = value
                elif name == 'PhoneNumber':
                    phone_number = value
                elif name == 'TransactionDate':
                    transaction_date = value
                elif name == 'Amount':
                    amount = value
        
        return {
            'checkout_request_id': checkout_request_id,
            'result_code': result_code,
            'result_desc': result_desc,
            'receipt_number': receipt_number,
            'phone_number': phone_number,
            'transaction_date': transaction_date,
            'amount': amount,
            'is_successful': result_code == 0
        }

    def _simulate_sandbox_callback(self, callback_url, conversation_id, amount, phone_number):
        """Simulate a successful callback in sandbox mode"""
        try:
            # Prepare callback data
            callback_data = {
                "Result": {
                    "ConversationID": conversation_id,
                    "OriginatorConversationID": str(uuid.uuid4()),
                    "ResultCode": 0,
                    "ResultDesc": "The service request is processed successfully.",
                    "ResultParameters": {
                        "ResultParameter": [
                            {
                                "Key": "TransactionAmount",
                                "Value": str(amount)
                            },
                            {
                                "Key": "TransactionReceipt",
                                "Value": f"TEST-{conversation_id[:8]}"
                            },
                            {
                                "Key": "B2CRecipientIsRegisteredCustomer",
                                "Value": "Y"
                            },
                            {
                                "Key": "B2CChargesPaidAccountAvailableFunds",
                                "Value": str(amount)
                            },
                            {
                                "Key": "ReceiverPartyPublicName",
                                "Value": f"{phone_number} - Test User"
                            },
                            {
                                "Key": "TransactionCompletedDateTime",
                                "Value": datetime.now().strftime("%d.%m.%Y %H:%M:%S")
                            },
                            {
                                "Key": "B2CUtilityAccountAvailableFunds",
                                "Value": "10000.00"
                            },
                            {
                                "Key": "B2CWorkingAccountAvailableFunds",
                                "Value": "10000.00"
                            }
                        ]
                    },
                    "ReferenceData": {
                        "ReferenceItem": {
                            "Key": "QueueTimeoutURL",
                            "Value": self.b2c_queue_timeout_url
                        }
                    }
                }
            }
            
            logging.info(f"Simulating sandbox callback to {callback_url}")
            logging.info(f"Callback data: {json.dumps(callback_data, indent=2)}")
            
            # Send the callback with a shorter timeout
            response = requests.post(
                callback_url,
                json=callback_data,
                headers={'Content-Type': 'application/json'},
                verify=False,  # Skip SSL verification for localhost
                timeout=5  # Reduced timeout
            )
            
            logging.info(f"Sandbox callback response: {response.status_code} - {response.text}")
            
        except Exception as e:
            logging.error(f"Error simulating sandbox callback: {str(e)}")
            raise

    @handle_api_errors
    def b2c_payment(self, phone_number, amount, remarks=None):
        """
        Initiate a B2C payment (Business to Customer)
        
        Args:
            phone_number: The phone number to send money to (format: 254XXXXXXXXX)
            amount: Amount to send
            remarks: Optional remarks for the transaction
            
        Returns:
            dict: M-Pesa API response with ConversationID
        """
        if self.test_mode:
            logging.info("Test mode: Returning mock B2C response")
            test_conversation_id = str(uuid.uuid4())
            
            # Simulate a successful callback in test mode
            try:
                self._simulate_sandbox_callback(
                    self.b2c_result_url,
                    test_conversation_id,
                    amount,
                    phone_number
                )
            except Exception as e:
                logging.error(f"Error simulating sandbox callback: {str(e)}")
            
            return {
                'test_mode': True,
                'ConversationID': test_conversation_id,
                'OriginatorConversationID': str(uuid.uuid4()),
                'ResponseCode': '0',
                'ResponseDescription': 'Accept the service request successfully.'
            }
            
        if not all([self.initiator_name, self.security_credential, self.b2c_shortcode]):
            raise ValueError("Missing required B2C configuration. Check MPESA_INITIATOR_NAME, MPESA_SECURITY_CREDENTIAL, and MPESA_B2C_SHORTCODE")
            
        # Format phone number
        phone_number = self._validate_phone_number(phone_number)
        
        # Set up the request
        headers = {
            'Authorization': f'Bearer {self.get_auth_token()}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'InitiatorName': self.initiator_name,
            'SecurityCredential': self.security_credential,
            'CommandID': 'BusinessPayment',
            'Amount': int(float(amount)),
            'PartyA': self.b2c_shortcode,
            'PartyB': phone_number,
            'Remarks': remarks or 'Withdrawal Payment',
            'QueueTimeOutURL': self.b2c_queue_timeout_url,
            'ResultURL': self.b2c_result_url,
            'Occasion': 'Withdrawal'
        }

        # Make request with retries
        max_retries = 2
        retry_delay = 1
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                logging.debug("=== B2C Payment Request ===")
                logging.debug(f"URL: {self.b2c_url}")
                logging.debug(f"Headers: {headers}")
                logging.debug(f"Payload: {payload}")
                logging.debug(f"Attempt: {attempt + 1}/{max_retries + 1}")
                
                response = requests.post(
                    self.b2c_url,
                    json=payload,
                    headers=headers,
                    timeout=30
                )
                
                logging.debug("=== B2C Payment Response ===")
                logging.debug(f"Status Code: {response.status_code}")
                logging.debug(f"Response Content-Type: {response.headers.get('content-type', 'unknown')}")
                logging.debug(f"Response: {response.text[:1000]}")  # Log first 1000 chars to avoid huge logs
                
                # Check content type for HTML response
                content_type = response.headers.get('content-type', '').lower()
                if 'text/html' in content_type:
                    error_msg = "Received HTML response from M-Pesa API instead of JSON"
                    logging.error(f"{error_msg}. Status: {response.status_code}, Content: {response.text[:500]}")
                    raise Exception(error_msg)
                
                # Try to parse response as JSON
                try:
                    result = response.json()
                except ValueError as e:
                    error_msg = f"Invalid JSON response from M-Pesa: {response.text[:500]}"
                    logging.error(error_msg)
                    raise Exception(error_msg)

                # Check for error response
                if response.status_code != 200:
                    error_msg = f"B2C payment failed with status {response.status_code}: {result.get('errorMessage', response.text)}"
                    logging.error(error_msg)
                    raise Exception(error_msg)
                    
                # Validate response has required fields
                if 'ConversationID' not in result:
                    error_msg = f"Invalid B2C response: missing ConversationID. Response: {result}"
                    logging.error(error_msg)
                    raise Exception(error_msg)
                    
                return result

            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    logging.warning(f"B2C payment attempt {attempt + 1} failed: {str(e)}. Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                break
                
        error_msg = f"All B2C payment attempts failed: {str(last_error)}"
        logging.error(error_msg)
        raise Exception(error_msg)