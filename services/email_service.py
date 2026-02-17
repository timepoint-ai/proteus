"""
Email service for sending OTP codes via SendGrid
"""

import os
import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, Content

logger = logging.getLogger(__name__)

class EmailService:
    """Service for sending emails via SendGrid"""
    
    def __init__(self):
        self.api_key = os.environ.get('SENDGRID_API_KEY')
        self.from_email = os.environ.get('FROM_EMAIL', 'noreply@proteus.markets')
        self.from_name = 'Proteus'
        
        if self.api_key:
            self.client = SendGridAPIClient(self.api_key)
            logger.info("SendGrid email service initialized")
        else:
            self.client = None
            logger.warning("SendGrid API key not found - email sending disabled")
    
    def send_otp(self, to_email: str, otp_code: str) -> dict:
        """
        Send OTP code via email
        
        Args:
            to_email: Recipient email address
            otp_code: 6-digit OTP code
            
        Returns:
            Result dict with success status
        """
        if not self.client:
            logger.warning(f"Email not sent (no API key): OTP {otp_code} for {to_email}")
            return {
                'success': False,
                'error': 'Email service not configured',
                'test_mode': True,
                'otp': otp_code  # Return OTP for testing
            }
        
        try:
            # Create email content
            subject = f"Your Proteus verification code: {otp_code}"
            
            html_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
                    <h1 style="color: white; margin: 0;">Proteus</h1>
                </div>
                <div style="padding: 40px; background: #f5f5f5;">
                    <h2 style="color: #333; margin-bottom: 20px;">Verify your email</h2>
                    <p style="color: #666; font-size: 16px; line-height: 1.5;">
                        Enter this code to complete your sign in:
                    </p>
                    <div style="background: white; border: 2px solid #667eea; border-radius: 10px; padding: 20px; margin: 30px 0; text-align: center;">
                        <span style="font-size: 32px; font-weight: bold; color: #667eea; letter-spacing: 5px;">
                            {otp_code}
                        </span>
                    </div>
                    <p style="color: #999; font-size: 14px; margin-top: 30px;">
                        This code expires in 5 minutes. Don't share it with anyone.
                    </p>
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                    <p style="color: #999; font-size: 12px; text-align: center;">
                        If you didn't request this code, you can safely ignore this email.
                    </p>
                </div>
            </div>
            """
            
            text_content = f"""
            Proteus Verification Code
            
            Your verification code is: {otp_code}
            
            This code expires in 5 minutes.
            Don't share this code with anyone.
            
            If you didn't request this code, you can safely ignore this email.
            """
            
            # Create mail object
            message = Mail(
                from_email=(self.from_email, self.from_name),
                to_emails=to_email,
                subject=subject,
                html_content=html_content,
                plain_text_content=text_content
            )
            
            # Send email
            response = self.client.send(message)
            
            logger.info(f"OTP email sent to {to_email}, status code: {response.status_code}")
            
            return {
                'success': True,
                'message': f'OTP sent to {to_email}',
                'status_code': response.status_code
            }
            
        except Exception as e:
            logger.error(f"Failed to send OTP email: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'test_mode': True,
                'otp': otp_code  # Return OTP for fallback testing
            }
    
    def send_transaction_alert(self, to_email: str, tx_details: dict) -> dict:
        """
        Send transaction alert email
        
        Args:
            to_email: Recipient email address
            tx_details: Transaction details
            
        Returns:
            Result dict
        """
        if not self.client:
            return {'success': False, 'error': 'Email service not configured'}
        
        try:
            amount = tx_details.get('amount_usd', 0)
            tx_hash = tx_details.get('tx_hash', 'N/A')
            market = tx_details.get('market', 'Unknown')
            
            subject = f"Transaction confirmed: ${amount:.2f} USD"
            
            html_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
                    <h1 style="color: white; margin: 0;">Transaction Confirmed</h1>
                </div>
                <div style="padding: 40px; background: #f5f5f5;">
                    <div style="background: white; border-radius: 10px; padding: 20px; margin-bottom: 20px;">
                        <h3 style="color: #333; margin-top: 0;">Transaction Details</h3>
                        <p><strong>Amount:</strong> ${amount:.2f} USD</p>
                        <p><strong>Market:</strong> {market}</p>
                        <p><strong>Transaction ID:</strong> <code style="background: #f0f0f0; padding: 2px 5px; border-radius: 3px; font-size: 12px;">{tx_hash}</code></p>
                    </div>
                    <p style="color: #666; font-size: 14px;">
                        Your transaction has been confirmed on the BASE network.
                    </p>
                </div>
            </div>
            """
            
            message = Mail(
                from_email=(self.from_email, self.from_name),
                to_emails=to_email,
                subject=subject,
                html_content=html_content
            )
            
            response = self.client.send(message)
            
            return {
                'success': True,
                'status_code': response.status_code
            }
            
        except Exception as e:
            logger.error(f"Failed to send transaction alert: {str(e)}")
            return {'success': False, 'error': str(e)}

# Initialize service
email_service = EmailService()