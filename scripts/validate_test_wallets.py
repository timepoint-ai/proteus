#!/usr/bin/env python3
"""
Validate Test Wallet Configuration for Proteus

This script checks that all required test wallet environment variables are properly configured
for BASE Sepolia testnet testing.
"""

import os
import json
import sys
from web3 import Web3
from eth_account import Account
import requests
from decimal import Decimal

# BASE Sepolia configuration
BASE_SEPOLIA_CHAIN_ID = 84532
BASE_SEPOLIA_RPC = "https://base-sepolia.g.alchemy.com/public"
BASE_SEPOLIA_EXPLORER = "https://sepolia.basescan.org"

class Colors:
    """Terminal colors for output"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_status(status, message):
    """Print colored status message"""
    if status == "success":
        print(f"{Colors.GREEN}✓{Colors.RESET} {message}")
    elif status == "warning":
        print(f"{Colors.YELLOW}⚠{Colors.RESET} {message}")
    elif status == "error":
        print(f"{Colors.RED}✗{Colors.RESET} {message}")
    elif status == "info":
        print(f"{Colors.BLUE}ℹ{Colors.RESET} {message}")

def validate_wallet_address(address):
    """Validate ethereum wallet address"""
    try:
        if not address:
            return False, "Address is empty"
        if not address.startswith('0x'):
            return False, "Address must start with 0x"
        if len(address) != 42:
            return False, f"Address must be 42 characters, got {len(address)}"
        if not Web3.is_address(address):
            return False, "Invalid address format"
        return True, "Valid address"
    except Exception as e:
        return False, str(e)

def validate_private_key(private_key):
    """Validate ethereum private key"""
    try:
        if not private_key:
            return False, "Private key is empty", None
        if not private_key.startswith('0x'):
            return False, "Private key must start with 0x", None
        if len(private_key) != 66:
            return False, f"Private key must be 66 characters, got {len(private_key)}", None
        
        # Try to create account from private key
        account = Account.from_key(private_key)
        return True, "Valid private key", account.address
    except Exception as e:
        return False, f"Invalid private key: {str(e)}", None

def check_wallet_balance(w3, address):
    """Check wallet balance on BASE Sepolia"""
    try:
        balance_wei = w3.eth.get_balance(address)
        balance_eth = w3.from_wei(balance_wei, 'ether')
        return True, balance_eth
    except Exception as e:
        return False, str(e)

def main():
    """Main validation function"""
    print(f"\n{Colors.BOLD}Proteus Test Wallet Configuration Validator{Colors.RESET}")
    print(f"Validating configuration for BASE Sepolia (Chain ID: {BASE_SEPOLIA_CHAIN_ID})\n")
    
    # Initialize Web3
    print_status("info", "Connecting to BASE Sepolia RPC...")
    try:
        # Try custom RPC first, fall back to public
        custom_rpc = os.environ.get('TEST_NETWORK_RPC')
        rpc_url = custom_rpc if custom_rpc else BASE_SEPOLIA_RPC
        
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not w3.is_connected():
            print_status("error", f"Failed to connect to RPC: {rpc_url}")
            return 1
        
        chain_id = w3.eth.chain_id
        if chain_id != BASE_SEPOLIA_CHAIN_ID:
            print_status("error", f"Wrong chain ID: {chain_id}, expected {BASE_SEPOLIA_CHAIN_ID}")
            return 1
        
        print_status("success", f"Connected to BASE Sepolia (Chain ID: {chain_id})")
        print_status("info", f"RPC URL: {rpc_url}")
        
        # Get current gas price
        gas_price = w3.eth.gas_price
        gas_price_gwei = gas_price / 10**9
        print_status("info", f"Current gas price: {gas_price_gwei:.3f} gwei\n")
        
    except Exception as e:
        print_status("error", f"RPC connection error: {str(e)}")
        return 1
    
    # Check environment variables
    errors = 0
    warnings = 0
    
    # 1. Check TEST_WALLET_ADDRESS
    print(f"{Colors.BOLD}1. Main Test Wallet{Colors.RESET}")
    test_wallet = os.environ.get('TEST_WALLET_ADDRESS')
    if not test_wallet:
        print_status("error", "TEST_WALLET_ADDRESS not set")
        errors += 1
    else:
        valid, message = validate_wallet_address(test_wallet)
        if valid:
            print_status("success", f"TEST_WALLET_ADDRESS: {test_wallet}")
            # Check balance
            success, balance = check_wallet_balance(w3, test_wallet)
            if success:
                if balance > 0.1:
                    print_status("success", f"Balance: {balance} BASE ETH")
                elif balance > 0.01:
                    print_status("warning", f"Balance: {balance} BASE ETH (recommended: >0.1)")
                    warnings += 1
                else:
                    print_status("error", f"Balance: {balance} BASE ETH (insufficient)")
                    errors += 1
            else:
                print_status("error", f"Failed to check balance: {balance}")
                errors += 1
        else:
            print_status("error", f"Invalid address: {message}")
            errors += 1
    
    # 2. Check TEST_WALLET_PRIVATE_KEY
    print(f"\n{Colors.BOLD}2. Main Wallet Private Key{Colors.RESET}")
    test_private_key = os.environ.get('TEST_WALLET_PRIVATE_KEY')
    if not test_private_key:
        print_status("error", "TEST_WALLET_PRIVATE_KEY not set")
        errors += 1
    else:
        valid, message, derived_address = validate_private_key(test_private_key)
        if valid:
            print_status("success", "TEST_WALLET_PRIVATE_KEY is valid")
            # Check if private key matches address
            if test_wallet and derived_address.lower() == test_wallet.lower():
                print_status("success", "Private key matches wallet address")
            elif test_wallet:
                print_status("error", f"Private key derives different address: {derived_address}")
                errors += 1
        else:
            print_status("error", message)
            errors += 1
    
    # 3. Check TEST_ORACLE_WALLETS
    print(f"\n{Colors.BOLD}3. Oracle Wallets{Colors.RESET}")
    oracle_wallets_str = os.environ.get('TEST_ORACLE_WALLETS')
    if not oracle_wallets_str:
        print_status("error", "TEST_ORACLE_WALLETS not set")
        errors += 1
    else:
        try:
            oracle_wallets = json.loads(oracle_wallets_str)
            if not isinstance(oracle_wallets, list):
                print_status("error", "TEST_ORACLE_WALLETS must be a JSON array")
                errors += 1
            elif len(oracle_wallets) < 3:
                print_status("error", f"Need at least 3 oracle wallets, found {len(oracle_wallets)}")
                errors += 1
            else:
                print_status("success", f"Found {len(oracle_wallets)} oracle wallets")
                
                # Validate each oracle wallet
                for i, wallet in enumerate(oracle_wallets):
                    valid, message = validate_wallet_address(wallet)
                    if valid:
                        success, balance = check_wallet_balance(w3, wallet)
                        if success:
                            if balance >= 0.01:
                                print_status("success", f"Oracle {i+1}: {wallet[:10]}... (Balance: {balance} ETH)")
                            else:
                                print_status("warning", f"Oracle {i+1}: {wallet[:10]}... (Low balance: {balance} ETH)")
                                warnings += 1
                    else:
                        print_status("error", f"Oracle {i+1}: {message}")
                        errors += 1
                
                # Check for duplicates
                if len(oracle_wallets) != len(set(oracle_wallets)):
                    print_status("error", "Duplicate oracle wallets detected")
                    errors += 1
                    
        except json.JSONDecodeError as e:
            print_status("error", f"Invalid JSON format: {str(e)}")
            errors += 1
        except Exception as e:
            print_status("error", f"Error parsing oracle wallets: {str(e)}")
            errors += 1
    
    # 4. Check TEST_CHAIN_ID (optional)
    print(f"\n{Colors.BOLD}4. Chain Configuration{Colors.RESET}")
    test_chain_id = os.environ.get('TEST_CHAIN_ID')
    if test_chain_id:
        try:
            chain_id_int = int(test_chain_id)
            if chain_id_int == BASE_SEPOLIA_CHAIN_ID:
                print_status("success", f"TEST_CHAIN_ID: {test_chain_id} (BASE Sepolia)")
            elif chain_id_int == 11155111:
                print_status("error", "TEST_CHAIN_ID is set to Ethereum Sepolia (11155111), should be BASE Sepolia (84532)")
                errors += 1
            else:
                print_status("error", f"Unknown chain ID: {test_chain_id}")
                errors += 1
        except ValueError:
            print_status("error", f"Invalid chain ID format: {test_chain_id}")
            errors += 1
    else:
        print_status("info", f"TEST_CHAIN_ID not set (will use default: {BASE_SEPOLIA_CHAIN_ID})")
    
    # 5. Check other required secrets
    print(f"\n{Colors.BOLD}5. Other Required Secrets{Colors.RESET}")
    
    # Check TEST_MANAGER_PASSCODE
    if os.environ.get('TEST_MANAGER_PASSCODE'):
        print_status("success", "TEST_MANAGER_PASSCODE is set")
    else:
        print_status("warning", "TEST_MANAGER_PASSCODE not set (required for test manager access)")
        warnings += 1
    
    # Check X.com API credentials
    x_api_configured = all([
        os.environ.get('X_API_KEY'),
        os.environ.get('X_API_KEY_SECRET'),
        os.environ.get('X_BEARER_TOKEN')
    ])
    
    if x_api_configured:
        print_status("success", "X.com API credentials are configured")
    else:
        print_status("warning", "X.com API credentials not fully configured (oracle functionality limited)")
        warnings += 1
    
    # Summary
    print(f"\n{Colors.BOLD}Validation Summary{Colors.RESET}")
    print(f"Errors: {errors}")
    print(f"Warnings: {warnings}")
    
    if errors == 0:
        if warnings == 0:
            print_status("success", "All test wallet configuration is valid! ✨")
            print(f"\n{Colors.BLUE}Next steps:{Colors.RESET}")
            print("1. Navigate to /test-manager/login")
            print("2. Enter your TEST_MANAGER_PASSCODE")
            print("3. Run the E2E test suite")
        else:
            print_status("warning", "Configuration is valid but has warnings")
            print("\nConsider addressing the warnings before running tests.")
        return 0
    else:
        print_status("error", "Configuration has errors that must be fixed")
        print(f"\n{Colors.YELLOW}To fix errors:{Colors.RESET}")
        print("1. Review the error messages above")
        print("2. Set missing environment variables in Replit Secrets")
        print("3. Ensure wallets have sufficient BASE Sepolia ETH")
        print("4. Run this script again to verify")
        return 1

if __name__ == "__main__":
    sys.exit(main())