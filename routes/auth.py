"""
Wallet authentication routes for BASE-only architecture
Phase 2: Wallet-only authentication endpoints
"""

from flask import Blueprint, request, jsonify
import logging
from datetime import datetime
import secrets
from services.wallet_auth import wallet_auth_service

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

# Store nonces temporarily (in production, use Redis with expiry)
nonce_store = {}

@auth_bp.route('/auth/nonce/<address>', methods=['GET'])
def get_auth_nonce(address):
    """Get a nonce for wallet authentication"""
    try:
        # Generate a secure random nonce
        nonce = secrets.token_hex(16)
        
        # Store nonce with timestamp (cleanup old nonces periodically)
        nonce_store[address.lower()] = {
            'nonce': nonce,
            'timestamp': datetime.utcnow()
        }
        
        # Generate the message to sign
        message = wallet_auth_service.generate_auth_message(address, nonce)
        
        return jsonify({
            'nonce': nonce,
            'message': message
        })
        
    except Exception as e:
        logger.error(f"Error generating nonce: {e}")
        return jsonify({'error': 'Failed to generate nonce'}), 500

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
            return jsonify({'error': 'Missing required fields'}), 400
            
        # Authenticate the wallet
        result = wallet_auth_service.authenticate_wallet(address, signature, message)
        
        if result['success']:
            # Clean up the used nonce
            if address.lower() in nonce_store:
                del nonce_store[address.lower()]
                
            return jsonify({
                'success': True,
                'token': result['token'],
                'address': result['address'],
                'expires_in': result['expires_in']
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 401
            
    except Exception as e:
        logger.error(f"Error verifying wallet: {e}")
        return jsonify({'error': 'Verification failed'}), 500

@auth_bp.route('/auth/refresh', methods=['POST'])
def refresh_token():
    """Refresh an existing JWT token"""
    try:
        # Get the current token
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'No token provided'}), 401
            
        token = auth_header.split(' ')[1]
        
        # Verify the current token
        payload = wallet_auth_service.verify_jwt_token(token)
        
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
            
        # Issue a new token
        new_token = wallet_auth_service.create_jwt_token(payload['address'])
        
        return jsonify({
            'success': True,
            'token': new_token,
            'address': payload['address'],
            'expires_in': wallet_auth_service.token_expiry_hours * 3600
        })
        
    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        return jsonify({'error': 'Failed to refresh token'}), 500

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
                
        return jsonify({
            'success': True,
            'message': 'Logged out successfully'
        })
        
    except Exception as e:
        logger.error(f"Error during logout: {e}")
        return jsonify({'error': 'Logout failed'}), 500

@auth_bp.route('/auth/status', methods=['GET'])
def auth_status():
    """Check authentication status"""
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
        logger.error(f"Error checking auth status: {e}")
        return jsonify({
            'authenticated': False,
            'address': None
        })