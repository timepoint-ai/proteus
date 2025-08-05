#!/usr/bin/env python3
"""
Blockchain Test Data Generator for BASE Sepolia
Replaces database test data generation with on-chain transactions
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta
from decimal import Decimal
from web3 import Web3
from eth_account import Account
import random
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BlockchainTestDataGenerator:
    """Generate test data directly on BASE Sepolia blockchain"""
    
    def __init__(self):
        # Load configuration
        self.rpc_url = os.environ.get('BASE_RPC_URL', 'https://base-sepolia.g.alchemy.com/public')
        self.chain_id = int(os.environ.get('BASE_CHAIN_ID', '84532'))
        
        # Initialize Web3
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        if not self.w3.is_connected():
            raise Exception("Failed to connect to BASE Sepolia")
        
        logger.info(f"Connected to BASE Sepolia at {self.rpc_url}")
        
        # Load test wallets
        with open('.test_wallets.json', 'r') as f:
            self.test_wallets = json.load(f)
        
        # Create account from private key
        self.main_account = Account.from_key(self.test_wallets['main_wallet']['private_key'])
        logger.info(f"Using main wallet: {self.main_account.address}")
        
        # Load contract addresses and ABIs
        self.load_contracts()
        
    def load_contracts(self):
        """Load deployed contract addresses and ABIs"""
        # Contract addresses from README.md
        self.contracts = {
            'EnhancedPredictionMarket': '0x6B67Cb0DaAf78f63BD11195Df0FD9FFe4361b93C',
            'DecentralizedOracle': '0x7EF22e27D44E3f4Cc2f133BB4ab2065D180be3C1',
            'ActorRegistry': '0xC71CC19C5573C5E1E144829800cD0005D0eDB723',
            'PayoutManager': '0x88d399C949Ff2f1aaa8eA5a859Ae4d97c74f6871'
        }
        
        # Load ABIs from artifacts directory
        self.abis = {}
        artifacts_dir = './artifacts'
        for contract_name in self.contracts.keys():
            abi_path = os.path.join(artifacts_dir, f'{contract_name}.json')
            if os.path.exists(abi_path):
                with open(abi_path, 'r') as f:
                    artifact = json.load(f)
                    self.abis[contract_name] = artifact['abi']
                    logger.info(f"Loaded ABI for {contract_name}")
            else:
                logger.warning(f"ABI file not found for {contract_name}: {abi_path}")
    
    def register_test_actors(self, count=5):
        """Register test actors on blockchain"""
        logger.info(f"Registering {count} test actors...")
        
        if 'ActorRegistry' not in self.abis:
            logger.error("ActorRegistry ABI not loaded")
            return []
        
        # Get contract instance
        actor_registry = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.contracts['ActorRegistry']),
            abi=self.abis['ActorRegistry']
        )
        
        test_actors = [
            ("elonmusk_test", "Test Elon Musk", "Test tech entrepreneur"),
            ("taylorswift13_test", "Test Taylor Swift", "Test pop artist"),
            ("POTUS_test", "Test President", "Test government official"),
            ("Oprah_test", "Test Oprah", "Test media personality"),
            ("BillGates_test", "Test Bill Gates", "Test philanthropist")
        ]
        
        registered_actors = []
        
        for i, (username, display_name, bio) in enumerate(test_actors[:count]):
            try:
                # Check if actor already exists
                actor_id = actor_registry.functions.getActorByUsername(username).call()
                if actor_id != '':
                    logger.info(f"Actor {username} already registered with ID: {actor_id}")
                    registered_actors.append((actor_id, username))
                    continue
                
                # Build transaction
                nonce = self.w3.eth.get_transaction_count(self.main_account.address)
                
                tx = actor_registry.functions.registerActor(
                    username,
                    display_name,
                    bio,
                    True  # is_test_account
                ).build_transaction({
                    'from': self.main_account.address,
                    'nonce': nonce,
                    'gas': 300000,
                    'gasPrice': self.w3.eth.gas_price,
                    'chainId': self.chain_id
                })
                
                # Sign and send transaction
                signed_tx = self.main_account.sign_transaction(tx)
                tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                
                logger.info(f"Registering actor {username}, tx: {tx_hash.hex()}")
                
                # Wait for confirmation
                receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
                
                if receipt.status == 1:
                    # Get actor ID from event logs
                    logs = actor_registry.events.ActorRegistered().process_receipt(receipt)
                    if logs:
                        actor_id = logs[0]['args']['actorId']
                        logger.info(f"Successfully registered actor {username} with ID: {actor_id}")
                        registered_actors.append((actor_id, username))
                else:
                    logger.error(f"Failed to register actor {username}")
                    
            except Exception as e:
                logger.error(f"Error registering actor {username}: {e}")
                
        return registered_actors
    
    def create_test_markets(self, actors, count=3):
        """Create test prediction markets"""
        logger.info(f"Creating {count} test markets...")
        
        if 'EnhancedPredictionMarket' not in self.abis:
            logger.error("EnhancedPredictionMarket ABI not loaded")
            return []
        
        # Get contract instance
        market_contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.contracts['EnhancedPredictionMarket']),
            abi=self.abis['EnhancedPredictionMarket']
        )
        
        created_markets = []
        
        for i in range(min(count, len(actors))):
            actor_id, username = actors[i]
            
            try:
                # Create time window
                start_time = int((datetime.utcnow() + timedelta(hours=1)).timestamp())
                end_time = int((datetime.utcnow() + timedelta(hours=24)).timestamp())
                
                # Use test oracle wallets
                oracle_wallets = self.test_wallets['oracle_wallets'][:3]
                
                # Build transaction
                nonce = self.w3.eth.get_transaction_count(self.main_account.address)
                
                tx = market_contract.functions.createMarket(
                    actor_id,
                    start_time,
                    end_time,
                    oracle_wallets
                ).build_transaction({
                    'from': self.main_account.address,
                    'nonce': nonce,
                    'gas': 500000,
                    'gasPrice': self.w3.eth.gas_price,
                    'chainId': self.chain_id,
                    'value': Web3.to_wei(0.01, 'ether')  # Platform fee
                })
                
                # Sign and send transaction
                signed_tx = self.main_account.sign_transaction(tx)
                tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                
                logger.info(f"Creating market for {username}, tx: {tx_hash.hex()}")
                
                # Wait for confirmation
                receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
                
                if receipt.status == 1:
                    # Get market ID from event logs
                    logs = market_contract.events.MarketCreated().process_receipt(receipt)
                    if logs:
                        market_id = logs[0]['args']['marketId']
                        logger.info(f"Successfully created market {market_id} for {username}")
                        created_markets.append({
                            'market_id': market_id,
                            'actor_id': actor_id,
                            'username': username,
                            'start_time': start_time,
                            'end_time': end_time
                        })
                else:
                    logger.error(f"Failed to create market for {username}")
                    
            except Exception as e:
                logger.error(f"Error creating market for {username}: {e}")
                
        return created_markets
    
    def create_test_submissions(self, markets):
        """Create test submissions for markets"""
        logger.info("Creating test submissions...")
        
        if 'EnhancedPredictionMarket' not in self.abis:
            logger.error("EnhancedPredictionMarket ABI not loaded")
            return []
        
        # Get contract instance
        market_contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.contracts['EnhancedPredictionMarket']),
            abi=self.abis['EnhancedPredictionMarket']
        )
        
        test_predictions = [
            "I think blockchain will revolutionize finance by 2030",
            "AI will be integrated into every aspect of our lives",
            "The future of transportation is autonomous vehicles",
            "Climate change requires immediate global action",
            "Space exploration will become commercially viable"
        ]
        
        submissions = []
        
        for market in markets:
            market_id = market['market_id']
            username = market['username']
            
            # Create 2-3 submissions per market
            num_submissions = random.randint(2, 3)
            
            for i in range(num_submissions):
                try:
                    # First submission is original, others are competitors
                    submission_type = 0 if i == 0 else 1  # 0=original, 1=competitor
                    predicted_text = random.choice(test_predictions)
                    
                    # Build transaction
                    nonce = self.w3.eth.get_transaction_count(self.main_account.address)
                    
                    tx = market_contract.functions.createSubmission(
                        market_id,
                        predicted_text,
                        submission_type
                    ).build_transaction({
                        'from': self.main_account.address,
                        'nonce': nonce,
                        'gas': 300000,
                        'gasPrice': self.w3.eth.gas_price,
                        'chainId': self.chain_id,
                        'value': Web3.to_wei(0.01, 'ether')  # Stake amount
                    })
                    
                    # Sign and send transaction
                    signed_tx = self.main_account.sign_transaction(tx)
                    tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                    
                    logger.info(f"Creating submission for market {market_id}, tx: {tx_hash.hex()}")
                    
                    # Wait for confirmation
                    receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
                    
                    if receipt.status == 1:
                        # Get submission ID from event logs
                        logs = market_contract.events.SubmissionCreated().process_receipt(receipt)
                        if logs:
                            submission_id = logs[0]['args']['submissionId']
                            logger.info(f"Created submission {submission_id} for market {market_id}")
                            submissions.append({
                                'submission_id': submission_id,
                                'market_id': market_id,
                                'predicted_text': predicted_text,
                                'type': 'original' if submission_type == 0 else 'competitor'
                            })
                    else:
                        logger.error(f"Failed to create submission for market {market_id}")
                        
                except Exception as e:
                    logger.error(f"Error creating submission: {e}")
                    
        return submissions
    
    def place_test_bets(self, submissions):
        """Place test bets on submissions"""
        logger.info("Placing test bets...")
        
        if 'EnhancedPredictionMarket' not in self.abis:
            logger.error("EnhancedPredictionMarket ABI not loaded")
            return []
        
        # Get contract instance
        market_contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.contracts['EnhancedPredictionMarket']),
            abi=self.abis['EnhancedPredictionMarket']
        )
        
        bets = []
        
        # Place 1-2 bets on each submission
        for submission in submissions:
            num_bets = random.randint(1, 2)
            
            for i in range(num_bets):
                try:
                    # Random bet amount between 0.005 and 0.02 ETH
                    bet_amount = random.uniform(0.005, 0.02)
                    
                    # Build transaction
                    nonce = self.w3.eth.get_transaction_count(self.main_account.address)
                    
                    tx = market_contract.functions.placeBet(
                        submission['submission_id']
                    ).build_transaction({
                        'from': self.main_account.address,
                        'nonce': nonce,
                        'gas': 200000,
                        'gasPrice': self.w3.eth.gas_price,
                        'chainId': self.chain_id,
                        'value': Web3.to_wei(bet_amount, 'ether')
                    })
                    
                    # Sign and send transaction
                    signed_tx = self.main_account.sign_transaction(tx)
                    tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                    
                    logger.info(f"Placing bet on submission {submission['submission_id']}, tx: {tx_hash.hex()}")
                    
                    # Wait for confirmation
                    receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
                    
                    if receipt.status == 1:
                        logger.info(f"Successfully placed bet of {bet_amount} ETH")
                        bets.append({
                            'submission_id': submission['submission_id'],
                            'amount': bet_amount,
                            'tx_hash': tx_hash.hex()
                        })
                    else:
                        logger.error(f"Failed to place bet")
                        
                except Exception as e:
                    logger.error(f"Error placing bet: {e}")
                    
        return bets
    
    def generate_full_test_dataset(self):
        """Generate complete test dataset on blockchain"""
        logger.info("Starting full test dataset generation...")
        
        # Check wallet balance
        balance = self.w3.eth.get_balance(self.main_account.address)
        logger.info(f"Wallet balance: {Web3.from_wei(balance, 'ether')} ETH")
        
        if balance < Web3.to_wei(0.1, 'ether'):
            logger.error("Insufficient balance. Need at least 0.1 ETH for test data generation")
            return
        
        # 1. Register test actors
        actors = self.register_test_actors(count=3)
        if not actors:
            logger.error("No actors registered, aborting")
            return
        
        # 2. Create test markets
        markets = self.create_test_markets(actors, count=3)
        if not markets:
            logger.error("No markets created, aborting")
            return
        
        # 3. Create test submissions
        submissions = self.create_test_submissions(markets)
        if not submissions:
            logger.error("No submissions created, aborting")
            return
        
        # 4. Place test bets
        bets = self.place_test_bets(submissions)
        
        # Summary
        logger.info("Test data generation complete!")
        logger.info(f"Created {len(actors)} actors, {len(markets)} markets, {len(submissions)} submissions, {len(bets)} bets")
        
        # Save test data info
        test_data = {
            'generated_at': datetime.utcnow().isoformat(),
            'chain_id': self.chain_id,
            'actors': actors,
            'markets': markets,
            'submissions': submissions,
            'bets': bets
        }
        
        with open('blockchain_test_data.json', 'w') as f:
            json.dump(test_data, f, indent=2)
        
        logger.info("Test data info saved to blockchain_test_data.json")


def main():
    """Main entry point"""
    generator = BlockchainTestDataGenerator()
    generator.generate_full_test_dataset()


if __name__ == '__main__':
    main()