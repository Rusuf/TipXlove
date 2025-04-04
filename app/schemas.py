from marshmallow import Schema, fields, validate

class PaymentSchema(Schema):
    """Schema for validating payment requests"""
    creator_id = fields.Integer(required=True)
    # Use Decimal for currency, but ensure it handles M-Pesa integer amounts if needed
    amount = fields.Decimal(required=True, validate=validate.Range(min=1, max=70000), as_string=False, places=2)
    phone_number = fields.String(required=True, validate=validate.Regexp(r'^254[0-9]{9}$', error="Phone number must be in 254xxxxxxxxx format"))
    tipper_name = fields.String(required=False, validate=validate.Length(max=50), load_default='Anonymous', dump_default='Anonymous')
    message = fields.String(required=False, validate=validate.Length(max=200), load_default='', dump_default='')

# Add other schemas here as needed, e.g.:
# class UserSchema(Schema): ...
# class WithdrawalSchema(Schema): ... 