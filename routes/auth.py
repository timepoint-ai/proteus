"""
Wallet authentication routes for BASE-only architecture
Phase 2: Wallet-only authentication endpoints
Now includes Coinbase Embedded Wallet email authentication
"""

from flask import Blueprint, request, jsonify, session
import logging
from datetime import datetime, timedelta, timezone
import secrets
import random
from services.wallet_auth import wallet_auth_service
from services.firebase_auth import FirebaseAuthService
from utils.api_errors import (
    error_response, success_response, validation_error, unauthorized,
    internal_error, ErrorCode
)

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

# Initialize Firebase Auth Service
firebase_auth = FirebaseAuthService()

# Store nonces temporarily (in production, use Redis with expiry)
nonce_store = {}

# Store OTP codes temporarily (in production, use Redis with expiry)
otp_store = {}

@auth_bp.route('/auth/nonce/<address>', methods=['GET'])
def get_auth_nonce(address):
    """Get a nonce for wallet authentication"""
    try:
        # Generate a secure random nonce
        nonce = secrets.token_hex(16)
        
        # Store nonce with timestamp (cleanup old nonces periodically)
        nonce_store[address.lower()] = {
            'nonce': nonce,
            'timestamp': datetime.now(timezone.utc)
        }
        
        # Generate the message to sign
        message = wallet_auth_service.generate_auth_message(address, nonce)
        
        return jsonify({
            'nonce': nonce,
            'message': message
        })
        
    except Exception as e:
        logger.error(f"Error generating nonce: {e}")
        return internal_error('Failed to generate nonce')

@auth_bp.route('/api/embedded/auth/send-otp', methods=['POST'])
def send_otp():
    """Send OTP to email for Coinbase Embedded Wallet authentication"""
    try:
        data = request.get_json()
        email = data.get('email')

        if not email:
            return validation_error('Email is required', 'email')

        # Generate 6-digit OTP
        otp = str(random.randint(100000, 999999))

        # Store OTP with expiry (5 minutes)
        otp_store[email.lower()] = {
            'otp': otp,
            'timestamp': datetime.now(timezone.utc),
            'expires_at': datetime.now(timezone.utc) + timedelta(minutes=5)
        }

        # Send OTP via Firebase
        success = firebase_auth.send_otp_email(email, otp)

        if success:
            logger.info(f"OTP sent to {email}")
            return success_response(message='OTP sent successfully')
        else:
            return internal_error('Failed to send OTP')

    except Exception as e:
        logger.error(f"Error sending OTP: {e}")
        return internal_error('Failed to send OTP')

@auth_bp.route('/api/embedded/auth/verify-otp', methods=['POST'])
def verify_otp():
    """Verify OTP and create authenticated session"""
    try:
        data = request.get_json()
        email = data.get('email')
        otp = data.get('otp')

        if not all([email, otp]):
            return validation_error('Email and OTP are required')

        # Check if OTP exists and is valid
        stored_otp = otp_store.get(email.lower())

        if not stored_otp:
            return error_response(ErrorCode.TOKEN_EXPIRED, 'Invalid or expired OTP', 400)

        # Check expiry
        if datetime.now(timezone.utc) > stored_otp['expires_at']:
            del otp_store[email.lower()]
            return error_response(ErrorCode.TOKEN_EXPIRED, 'OTP has expired', 400)

        # Verify OTP
        if stored_otp['otp'] != otp:
            return error_response(ErrorCode.INVALID_TOKEN, 'Invalid OTP', 400)

        # Clean up used OTP
        del otp_store[email.lower()]

        # Create authenticated session
        session['authenticated'] = True
        session['email'] = email
        session['wallet_type'] = 'coinbase'

        # Generate a wallet address for the user (deterministic from email)
        # In production, this would be the actual Coinbase wallet address
        import hashlib
        wallet_hash = hashlib.sha256(email.encode()).hexdigest()
        wallet_address = '0x' + wallet_hash[:40]

        session['wallet_address'] = wallet_address

        return success_response({
            'email': email,
            'wallet_address': wallet_address
        }, message='Successfully authenticated')

    except Exception as e:
        logger.error(f"Error verifying OTP: {e}")
        return internal_error('Failed to verify OTP')

