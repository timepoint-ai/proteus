"""
Embedded wallet authentication routes
Provides email/SMS login without seed phrases
"""

from flask import Blueprint, request, jsonify, session, render_template
from services.embedded_wallet import EmbeddedWalletService
from services.firebase_auth import firebase_auth
from utils.api_errors import (
    error_response, success_response, validation_error, unauthorized,
    forbidden, internal_error, ErrorCode
)
import logging
import os
import secrets
import time
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

embedded_auth = Blueprint('embedded_auth', __name__, url_prefix='/api/embedded')
wallet_service = EmbeddedWalletService()

# Store OTP codes temporarily (in production, use Redis)
otp_storage = {}

@embedded_auth.route('/request-otp', methods=['POST'])
def request_otp():
    """Request OTP for email/SMS authentication"""
    try:
        data = request.json
        identifier = data.get('identifier')  # Email or phone
        auth_method = data.get('auth_method', 'email')  # 'email' or 'sms'

        if not identifier:
            return validation_error('Identifier required', 'identifier')
        
        # Use Firebase for email authentication
        if '@' in identifier:
            result = firebase_auth.send_email_verification(identifier)
            
            if result['success']:
                # Store for verification (Firebase handles the actual OTP)
                otp_storage[identifier] = {
                    'expires': time.time() + 300,
                    'auth_method': 'email',
                    'firebase_uid': result.get('uid')
                }
                
                return jsonify({
                    'success': True,
                    'message': f'Verification email sent to {identifier}',
                    'auth_method': 'email',
                    'test_otp': result.get('otp') if result.get('test_mode') else None
                })
            else:
                return error_response(
                    ErrorCode.WALLET_ERROR,
                    result.get('error', 'Failed to send email'),
                    400
                )
        else:
            # Phone number - use Firebase SMS (requires client-side implementation)
            result = firebase_auth.send_sms_otp(identifier)
            
            if result['success']:
                otp_storage[identifier] = {
                    'code': result.get('otp', ''),
                    'expires': time.time() + 300,
                    'auth_method': 'sms'
                }
                
                return jsonify({
                    'success': True,
                    'message': f'SMS sent to {identifier}',
                    'auth_method': 'sms',
                    'test_otp': result.get('otp') if result.get('test_mode') else None,
                    'info': result.get('info')
                })
            else:
                return error_response(
                    ErrorCode.WALLET_ERROR,
                    result.get('error', 'SMS requires client-side implementation'),
                    400,
                    {'info': 'Use Firebase JavaScript SDK for phone authentication'}
                )

    except Exception as e:
        logger.error(f"OTP request failed: {str(e)}")
        return internal_error(f'OTP request failed: {str(e)}')

@embedded_auth.route('/verify-otp', methods=['POST'])
def verify_otp():
    """Verify OTP and create/login to wallet"""
    try:
        data = request.json
        identifier = data.get('identifier')
        otp_code = data.get('otp_code')

        if not identifier or not otp_code:
            return validation_error('Identifier and OTP required')

        # Check if email or phone
        if '@' in identifier:
            # Verify with Firebase
            result = firebase_auth.verify_email_otp(identifier, otp_code)

            if not result['success']:
                return error_response(ErrorCode.INVALID_TOKEN, result.get('error', 'Invalid OTP'), 400)

            firebase_uid = result.get('uid')
        else:
            # For phone, check stored OTP (simplified for now)
            stored_otp = otp_storage.get(identifier)
            if not stored_otp:
                return error_response(ErrorCode.TOKEN_EXPIRED, 'OTP not found or expired', 400)

            if time.time() > stored_otp['expires']:
                del otp_storage[identifier]
                return error_response(ErrorCode.TOKEN_EXPIRED, 'OTP expired', 400)

            if stored_otp.get('code') != otp_code:
                return error_response(ErrorCode.INVALID_TOKEN, 'Invalid OTP', 400)

            firebase_uid = f"phone_{identifier}"
        
        # Clear OTP after successful verification
        auth_method = stored_otp['auth_method']
        del otp_storage[identifier]
        
        # Create or authenticate wallet
        result = wallet_service.authenticate_wallet(identifier, otp_code)
        
        if result['success']:
            # Store in session
            session['wallet_address'] = result['wallet_address']
            session['identifier'] = identifier
            session['auth_method'] = auth_method
            
            # Get wallet balance
            balance = wallet_service.get_wallet_balance(result['wallet_address'])
            
            return jsonify({
                'success': True,
                'wallet_address': result['wallet_address'],
                'token': result['token'],
                'auth_method': auth_method,
                'balance_usd': balance.get('balance_usd', 0)
            })
        else:
            return unauthorized(result.get('error', 'Authentication failed'))

    except Exception as e:
        logger.error(f"OTP verification failed: {str(e)}")
        return internal_error(f'OTP verification failed: {str(e)}')

