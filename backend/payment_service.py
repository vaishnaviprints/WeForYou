import os
import razorpay
import uuid
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class PaymentService:
    def __init__(self):
        self.use_mock = os.environ.get('USE_MOCK_PAYMENT', 'true').lower() == 'true'
        self.razorpay_key_id = os.environ.get('RAZORPAY_KEY_ID', '')
        self.razorpay_key_secret = os.environ.get('RAZORPAY_KEY_SECRET', '')
        
        if not self.use_mock and self.razorpay_key_id and self.razorpay_key_secret:
            self.client = razorpay.Client(auth=(self.razorpay_key_id, self.razorpay_key_secret))
        else:
            self.client = None
            logger.info("Payment service running in MOCK mode")
    
    async def create_order(self, amount: float, currency: str, donation_id: str, user_email: str):
        """Create a Razorpay order or mock order"""
        amount_paise = int(amount * 100)  # Convert to paise
        
        if self.use_mock or not self.client:
            # Mock payment
            order_id = f"order_mock_{uuid.uuid4().hex[:12]}"
            return {
                "id": order_id,
                "amount": amount_paise,
                "currency": currency,
                "status": "created",
                "key_id": "mock_key"
            }
        
        try:
            order_data = {
                "amount": amount_paise,
                "currency": currency,
                "receipt": donation_id,
                "notes": {
                    "donation_id": donation_id,
                    "user_email": user_email
                }
            }
            order = self.client.order.create(data=order_data)
            return order
        except Exception as e:
            logger.error(f"Razorpay order creation failed: {str(e)}")
            raise Exception(f"Payment order creation failed: {str(e)}")
    
    async def verify_payment(self, order_id: str, payment_id: str, signature: str) -> bool:
        """Verify Razorpay payment signature"""
        if self.use_mock or not self.client:
            # Mock verification - always succeeds for testing
            return True
        
        try:
            params_dict = {
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }
            self.client.utility.verify_payment_signature(params_dict)
            return True
        except Exception as e:
            logger.error(f"Payment verification failed: {str(e)}")
            return False
    
    async def capture_payment(self, payment_id: str, amount: float):
        """Capture a payment"""
        if self.use_mock or not self.client:
            return {"id": payment_id, "status": "captured"}
        
        try:
            amount_paise = int(amount * 100)
            payment = self.client.payment.capture(payment_id, amount_paise)
            return payment
        except Exception as e:
            logger.error(f"Payment capture failed: {str(e)}")
            raise Exception(f"Payment capture failed: {str(e)}")
    
    async def refund_payment(self, payment_id: str, amount: Optional[float] = None):
        """Refund a payment"""
        if self.use_mock or not self.client:
            return {"id": f"rfnd_mock_{uuid.uuid4().hex[:12]}", "status": "processed"}
        
        try:
            refund_data = {}
            if amount:
                refund_data["amount"] = int(amount * 100)
            
            refund = self.client.payment.refund(payment_id, refund_data)
            return refund
        except Exception as e:
            logger.error(f"Refund failed: {str(e)}")
            raise Exception(f"Refund failed: {str(e)}")