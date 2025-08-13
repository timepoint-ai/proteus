#!/usr/bin/env python3
"""
Create test transactions on BASE Sepolia blockchain
Phase 7 Complete - Fully decentralized test transactions
"""

import json
import os
import sys
import time
from datetime import datetime, timedelta
from web3 import Web3
from eth_account import Account
import random

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
print(f"Connected to BASE Sepolia: {w3.is_connected()}")
print(f"Chain ID: {w3.eth.chain_id}")

# Test accounts
main_account = Account.from_key(main_test_wallet['privateKey'])
oracle_accounts = [
    Account.from_key('0x' + key if not key.startswith('0x') else key) 
    for key in test_wallets['oracle_private_keys']
]

print(f"\nTest Wallets:")
print(f"Main wallet: {main_account.address}")
print(f"Oracle wallets: {[acc.address for acc in oracle_accounts]}")

# Contract addresses
prediction_market_address = deployment['contracts']['EnhancedPredictionMarket']['address']
actor_registry_address = deployment['contracts']['ActorRegistry']['address']
oracle_address = deployment['contracts']['DecentralizedOracle']['address']

print(f"\nContract Addresses:")
print(f"PredictionMarket: {prediction_market_address}")
print(f"ActorRegistry: {actor_registry_address}")
print(f"Oracle: {oracle_address}")

# Load contract ABIs
def load_abi(contract_name):
    abi_path = f'artifacts/contracts/src/{contract_name}.sol/{contract_name}.json'
    with open(abi_path, 'r') as f:
        return json.load(f)['abi']

# Initialize contracts
prediction_market_abi = load_abi('EnhancedPredictionMarket')
actor_registry_abi = load_abi('ActorRegistry')
oracle_abi = load_abi('DecentralizedOracle')

prediction_market = w3.eth.contract(
    address=Web3.to_checksum_address(prediction_market_address),
    abi=prediction_market_abi
)

actor_registry = w3.eth.contract(
    address=Web3.to_checksum_address(actor_registry_address),
    abi=actor_registry_abi
)

oracle_contract = w3.eth.contract(
    address=Web3.to_checksum_address(oracle_address),
    abi=oracle_abi
)

def send_transaction(account, contract_function, value=0):
    """Send a transaction and wait for receipt"""
    try:
        # Get current nonce
        nonce = w3.eth.get_transaction_count(account.address)
        
        # Build transaction
        tx = contract_function.build_transaction({
            'from': account.address,
            'value': value,
            'gas': 500000,
            'gasPrice': w3.eth.gas_price,
            'nonce': nonce,
            'chainId': 84532  # BASE Sepolia
        })
        
        # Sign and send
        signed_tx = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        print(f"Transaction sent: {tx_hash.hex()}")
        
        # Wait for receipt
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
        
        if receipt['status'] == 1:
            print(f"✅ Transaction successful! Gas used: {receipt['gasUsed']}")
            return receipt
        else:
            print(f"❌ Transaction failed!")
            return None
            
    except Exception as e:
        print(f"❌ Error sending transaction: {str(e)}")
        return None

def check_balances():
    """Check ETH balances of test wallets"""
    print("\n🔍 Checking wallet balances...")
    
    main_balance = w3.eth.get_balance(main_account.address)
    print(f"Main wallet ({main_account.address}): {Web3.from_wei(main_balance, 'ether')} ETH")
    
    for i, acc in enumerate(oracle_accounts[:1]):  # Check first oracle only
        balance = w3.eth.get_balance(acc.address)
        print(f"Oracle {i+1} ({acc.address}): {Web3.from_wei(balance, 'ether')} ETH")
    
    if main_balance == 0:
        print("\n⚠️ Main wallet has no ETH! Please fund it at: https://base-sepolia.blockscout.com/faucet")
        return False
    return True

def create_test_market():
    """Create a test prediction market"""
    print("\n📊 Creating test market...")
    
    # Market parameters
    actor_id = 1  # Elon Musk
    description = f"Test market created at {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    end_time = int((datetime.now() + timedelta(hours=24)).timestamp())
    
    print(f"Actor ID: {actor_id}")
    print(f"Description: {description}")
    print(f"End time: {datetime.fromtimestamp(end_time)}")
    
    # Create market transaction
    create_market_fn = prediction_market.functions.createMarket(
        actor_id,
        description,
        end_time
    )
    
    receipt = send_transaction(main_account, create_market_fn)
    
    if receipt:
        # Parse events
        events = prediction_market.events.MarketCreated().process_receipt(receipt)
        if events:
            market_id = events[0]['args']['marketId']
            print(f"✅ Market created with ID: {market_id}")
            return market_id
    
    return None

