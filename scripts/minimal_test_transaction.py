#!/usr/bin/env python3
"""
Minimal test transaction with available balance
"""

import json
from web3 import Web3
from eth_account import Account

# Load test wallet
with open('.test-wallet.json', 'r') as f:
    main_test_wallet = json.load(f)

with open('.test_wallets.json', 'r') as f:
    test_wallets = json.load(f)

# Initialize Web3
w3 = Web3(Web3.HTTPProvider('https://sepolia.base.org'))

print("=" * 60)
print("MINIMAL TEST TRANSACTION - BASE SEPOLIA")
print("=" * 60)

# Test account
main_account = Account.from_key(main_test_wallet['privateKey'])
oracle_account = Account.from_key('0x' + test_wallets['oracle_private_keys'][0])

# Check balances
main_balance = w3.eth.get_balance(main_account.address)
oracle_balance = w3.eth.get_balance(oracle_account.address)

print(f"\n📊 Initial Balances:")
print(f"Main wallet: {main_account.address}")
print(f"  Balance: {Web3.from_wei(main_balance, 'ether')} ETH")
print(f"Oracle wallet: {oracle_account.address}")
print(f"  Balance: {Web3.from_wei(oracle_balance, 'ether')} ETH")

# Calculate transaction amount (send half of available, minus gas)
gas_price = w3.eth.gas_price
gas_limit = 21000
gas_cost = gas_price * gas_limit
available = main_balance - gas_cost

if available > 0:
    # Send 50% of available after gas
    send_amount = available // 2
    
    print(f"\n💸 Sending Transaction:")
    print(f"  Amount: {Web3.from_wei(send_amount, 'ether')} ETH")
    print(f"  Gas: {Web3.from_wei(gas_cost, 'ether')} ETH")
    
    try:
        # Build transaction
        tx = {
            'from': main_account.address,
            'to': oracle_account.address,
            'value': send_amount,
            'gas': gas_limit,
            'gasPrice': gas_price,
            'nonce': w3.eth.get_transaction_count(main_account.address),
            'chainId': 84532
        }
        
        # Sign and send
        signed_tx = main_account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        print(f"  ✅ Transaction sent!")
        print(f"  Hash: {tx_hash.hex()}")
        
        # Wait for confirmation
        print("  ⏳ Waiting for confirmation...")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
        
        if receipt['status'] == 1:
            print(f"  ✅ Transaction confirmed!")
            print(f"  Block: {receipt['blockNumber']}")
            print(f"  Gas used: {receipt['gasUsed']}")
            
            # Check final balances
            main_balance_final = w3.eth.get_balance(main_account.address)
            oracle_balance_final = w3.eth.get_balance(oracle_account.address)
            
            print(f"\n📊 Final Balances:")
            print(f"Main wallet: {Web3.from_wei(main_balance_final, 'ether')} ETH")
            print(f"Oracle wallet: {Web3.from_wei(oracle_balance_final, 'ether')} ETH")
            
            print(f"\n🔗 View on Explorer:")
            print(f"https://sepolia.basescan.org/tx/{tx_hash.hex()}")
            
        else:
            print(f"  ❌ Transaction failed!")
            
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        
else:
    print(f"\n⚠️ Insufficient balance for transaction")
    print(f"Available after gas: {Web3.from_wei(available, 'ether')} ETH")
    print(f"Please fund wallet at: https://base-sepolia.blockscout.com/faucet")

print("\n" + "=" * 60)
print("✅ Test complete!")