@auth_bp.route('/api/embedded/auth/status', methods=['GET'])
def auth_status():
    """Check authentication status"""
    try:
        if session.get('authenticated'):
            return jsonify({
                'authenticated': True,
                'email': session.get('email'),
                'wallet_address': session.get('wallet_address'),
                'wallet_type': session.get('wallet_type', 'coinbase')
            })
        else:
            return jsonify({
                'authenticated': False
            })
    except Exception as e:
        logger.error(f"Error checking auth status: {e}")
        return jsonify({'authenticated': False}), 500

@auth_bp.route('/auth/verify', methods=['POST'])
def verify_wallet():
    """Verify wallet signature and issue JWT token"""
    try:
        data = request.get_json()

        # Extract required fields
        address = data.get('address')
        signature = data.get('signature')
        message = data.get('message')

        if not all([address, signature, message]):
            return validation_error('Missing required fields: address, signature, message')

        # Authenticate the wallet
        result = wallet_auth_service.authenticate_wallet(address, signature, message)

        if result['success']:
            # Clean up the used nonce
            if address.lower() in nonce_store:
                del nonce_store[address.lower()]

            return success_response({
                'token': result['token'],
                'address': result['address'],
                'expires_in': result['expires_in']
            })
        else:
            return error_response(ErrorCode.INVALID_SIGNATURE, result['error'], 401)

    except Exception as e:
        logger.error(f"Error verifying wallet: {e}")
        return internal_error('Verification failed')

@auth_bp.route('/auth/refresh', methods=['POST'])
def refresh_token():
    """Refresh an existing JWT token"""
    try:
        # Get the current token
        auth_header = request.headers.get('Authorization')

        if not auth_header or not auth_header.startswith('Bearer '):
            return unauthorized('No token provided')

        token = auth_header.split(' ')[1]

        # Verify the current token
        payload = wallet_auth_service.verify_jwt_token(token)

        if not payload:
            return error_response(ErrorCode.TOKEN_EXPIRED, 'Invalid or expired token', 401)

        # Issue a new token
        new_token = wallet_auth_service.create_jwt_token(payload['address'])

        return success_response({
            'token': new_token,
            'address': payload['address'],
            'expires_in': wallet_auth_service.token_expiry_hours * 3600
        })

    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        return internal_error('Failed to refresh token')

@auth_bp.route('/auth/logout', methods=['POST'])
def logout():
    """Logout endpoint (client should discard JWT token)"""
    # In a JWT-based system, logout is handled client-side
    # This endpoint exists for compatibility and logging purposes
    try:
        auth_header = request.headers.get('Authorization')

        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            payload = wallet_auth_service.verify_jwt_token(token)

            if payload:
                logger.info(f"Wallet {payload['address']} logged out")

        return success_response(message='Logged out successfully')

    except Exception as e:
        logger.error(f"Error during logout: {e}")
        return internal_error('Logout failed')

@auth_bp.route('/auth/jwt-status', methods=['GET'])
def jwt_auth_status():
    """Check JWT authentication status for MetaMask"""
    try:
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                'authenticated': False,
                'address': None
            })
            
        token = auth_header.split(' ')[1]
        payload = wallet_auth_service.verify_jwt_token(token)
        
        if payload:
            return jsonify({
                'authenticated': True,
                'address': payload['address']
            })
        else:
            return jsonify({
                'authenticated': False,
                'address': None
            })
            
    except Exception as e:
        logger.error(f"Error checking JWT auth status: {e}")
        return jsonify({
            'authenticated': False,
            'address': None
        })