def create_submission(market_id):
    """Create a submission for a market"""
    print(f"\n📝 Creating submission for market {market_id}...")
    
    # Submission parameters
    predicted_texts = [
        "Mars is the future",
        "Going to Mars soon",
        "We need to go to Mars",
        "Mars colonization is essential"
    ]
    predicted_text = random.choice(predicted_texts)
    stake_amount = Web3.to_wei(0.001, 'ether')  # 0.001 ETH stake
    
    print(f"Predicted text: '{predicted_text}'")
    print(f"Stake amount: {Web3.from_wei(stake_amount, 'ether')} ETH")
    
    # Create submission transaction
    create_submission_fn = prediction_market.functions.createSubmission(
        market_id,
        predicted_text
    )
    
    receipt = send_transaction(oracle_accounts[0], create_submission_fn, value=stake_amount)
    
    if receipt:
        # Parse events
        events = prediction_market.events.SubmissionCreated().process_receipt(receipt)
        if events:
            submission_id = events[0]['args']['submissionId']
            print(f"✅ Submission created with ID: {submission_id}")
            return submission_id
    
    return None

def place_bet(market_id, submission_id):
    """Place a bet on a submission"""
    print(f"\n💰 Placing bet on submission {submission_id} in market {market_id}...")
    
    bet_amount = Web3.to_wei(0.0005, 'ether')  # 0.0005 ETH bet
    print(f"Bet amount: {Web3.from_wei(bet_amount, 'ether')} ETH")
    
    # Place bet transaction
    place_bet_fn = prediction_market.functions.placeBet(
        market_id,
        submission_id
    )
    
    # Use a different account for betting
    betting_account = oracle_accounts[1] if len(oracle_accounts) > 1 else main_account
    receipt = send_transaction(betting_account, place_bet_fn, value=bet_amount)
    
    if receipt:
        print(f"✅ Bet placed successfully!")
        return True
    
    return False

def get_market_stats():
    """Get and display market statistics"""
    print("\n📈 Fetching market statistics...")
    
    try:
        # Get total markets
        total_markets = prediction_market.functions.marketIdCounter().call()
        print(f"Total markets: {total_markets}")
        
        # Get recent market details if any exist
        if total_markets > 0:
            latest_market_id = total_markets - 1
            market = prediction_market.functions.markets(latest_market_id).call()
            
            print(f"\nLatest Market (ID: {latest_market_id}):")
            print(f"  Actor ID: {market[0]}")
            print(f"  Description: {market[1]}")
            print(f"  End time: {datetime.fromtimestamp(market[2])}")
            print(f"  Total pool: {Web3.from_wei(market[3], 'ether')} ETH")
            print(f"  Resolved: {market[4]}")
            
    except Exception as e:
        print(f"Error fetching stats: {str(e)}")

def main():
    """Main execution function"""
    print("=" * 60)
    print("CLOCKCHAIN TEST TRANSACTIONS")
    print("Phase 7 Complete - Fully Decentralized")
    print("=" * 60)
    
    # Check balances
    if not check_balances():
        print("\n⚠️ Please fund your test wallets before running transactions")
        print("Faucet: https://base-sepolia.blockscout.com/faucet")
        return
    
    # Get current stats
    get_market_stats()
    
    # Create a test market
    market_id = create_test_market()
    
    if market_id is not None:
        # Wait a bit for blockchain confirmation
        time.sleep(5)
        
        # Create a submission
        submission_id = create_submission(market_id)
        
        if submission_id is not None:
            # Wait a bit
            time.sleep(5)
            
            # Place a bet
            place_bet(market_id, submission_id)
    
    # Show final stats
    print("\n" + "=" * 60)
    get_market_stats()
    
    print("\n✅ Test transactions complete!")
    print("View on explorer: https://sepolia.basescan.org/")

if __name__ == "__main__":
    main()