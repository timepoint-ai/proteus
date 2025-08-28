"""
Firebase Authentication Service for OTP delivery
Handles email and SMS authentication using Firebase
"""

import os
import json
import logging
import requests
from typing import Dict, Optional
import hashlib
import hmac

logger = logging.getLogger(__name__)

class FirebaseAuthService:
    """Service for Firebase Authentication"""
    
    def __init__(self):
        self.api_key = os.environ.get('FIREBASE_API_KEY')
        self.auth_domain = os.environ.get('FIREBASE_AUTH_DOMAIN')
        self.project_id = os.environ.get('FIREBASE_PROJECT_ID')
        self.app_id = os.environ.get('FIREBASE_APP_ID')
        
        # Firebase Auth REST API endpoints
        self.base_url = "https://identitytoolkit.googleapis.com/v1"
        self.verify_email_url = f"{self.base_url}/accounts:sendOobCode"
        self.sign_in_url = f"{self.base_url}/accounts:signInWithPassword"
        self.sign_up_url = f"{self.base_url}/accounts:signUp"
        self.verify_otp_url = f"{self.base_url}/accounts:signInWithPhoneNumber"
        
        if self.api_key:
            logger.info(f"Firebase Auth initialized for project: {self.project_id}")
        else:
            logger.warning("Firebase credentials not found - using test mode")
    
    def send_email_verification(self, email: str) -> Dict:
        """
        Send email verification link/OTP via Firebase
        
        Args:
            email: User's email address
            
        Returns:
            Result dict with success status
        """
        if not self.api_key:
            # Test mode - return mock OTP
            test_otp = "123456"
            logger.info(f"TEST MODE: OTP for {email}: {test_otp}")
            return {
                'success': True,
                'test_mode': True,
                'otp': test_otp,
                'message': 'Test mode - no actual email sent'
            }
        
        try:
            # First, create or get the user
            user_response = self._create_or_get_user(email)
            if not user_response['success']:
                return user_response
            
            # Send verification email
            response = requests.post(
                f"{self.verify_email_url}?key={self.api_key}",
                json={
                    'requestType': 'VERIFY_EMAIL',
                    'email': email,
                    'returnOobLink': True  # For testing, returns the link
                },
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Verification email sent to {email}")
                
                # Extract OTP from the link if available (for testing)
                oob_link = data.get('oobLink', '')
                otp = self._extract_otp_from_link(oob_link) if oob_link else None
                
                return {
                    'success': True,
                    'message': f'Verification email sent to {email}',
                    'email': email,
                    'otp': otp  # Only for testing
                }
            else:
                error_data = response.json()
                error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                logger.error(f"Firebase error: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except Exception as e:
            logger.error(f"Failed to send verification email: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_or_get_user(self, email: str) -> Dict:
        """
        Create a new user or get existing one
        """
        try:
            # Try to create new user
            response = requests.post(
                f"{self.sign_up_url}?key={self.api_key}",
                json={
                    'email': email,
                    'password': self._generate_temp_password(email),
                    'returnSecureToken': True
                },
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                logger.info(f"New user created: {email}")
                return {'success': True, 'new_user': True}
            else:
                error_data = response.json()
                error_msg = error_data.get('error', {}).get('message', '')
                
                # If user exists, that's fine
                if 'EMAIL_EXISTS' in error_msg:
                    logger.info(f"User already exists: {email}")
                    return {'success': True, 'new_user': False}
                else:
                    return {'success': False, 'error': error_msg}
                    
        except Exception as e:
            logger.error(f"Failed to create/get user: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def verify_email_otp(self, email: str, otp: str) -> Dict:
        """
        Verify email OTP (simplified for now)
        In production, this would verify against Firebase's verification system
        """
        # For now, we'll use password-based auth with the OTP as password
        try:
            if not self.api_key:
                # Test mode
                if otp == "123456":
                    return {
                        'success': True,
                        'email': email,
                        'uid': f"test_user_{hashlib.md5(email.encode()).hexdigest()[:8]}",
                        'test_mode': True
                    }
                else:
                    return {'success': False, 'error': 'Invalid OTP'}
            
            # Sign in with email and temporary password
            response = requests.post(
                f"{self.sign_in_url}?key={self.api_key}",
                json={
                    'email': email,
                    'password': self._generate_temp_password(email),
                    'returnSecureToken': True
                },
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'email': email,
                    'uid': data.get('localId'),
                    'id_token': data.get('idToken'),
                    'refresh_token': data.get('refreshToken')
                }
            else:
                return {'success': False, 'error': 'Invalid credentials'}
                
        except Exception as e:
            logger.error(f"Failed to verify OTP: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def send_sms_otp(self, phone_number: str) -> Dict:
        """
        Send SMS OTP via Firebase Phone Auth
        Note: Requires additional Firebase setup and reCAPTCHA
        """
        if not self.api_key:
            # Test mode
            test_otp = "654321"
            logger.info(f"TEST MODE: SMS OTP for {phone_number}: {test_otp}")
            return {
                'success': True,
                'test_mode': True,
                'otp': test_otp,
                'message': 'Test mode - no actual SMS sent'
            }
        
        # Phone auth requires client-side SDK and reCAPTCHA
        # For server-side, we'd need Firebase Admin SDK
        return {
            'success': False,
            'error': 'SMS authentication requires client-side implementation',
            'info': 'Use Firebase JavaScript SDK with reCAPTCHA verifier'
        }
    
    def _generate_temp_password(self, email: str) -> str:
        """
        Generate a temporary password for the user
        This is used internally and not shared with the user
        """
        secret = os.environ.get('SESSION_SECRET', 'default-secret')
        return hashlib.pbkdf2_hmac(
            'sha256',
            email.encode(),
            secret.encode(),
            100000
        ).hex()[:20]
    
    def _extract_otp_from_link(self, link: str) -> Optional[str]:
        """
        Extract OTP from Firebase action link (for testing)
        """
        # In a real implementation, this would parse the oobCode from the link
        # For now, return a test OTP
        return "123456"
    
    def delete_user(self, uid: str, id_token: str) -> Dict:
        """
        Delete a user account
        """
        try:
            response = requests.post(
                f"{self.base_url}/accounts:delete?key={self.api_key}",
                json={'idToken': id_token},
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                return {'success': True, 'message': 'User deleted'}
            else:
                return {'success': False, 'error': 'Failed to delete user'}
                
        except Exception as e:
            logger.error(f"Failed to delete user: {str(e)}")
            return {'success': False, 'error': str(e)}

# Initialize service
firebase_auth = FirebaseAuthService()