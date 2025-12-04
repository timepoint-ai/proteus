#!/usr/bin/env python3
"""
Clean Blockchain Test Data
Removes test actors and associated data from the blockchain
"""

import os
import sys
import json
import logging
from web3 import Web3
from eth_account import Account

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BlockchainTestDataCleaner:
    """Clean test data from BASE Sepolia blockchain"""
    
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
            'ActorRegistry': '0xC71CC19C5573C5E1E144829800cD0005D0eDB723',
            'EnhancedPredictionMarket': '0x6B67Cb0DaAf78f63BD11195Df0FD9FFe4361b93C'
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
    
    def get_test_actors(self):
        """Get all test actors from blockchain"""
        if 'ActorRegistry' not in self.abis:
            logger.error("ActorRegistry ABI not loaded")
            return []
        
        # Get contract instance
        actor_registry = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.contracts['ActorRegistry']),
            abi=self.abis['ActorRegistry']
        )
        
        test_actors = []
        
        # Known test actor usernames
        test_usernames = [
            "elonmusk_test",
            "taylorswift13_test", 
            "POTUS_test",
            "Oprah_test",
            "BillGates_test"
        ]
        
        for username in test_usernames:
            try:
                actor_id = actor_registry.functions.getActorByUsername(username).call()
                if actor_id and actor_id != '':
                    # Get actor details
                    actor = actor_registry.functions.getActor(actor_id).call()
                    if actor[5]:  # is_test_account flag
                        test_actors.append({
                            'id': actor_id,
                            'username': username,
                            'display_name': actor[1]
                        })
                        logger.info(f"Found test actor: {username} (ID: {actor_id})")
            except Exception as e:
                logger.debug(f"Actor {username} not found or error: {e}")
        
        return test_actors
    
    def deactivate_test_actors(self, test_actors):
        """Deactivate test actors (can't delete, but can mark inactive)"""
        if 'ActorRegistry' not in self.abis:
            logger.error("ActorRegistry ABI not loaded")
            return
        
        # Get contract instance
        actor_registry = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.contracts['ActorRegistry']),
            abi=self.abis['ActorRegistry']
        )
        
        for actor in test_actors:
            try:
                # Check if contract has deactivateActor function
                if hasattr(actor_registry.functions, 'deactivateActor'):
                    # Build transaction
                    nonce = self.w3.eth.get_transaction_count(self.main_account.address)
                    
                    tx = actor_registry.functions.deactivateActor(
                        actor['id']
                    ).build_transaction({
                        'from': self.main_account.address,
                        'nonce': nonce,
                        'gas': 100000,
                        'gasPrice': self.w3.eth.gas_price,
                        'chainId': self.chain_id
                    })
                    
                    # Sign and send transaction
                    signed_tx = self.main_account.sign_transaction(tx)
                    tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                    
                    logger.info(f"Deactivating actor {actor['username']}, tx: {tx_hash.hex()}")
                    
                    # Wait for confirmation
                    receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
                    
                    if receipt.status == 1:
                        logger.info(f"Successfully deactivated actor {actor['username']}")
                    else:
                        logger.error(f"Failed to deactivate actor {actor['username']}")
                else:
                    logger.info(f"Contract doesn't support deactivation, skipping {actor['username']}")
                    
            except Exception as e:
                logger.error(f"Error deactivating actor {actor['username']}: {e}")
    
    def get_test_markets(self, test_actors):
        """Get all markets for test actors"""
        if 'EnhancedPredictionMarket' not in self.abis:
            logger.error("EnhancedPredictionMarket ABI not loaded")
            return []
        
        # Get contract instance
        market_contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.contracts['EnhancedPredictionMarket']),
            abi=self.abis['EnhancedPredictionMarket']
        )
        
        test_markets = []
        
        for actor in test_actors:
            try:
                # Get markets for this actor
                markets = market_contract.functions.getMarketsByActor(actor['id']).call()
                for market_id in markets:
                    market = market_contract.functions.getMarket(market_id).call()
                    test_markets.append({
                        'id': market_id,
                        'actor_id': actor['id'],
                        'actor_username': actor['username'],
                        'status': market[5]  # Assuming status is at index 5
                    })
                    logger.info(f"Found test market {market_id} for {actor['username']}")
            except Exception as e:
                logger.debug(f"Error getting markets for {actor['username']}: {e}")
        
        return test_markets
    
    def clean_all_test_data(self):
        """Clean all test data from blockchain"""
        logger.info("Starting blockchain test data cleanup...")
        
        # 1. Get test actors
        test_actors = self.get_test_actors()
        logger.info(f"Found {len(test_actors)} test actors")
        
        if not test_actors:
            logger.info("No test actors found, nothing to clean")
            return
        
        # 2. Get test markets
        test_markets = self.get_test_markets(test_actors)
        logger.info(f"Found {len(test_markets)} test markets")
        
        # 3. Deactivate test actors (markets will be handled by contract logic)
        self.deactivate_test_actors(test_actors)
        
        # Summary
        logger.info("Test data cleanup complete!")
        logger.info(f"Processed {len(test_actors)} actors and {len(test_markets)} markets")
        
        # Load and update test data file if it exists
        if os.path.exists('blockchain_test_data.json'):
            with open('blockchain_test_data.json', 'r') as f:
                test_data = json.load(f)
            
            test_data['cleaned_at'] = datetime.now(timezone.utc).isoformat()
            test_data['cleaned_actors'] = len(test_actors)
            test_data['cleaned_markets'] = len(test_markets)
            
            with open('blockchain_test_data.json', 'w') as f:
                json.dump(test_data, f, indent=2)


def main():
    """Main entry point"""
    cleaner = BlockchainTestDataCleaner()
    cleaner.clean_all_test_data()


if __name__ == '__main__':
    from datetime import datetime, timezone
    main()