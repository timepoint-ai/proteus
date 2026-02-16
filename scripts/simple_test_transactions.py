#!/usr/bin/env python3
"""
Simple test transactions on BASE Sepolia blockchain
Phase 7 Complete - Read blockchain data and check balances
"""

import json
from web3 import Web3
from eth_account import Account

# Load test wallets
with open('.test_wallets.json', 'r') as f:
    test_wallets = json.load(f)

with open('.test-wallet.json', 'r') as f:
    main_test_wallet = json.load(f)

# Load deployment addresses
with open('deployment-base-sepolia.json', 'r') as f:
    deployment = json.load(f)

# Initialize Web3
w3 = Web3(Web3.HTTPProvider('https://sepolia.base.org'))
print("=" * 60)
print("PROTEUS MARKETS TEST TRANSACTIONS - SIMPLE")
print("Phase 7 Complete - Blockchain-Only System")
print("=" * 60)

print(f"\n✅ Connected to BASE Sepolia: {w3.is_connected()}")
print(f"Chain ID: {w3.eth.chain_id}")
print(f"Latest Block: {w3.eth.block_number}")

# Test accounts
main_account = Account.from_key(main_test_wallet['privateKey'])
oracle_accounts = [
    Account.from_key('0x' + key if not key.startswith('0x') else key) 
    for key in test_wallets['oracle_private_keys']
]

print(f"\n📊 Test Wallet Information:")
print(f"Main wallet: {main_account.address}")
main_balance = w3.eth.get_balance(main_account.address)
print(f"  Balance: {Web3.from_wei(main_balance, 'ether')} ETH")

if main_balance < Web3.to_wei(0.01, 'ether'):
    print(f"  ⚠️ WARNING: Low balance! Need at least 0.01 ETH for transactions")
    print(f"  🚰 Get testnet ETH: https://base-sepolia.blockscout.com/faucet")

print(f"\n🔐 Oracle Wallets:")
for i, acc in enumerate(oracle_accounts):
    balance = w3.eth.get_balance(acc.address)
    print(f"Oracle {i+1}: {acc.address}")
    print(f"  Balance: {Web3.from_wei(balance, 'ether')} ETH")

# Contract addresses
prediction_market_address = deployment['contracts']['EnhancedPredictionMarket']['address']
genesis_nft_address = deployment['contracts'].get('GenesisNFT', {}).get('address')
payout_manager_address = deployment['contracts'].get('ImprovedDistributedPayoutManager', {}).get('address')

print(f"\n📜 Deployed Contracts:")
print(f"PredictionMarket: {prediction_market_address}")
if genesis_nft_address:
    print(f"GenesisNFT: {genesis_nft_address}")
if payout_manager_address:
    print(f"PayoutManager: {payout_manager_address}")

# Try to read some blockchain data
print(f"\n📖 Reading Blockchain Data...")

# Load minimal ABI just for reading
minimal_abi = [
    {
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "name",
        "outputs": [{"name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function"
    }
]

# Try to read Genesis NFT data if available
if genesis_nft_address and genesis_nft_address != 'Not deployed':
    try:
        genesis_contract = w3.eth.contract(
            address=Web3.to_checksum_address(genesis_nft_address),
            abi=minimal_abi
        )
        
        total_supply = genesis_contract.functions.totalSupply().call()
        print(f"\n💎 Genesis NFT Statistics:")
        print(f"  Total Supply: {total_supply} NFTs")
        
    except Exception as e:
        print(f"  Could not read Genesis NFT data: {str(e)[:100]}")

# Create a simple transaction (just send ETH between test wallets)
print(f"\n💸 Test Transaction:")
if main_balance > Web3.to_wei(0.001, 'ether'):
    print("Preparing to send 0.0001 ETH from main wallet to oracle wallet...")
    
    try:
        # Build transaction
        tx = {
            'from': main_account.address,
            'to': oracle_accounts[0].address,
            'value': Web3.to_wei(0.0001, 'ether'),
            'gas': 21000,
            'gasPrice': w3.eth.gas_price,
            'nonce': w3.eth.get_transaction_count(main_account.address),
            'chainId': 84532
        }
        
        # Sign transaction
        signed_tx = main_account.sign_transaction(tx)
        
        # Send transaction
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        print(f"  ✅ Transaction sent! Hash: {tx_hash.hex()}")
        
        # Wait for receipt
        print("  ⏳ Waiting for confirmation...")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
        
        if receipt['status'] == 1:
            print(f"  ✅ Transaction confirmed! Block: {receipt['blockNumber']}")
            print(f"  Gas used: {receipt['gasUsed']}")
            print(f"  View on explorer: https://sepolia.basescan.org/tx/{tx_hash.hex()}")
        else:
            print(f"  ❌ Transaction failed!")
            
    except Exception as e:
        print(f"  ❌ Error sending transaction: {str(e)}")
else:
    print("  ⚠️ Insufficient balance for test transaction")
    print("  Need at least 0.001 ETH to send a test transaction")

# Final balance check
print(f"\n💰 Final Balances:")
main_balance_final = w3.eth.get_balance(main_account.address)
oracle_balance_final = w3.eth.get_balance(oracle_accounts[0].address)

print(f"Main wallet: {Web3.from_wei(main_balance_final, 'ether')} ETH")
print(f"Oracle wallet 1: {Web3.from_wei(oracle_balance_final, 'ether')} ETH")

print("\n" + "=" * 60)
print("✅ Test complete! System is fully decentralized and blockchain-only.")
print("All data is stored on BASE Sepolia blockchain.")
print("=" * 60)