@embedded_auth.route('/create-wallet', methods=['POST'])
def create_wallet():
    """Create a new embedded wallet"""
    try:
        data = request.json
        identifier = data.get('identifier')
        auth_method = data.get('auth_method', 'email')

        if not identifier:
            return validation_error('Identifier required', 'identifier')

        # Create wallet
        result = wallet_service.create_wallet(identifier, auth_method)

        if result['success']:
            # Store in session
            session['wallet_address'] = result['wallet_address']
            session['identifier'] = identifier
            session['auth_method'] = auth_method

            return jsonify({
                'success': True,
                'wallet_address': result['wallet_address'],
                'token': result['token'],
                'auth_method': auth_method
            })
        else:
            return error_response(ErrorCode.WALLET_ERROR, result.get('error', 'Wallet creation failed'), 500)

    except Exception as e:
        logger.error(f"Wallet creation failed: {str(e)}")
        return internal_error(f'Wallet creation failed: {str(e)}')

@embedded_auth.route('/wallet-info', methods=['GET'])
def wallet_info():
    """Get wallet information for current user"""
    try:
        wallet_address = session.get('wallet_address')
        if not wallet_address:
            return unauthorized('Not authenticated')

        # Get wallet balance
        balance = wallet_service.get_wallet_balance(wallet_address)

        # Get wallet policies
        policies = wallet_service.get_wallet_policy(wallet_address)

        return jsonify({
            'success': True,
            'wallet_address': wallet_address,
            'identifier': session.get('identifier'),
            'auth_method': session.get('auth_method'),
            'balance': balance,
            'policies': policies
        })

    except Exception as e:
        logger.error(f"Failed to get wallet info: {str(e)}")
        return internal_error(f'Failed to get wallet info: {str(e)}')

@embedded_auth.route('/update-policies', methods=['POST'])
def update_policies():
    """Update wallet policies"""
    try:
        wallet_address = session.get('wallet_address')
        if not wallet_address:
            return unauthorized('Not authenticated')

        data = request.json
        policy_updates = data.get('policies', {})

        # Validate and update policies
        success = wallet_service.update_wallet_policy(wallet_address, policy_updates)

        if success:
            return jsonify({
                'success': True,
                'message': 'Policies updated',
                'policies': wallet_service.get_wallet_policy(wallet_address)
            })
        else:
            return internal_error('Failed to update policies')

    except Exception as e:
        logger.error(f"Policy update failed: {str(e)}")
        return internal_error(f'Policy update failed: {str(e)}')

@embedded_auth.route('/sign-transaction', methods=['POST'])
def sign_transaction():
    """Sign a transaction with embedded wallet"""
    try:
        wallet_address = session.get('wallet_address')
        identifier = session.get('identifier')

        if not wallet_address or not identifier:
            return unauthorized('Not authenticated')

        data = request.json
        tx_data = data.get('transaction')

        if not tx_data:
            return validation_error('Transaction data required', 'transaction')

        # Check compliance before signing
        compliance = wallet_service.check_transaction_compliance(wallet_address, tx_data)

        if not compliance['allowed']:
            return forbidden(compliance['reason'])

        # Sign transaction
        result = wallet_service.sign_transaction(identifier, tx_data)

        if result['success']:
            return jsonify({
                'success': True,
                'signed_tx': result['signed_tx'],
                'tx_hash': result['tx_hash'],
                'requires_2fa': compliance.get('requires_2fa', False)
            })
        else:
            return error_response(ErrorCode.WALLET_ERROR, result.get('error', 'Signing failed'), 500)

    except Exception as e:
        logger.error(f"Transaction signing failed: {str(e)}")
        return internal_error(f'Transaction signing failed: {str(e)}')

@embedded_auth.route('/logout', methods=['POST'])
def logout():
    """Logout from embedded wallet"""
    try:
        session.clear()
        return success_response(message='Logged out successfully')
    except Exception as e:
        logger.error(f"Logout failed: {str(e)}")
        return internal_error(f'Logout failed: {str(e)}')

@embedded_auth.route('/check-compliance', methods=['POST'])
def check_compliance():
    """Check if a transaction complies with policies"""
    try:
        wallet_address = session.get('wallet_address')
        if not wallet_address:
            return unauthorized('Not authenticated')

        data = request.json
        tx_data = data.get('transaction')

        if not tx_data:
            return validation_error('Transaction data required', 'transaction')

        # Check compliance
        compliance = wallet_service.check_transaction_compliance(wallet_address, tx_data)

        return success_response({'compliance': compliance})

    except Exception as e:
        logger.error(f"Compliance check failed: {str(e)}")
        return internal_error(f'Compliance check failed: {str(e)}')

@embedded_auth.route('/test')
def test_page():
    """Display the embedded wallet test page"""
    return render_template('embedded_wallet_test.html')