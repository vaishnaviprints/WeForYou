import logging
from typing import Optional
from models import NotificationLog

logger = logging.getLogger(__name__)

class NotificationService:
    """
    Notification service for sending SMS and Email
    Currently in MOCK mode - logs notifications but doesn't actually send
    Ready for integration with Twilio (SMS) and SendGrid (Email)
    """
    
    def __init__(self):
        self.mock_mode = True  # Set to False when integrating real services
        
    async def send_sms(self, phone: str, message: str, related_to: Optional[str] = None) -> NotificationLog:
        """Send SMS notification"""
        notification = NotificationLog(
            recipient=phone,
            type="sms",
            message=message,
            status="mocked" if self.mock_mode else "sent",
            related_to=related_to
        )
        
        if self.mock_mode:
            logger.info(f"[MOCK SMS] To: {phone} | Message: {message}")
        else:
            # TODO: Integrate with Twilio
            # client = TwilioClient(account_sid, auth_token)
            # client.messages.create(to=phone, from_=twilio_number, body=message)
            pass
            
        return notification
    
    async def send_email(self, email: str, subject: str, message: str, related_to: Optional[str] = None) -> NotificationLog:
        """Send Email notification"""
        notification = NotificationLog(
            recipient=email,
            type="email",
            subject=subject,
            message=message,
            status="mocked" if self.mock_mode else "sent",
            related_to=related_to
        )
        
        if self.mock_mode:
            logger.info(f"[MOCK EMAIL] To: {email} | Subject: {subject} | Message: {message}")
        else:
            # TODO: Integrate with SendGrid
            # sg = SendGridAPIClient(api_key)
            # sg.send(email_data)
            pass
            
        return notification
    
    async def send_donation_confirmation(self, donation: dict, donor_contact: str, volunteer_name: Optional[str] = None):
        """Send donation confirmation to donor"""
        if volunteer_name:
            message = f"Thank you for your donation of ₹{donation['amount']} to {donation.get('campaign_title', 'our cause')}! Collected by volunteer {volunteer_name}. Your receipt will be generated shortly. - WeForYou Foundation"
        else:
            message = f"Thank you for your donation of ₹{donation['amount']}! Your payment is confirmed. Receipt is being generated. - WeForYou Foundation"
        
        # Send SMS if phone number
        if donor_contact and donor_contact.startswith('+') or donor_contact.replace('-', '').replace(' ', '').isdigit():
            return await self.send_sms(donor_contact, message, donation['id'])
        # Send email if email
        elif donor_contact and '@' in donor_contact:
            return await self.send_email(donor_contact, "Donation Confirmation", message, donation['id'])
    
    async def send_cash_collection_alert(self, volunteer_email: str, amount: float, donor_name: str):
        """Alert volunteer about cash collection responsibility"""
        subject = "Cash Collection Responsibility - Action Required"
        message = f"""
        Dear Volunteer,
        
        You have collected ₹{amount} in CASH from {donor_name}.
        
        IMPORTANT: You are responsible for depositing this amount to the Foundation's bank account within 48 hours.
        
        Bank Details:
        Account Name: WeForYou Foundation
        Account Number: 1234567890
        IFSC Code: WFYB0001234
        Bank: Example Bank
        
        After deposit, please update the system with deposit confirmation.
        
        Thank you for your service!
        WeForYou Foundation
        """
        
        return await self.send_email(volunteer_email, subject, message)
    
    async def send_admin_cash_alert(self, admin_email: str, volunteer_name: str, amount: float, donor_name: str):
        """Alert admin about new cash collection"""
        subject = f"New Cash Collection by {volunteer_name}"
        message = f"""
        New cash collection recorded:
        
        Volunteer: {volunteer_name}
        Donor: {donor_name}
        Amount: ₹{amount}
        Status: Pending Deposit Confirmation
        
        Please monitor and confirm deposit when received.
        """
        
        return await self.send_email(admin_email, subject, message)
