"""
Actor Registry Service for Phase 9
Manages interaction with on-chain ActorRegistry smart contract
"""

import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from web3 import Web3
from web3.exceptions import ContractLogicError
from eth_account import Account
import logging
import os

from services.blockchain_base import BaseBlockchainService

logger = logging.getLogger(__name__)


class ActorRegistryService:
    """Service for interacting with on-chain ActorRegistry"""
    
    def __init__(self):
        self.blockchain = BaseBlockchainService()
        self.w3 = self.blockchain.w3
        
        # Load contract address and ABI
        self.contract_address = os.getenv('ACTOR_REGISTRY_ADDRESS')
        if not self.contract_address:
            raise ValueError("ACTOR_REGISTRY_ADDRESS not set in environment")
            
        # Load ABI from compiled contract
        abi_path = './contracts/artifacts/contracts/src/ActorRegistry.sol/ActorRegistry.json'
        try:
            with open(abi_path, 'r') as f:
                contract_json = json.load(f)
                self.contract_abi = contract_json['abi']
        except FileNotFoundError:
            logger.warning(f"ABI file not found at {abi_path}, using minimal ABI")
            self.contract_abi = self._get_minimal_abi()
            
        # Initialize contract
        self.contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.contract_address),
            abi=self.contract_abi
        )
        
        # Cache for gas estimates
        self.gas_estimates = {
            'propose_actor': 300000,
            'vote_proposal': 150000,
            'update_actor': 200000
        }
        
    def _get_minimal_abi(self) -> list:
        """Return minimal ABI for ActorRegistry contract"""
        return [
            {
                "inputs": [{"name": "_xUsername", "type": "string"}],
                "name": "actorExists",
                "outputs": [{"name": "", "type": "bool"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [{"name": "_xUsername", "type": "string"}],
                "name": "isActorActive",
                "outputs": [{"name": "", "type": "bool"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [{"name": "_xUsername", "type": "string"}],
                "name": "getActor",
                "outputs": [
                    {"name": "displayName", "type": "string"},
                    {"name": "bio", "type": "string"},
                    {"name": "verified", "type": "bool"},
                    {"name": "followerCount", "type": "uint256"},
                    {"name": "active", "type": "bool"},
                    {"name": "approvalCount", "type": "uint256"},
                    {"name": "registrationTime", "type": "uint256"},
                    {"name": "isTestAccount", "type": "bool"}
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "getActiveActors",
                "outputs": [{"name": "", "type": "string[]"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": True, "name": "xUsername", "type": "string"},
                    {"indexed": True, "name": "proposer", "type": "address"},
                    {"indexed": False, "name": "proposalId", "type": "bytes32"}
                ],
                "name": "ActorProposed",
                "type": "event"
            },
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": True, "name": "xUsername", "type": "string"},
                    {"indexed": False, "name": "approvalCount", "type": "uint256"}
                ],
                "name": "ActorActivated",
                "type": "event"
            }
        ]
        
    def check_actor_exists(self, x_username: str) -> bool:
        """Check if an actor exists on-chain"""
        try:
            return self.contract.functions.actorExists(x_username).call()
        except Exception as e:
            logger.error(f"Error checking actor existence: {e}")
            return False
            
    def is_actor_active(self, x_username: str) -> bool:
        """Check if an actor is active on-chain"""
        try:
            return self.contract.functions.isActorActive(x_username).call()
        except Exception as e:
            logger.error(f"Error checking actor active status: {e}")
            return False
            
    def get_actor(self, x_username: str) -> Optional[Dict]:
        """Get actor details from blockchain"""
        try:
            result = self.contract.functions.getActor(x_username).call()
            return {
                'x_username': x_username,
                'display_name': result[0],
                'bio': result[1],
                'verified': result[2],
                'follower_count': result[3],
                'active': result[4],
                'approval_count': result[5],
                'registration_time': datetime.fromtimestamp(result[6]),
                'is_test_account': result[7]
            }
        except Exception as e:
            logger.error(f"Error getting actor {x_username}: {e}")
            return None
            
    def get_all_active_actors(self) -> List[str]:
        """Get list of all active actor usernames"""
        try:
            return self.contract.functions.getActiveActors().call()
        except Exception as e:
            logger.error(f"Error getting active actors: {e}")
            return []
            
    def propose_actor(
        self,
        node_wallet_address: str,
        node_private_key: str,
        x_username: str,
        display_name: str,
        bio: str,
        profile_image_url: str,
        verified: bool,
        follower_count: int,
        is_test_account: bool = False
    ) -> Optional[str]:
        """Propose a new actor (requires node operator)"""
        try:
            # Check if actor already exists
            if self.check_actor_exists(x_username):
                logger.warning(f"Actor {x_username} already exists")
                return None
                
            # Build transaction
            account = Account.from_key(node_private_key)
            nonce = self.w3.eth.get_transaction_count(account.address)
            
            # Estimate gas
            gas_price = self.w3.eth.gas_price
            gas_limit = self.gas_estimates['propose_actor']
            
            # Build transaction
            transaction = self.contract.functions.proposeActor(
                x_username,
                display_name,
                bio,
                profile_image_url,
                verified,
                follower_count,
                is_test_account
            ).build_transaction({
                'from': account.address,
                'nonce': nonce,
                'gas': gas_limit,
                'gasPrice': gas_price,
                'chainId': self.blockchain.chain_id
            })
            
            # Sign and send transaction
            signed_txn = self.w3.eth.account.sign_transaction(transaction, node_private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt['status'] == 1:
                logger.info(f"Actor {x_username} proposed successfully. Tx: {tx_hash.hex()}")
                return tx_hash.hex()
            else:
                logger.error(f"Transaction failed for proposing actor {x_username}")
                return None
                
        except Exception as e:
            logger.error(f"Error proposing actor: {e}")
            return None
            
    def vote_on_proposal(
        self,
        node_wallet_address: str,
        node_private_key: str,
        proposal_id: bytes,
        support: bool
    ) -> Optional[str]:
        """Vote on an actor proposal (requires node operator)"""
        try:
            # Build transaction
            account = Account.from_key(node_private_key)
            nonce = self.w3.eth.get_transaction_count(account.address)
            
            # Estimate gas
            gas_price = self.w3.eth.gas_price
            gas_limit = self.gas_estimates['vote_proposal']
            
            # Build transaction
            transaction = self.contract.functions.voteOnProposal(
                proposal_id,
                support
            ).build_transaction({
                'from': account.address,
                'nonce': nonce,
                'gas': gas_limit,
                'gasPrice': gas_price,
                'chainId': self.blockchain.chain_id
            })
            
            # Sign and send transaction
            signed_txn = self.w3.eth.account.sign_transaction(transaction, node_private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt['status'] == 1:
                logger.info(f"Vote cast successfully. Tx: {tx_hash.hex()}")
                return tx_hash.hex()
            else:
                logger.error("Transaction failed for voting on proposal")
                return None
                
        except Exception as e:
            logger.error(f"Error voting on proposal: {e}")
            return None
            
    def update_actor(
        self,
        node_wallet_address: str,
        node_private_key: str,
        x_username: str,
        display_name: str,
        bio: str,
        profile_image_url: str,
        verified: bool,
        follower_count: int
    ) -> Optional[str]:
        """Update actor information (requires node operator)"""
        try:
            # Check if actor exists and is active
            if not self.is_actor_active(x_username):
                logger.warning(f"Actor {x_username} is not active")
                return None
                
            # Build transaction
            account = Account.from_key(node_private_key)
            nonce = self.w3.eth.get_transaction_count(account.address)
            
            # Estimate gas
            gas_price = self.w3.eth.gas_price
            gas_limit = self.gas_estimates['update_actor']
            
            # Build transaction
            transaction = self.contract.functions.updateActor(
                x_username,
                display_name,
                bio,
                profile_image_url,
                verified,
                follower_count
            ).build_transaction({
                'from': account.address,
                'nonce': nonce,
                'gas': gas_limit,
                'gasPrice': gas_price,
                'chainId': self.blockchain.chain_id
            })
            
            # Sign and send transaction
            signed_txn = self.w3.eth.account.sign_transaction(transaction, node_private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt['status'] == 1:
                logger.info(f"Actor {x_username} updated successfully. Tx: {tx_hash.hex()}")
                return tx_hash.hex()
            else:
                logger.error(f"Transaction failed for updating actor {x_username}")
                return None
                
        except Exception as e:
            logger.error(f"Error updating actor: {e}")
            return None
            
    def sync_actor_from_database(self, actor_db_model) -> bool:
        """Sync an actor from database to blockchain"""
        try:
            # Check if actor already exists on-chain
            if self.check_actor_exists(actor_db_model.x_username):
                # Update if needed
                on_chain = self.get_actor(actor_db_model.x_username)
                if on_chain and on_chain['active']:
                    # Check if update needed
                    if (on_chain['follower_count'] != actor_db_model.follower_count or
                        on_chain['verified'] != actor_db_model.verified):
                        # Update actor (would need node operator credentials)
                        logger.info(f"Actor {actor_db_model.x_username} needs update on-chain")
                    return True
                else:
                    # Actor exists but is not active
                    logger.info(f"Actor {actor_db_model.x_username} exists but is not active")
                    return False
            else:
                # Propose new actor (would need node operator credentials)
                logger.info(f"Actor {actor_db_model.x_username} needs to be proposed on-chain")
                return False
                
        except Exception as e:
            logger.error(f"Error syncing actor: {e}")
            return False
            
    def get_actor_for_market(self, x_username: str) -> Optional[Dict]:
        """Get actor data for market creation validation"""
        try:
            if not self.is_actor_active(x_username):
                return None
            return self.get_actor(x_username)
        except Exception as e:
            logger.error(f"Error getting actor for market: {e}")
            return None
            
    def listen_for_actor_events(self, callback):
        """Listen for ActorProposed and ActorActivated events"""
        try:
            # Create event filters
            proposed_filter = self.contract.events.ActorProposed.create_filter(fromBlock='latest')
            activated_filter = self.contract.events.ActorActivated.create_filter(fromBlock='latest')
            
            # Poll for events
            while True:
                for event in proposed_filter.get_new_entries():
                    callback('proposed', event)
                for event in activated_filter.get_new_entries():
                    callback('activated', event)
                    
        except Exception as e:
            logger.error(f"Error listening for events: {e}")