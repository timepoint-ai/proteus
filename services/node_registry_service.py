"""
Node Registry Service - Integrates with BASE blockchain NodeRegistry contract
Handles node staking, registration, and on-chain consensus
"""

import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from web3 import Web3
from eth_account import Account

from config import Config
from services.blockchain_base import BaseBlockchainService
from models import NodeOperator, db

logger = logging.getLogger(__name__)


class NodeRegistryService:
    """Service for interacting with NodeRegistry smart contract"""
    
    def __init__(self):
        self.blockchain_service = BaseBlockchainService()
        self.web3 = self.blockchain_service.web3
        self.node_registry_address = Config.NODE_REGISTRY_ADDRESS if hasattr(Config, 'NODE_REGISTRY_ADDRESS') else None
        self.contract = None
        
        if self.node_registry_address:
            self._load_contract()
            
    def _load_contract(self):
        """Load the NodeRegistry contract ABI and create contract instance"""
        try:
            # Simplified ABI for key functions
            self.contract_abi = [
                {
                    "name": "registerNode",
                    "type": "function",
                    "inputs": [{"name": "endpoint", "type": "string"}],
                    "outputs": [],
                    "stateMutability": "payable"
                },
                {
                    "name": "updateHeartbeat", 
                    "type": "function",
                    "inputs": [],
                    "outputs": [],
                    "stateMutability": "nonpayable"
                },
                {
                    "name": "voteOnNode",
                    "type": "function", 
                    "inputs": [
                        {"name": "voteId", "type": "uint256"},
                        {"name": "support", "type": "bool"}
                    ],
                    "outputs": [],
                    "stateMutability": "nonpayable"
                },
                {
                    "name": "withdrawStake",
                    "type": "function",
                    "inputs": [],
                    "outputs": [],
                    "stateMutability": "nonpayable"
                },
                {
                    "name": "getNodeDetails",
                    "type": "function",
                    "inputs": [{"name": "_operator", "type": "address"}],
                    "outputs": [
                        {"name": "stake", "type": "uint256"},
                        {"name": "reputation", "type": "uint256"},
                        {"name": "active", "type": "bool"},
                        {"name": "endpoint", "type": "string"},
                        {"name": "totalRewards", "type": "uint256"}
                    ],
                    "stateMutability": "view"
                },
                {
                    "name": "getActiveNodes",
                    "type": "function",
                    "inputs": [],
                    "outputs": [{"name": "", "type": "address[]"}],
                    "stateMutability": "view"
                },
                {
                    "name": "MINIMUM_STAKE",
                    "type": "function",
                    "inputs": [],
                    "outputs": [{"name": "", "type": "uint256"}],
                    "stateMutability": "view"
                },
                {
                    "name": "nodes",
                    "type": "function",
                    "inputs": [{"name": "", "type": "address"}],
                    "outputs": [
                        {"name": "operator", "type": "address"},
                        {"name": "stake", "type": "uint256"},
                        {"name": "reputation", "type": "uint256"},
                        {"name": "active", "type": "bool"},
                        {"name": "registrationTime", "type": "uint256"},
                        {"name": "lastActiveTime", "type": "uint256"},
                        {"name": "endpoint", "type": "string"},
                        {"name": "totalRewards", "type": "uint256"},
                        {"name": "slashCount", "type": "uint256"}
                    ],
                    "stateMutability": "view"
                },
                {
                    "name": "NodeRegistered",
                    "type": "event",
                    "inputs": [
                        {"name": "operator", "type": "address", "indexed": True},
                        {"name": "stake", "type": "uint256", "indexed": False}
                    ]
                },
                {
                    "name": "NodeDeactivated",
                    "type": "event",
                    "inputs": [
                        {"name": "operator", "type": "address", "indexed": True}
                    ]
                }
            ]
            
            self.contract = self.web3.eth.contract(
                address=Web3.to_checksum_address(self.node_registry_address),
                abi=self.contract_abi
            )
            logger.info(f"NodeRegistry contract loaded at {self.node_registry_address}")
            
        except Exception as e:
            logger.error(f"Error loading NodeRegistry contract: {e}")
            
    async def register_node(self, endpoint: str, private_key: str) -> Optional[str]:
        """Register a new node with stake"""
        try:
            if not self.contract:
                logger.error("NodeRegistry contract not loaded")
                return None
                
            # Get minimum stake requirement
            min_stake = self.contract.functions.MINIMUM_STAKE().call()
            logger.info(f"Minimum stake required: {Web3.from_wei(min_stake, 'ether')} BASE")
            
            # Build transaction
            account = Account.from_key(private_key)
            nonce = self.web3.eth.get_transaction_count(account.address)
            
            # Estimate gas
            try:
                gas_estimate = self.contract.functions.registerNode(endpoint).estimate_gas({
                    'from': account.address,
                    'value': min_stake
                })
            except Exception as e:
                logger.error(f"Gas estimation failed: {e}")
                gas_estimate = 300000
                
            # Get current gas price
            gas_price = self.web3.eth.gas_price
            
            # Build transaction
            transaction = self.contract.functions.registerNode(endpoint).build_transaction({
                'from': account.address,
                'value': min_stake,
                'gas': gas_estimate,
                'gasPrice': gas_price,
                'nonce': nonce,
                'chainId': self.blockchain_service.chain_id
            })
            
            # Sign and send transaction
            signed_txn = self.web3.eth.account.sign_transaction(transaction, private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            logger.info(f"Node registration transaction sent: {tx_hash.hex()}")
            
            # Wait for confirmation
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt['status'] == 1:
                logger.info(f"Node registered successfully. Gas used: {receipt['gasUsed']}")
                
                # Update database
                await self._update_node_in_db(account.address, endpoint, 'pending')
                
                return tx_hash.hex()
            else:
                logger.error("Node registration transaction failed")
                return None
                
        except Exception as e:
            logger.error(f"Error registering node: {e}")
            return None
            
    async def update_heartbeat(self, private_key: str) -> bool:
        """Update node heartbeat to maintain active status"""
        try:
            if not self.contract:
                return False
                
            account = Account.from_key(private_key)
            
            # Check if node is registered
            node_details = self.get_node_details(account.address)
            if not node_details or not node_details[2]:  # active flag
                logger.warning(f"Node {account.address} is not active")
                return False
                
            # Build and send heartbeat transaction
            nonce = self.web3.eth.get_transaction_count(account.address)
            
            transaction = self.contract.functions.updateHeartbeat().build_transaction({
                'from': account.address,
                'gas': 100000,
                'gasPrice': self.web3.eth.gas_price,
                'nonce': nonce,
                'chainId': self.blockchain_service.chain_id
            })
            
            signed_txn = self.web3.eth.account.sign_transaction(transaction, private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt['status'] == 1:
                logger.info(f"Node heartbeat updated for {account.address}")
                return True
            else:
                logger.error("Heartbeat update failed")
                return False
                
        except Exception as e:
            logger.error(f"Error updating heartbeat: {e}")
            return False
            
    async def vote_on_node(self, vote_id: int, support: bool, private_key: str) -> bool:
        """Vote on a node activation/deactivation proposal"""
        try:
            if not self.contract:
                return False
                
            account = Account.from_key(private_key)
            nonce = self.web3.eth.get_transaction_count(account.address)
            
            transaction = self.contract.functions.voteOnNode(vote_id, support).build_transaction({
                'from': account.address,
                'gas': 150000,
                'gasPrice': self.web3.eth.gas_price,
                'nonce': nonce,
                'chainId': self.blockchain_service.chain_id
            })
            
            signed_txn = self.web3.eth.account.sign_transaction(transaction, private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt['status'] == 1:
                logger.info(f"Vote cast successfully. Vote ID: {vote_id}, Support: {support}")
                return True
            else:
                logger.error("Vote transaction failed")
                return False
                
        except Exception as e:
            logger.error(f"Error voting on node: {e}")
            return False
            
    def get_node_details(self, node_address: str) -> Optional[Tuple]:
        """Get on-chain node details"""
        try:
            if not self.contract:
                return None
                
            details = self.contract.functions.getNodeDetails(
                Web3.to_checksum_address(node_address)
            ).call()
            
            return details
            
        except Exception as e:
            logger.error(f"Error getting node details: {e}")
            return None
            
    def get_active_nodes(self) -> List[str]:
        """Get list of active node addresses from blockchain"""
        try:
            if not self.contract:
                return []
                
            active_nodes = self.contract.functions.getActiveNodes().call()
            return active_nodes
            
        except Exception as e:
            logger.error(f"Error getting active nodes: {e}")
            return []
            
    async def sync_nodes_with_blockchain(self):
        """Sync local database with on-chain node registry"""
        try:
            active_nodes = self.get_active_nodes()
            
            from app import app
            with app.app_context():
                # Update or create node entries
                for node_address in active_nodes:
                    details = self.get_node_details(node_address)
                    if details:
                        stake, reputation, active, endpoint, total_rewards = details
                        
                        # Find or create node in database
                        node = NodeOperator.query.filter_by(
                            node_address=node_address.lower()
                        ).first()
                        
                        if not node:
                            node = NodeOperator(
                                operator_id=f"node-{node_address[:8]}",
                                node_address=node_address.lower(),
                                public_key="",  # Would be exchanged separately
                                status='active' if active else 'inactive'
                            )
                            db.session.add(node)
                        else:
                            node.status = 'active' if active else 'inactive'
                            node.last_seen = datetime.utcnow()
                            
                # Mark nodes not in active list as inactive
                all_nodes = NodeOperator.query.filter_by(status='active').all()
                for node in all_nodes:
                    if node.node_address not in [n.lower() for n in active_nodes]:
                        node.status = 'inactive'
                        
                db.session.commit()
                logger.info(f"Synced {len(active_nodes)} active nodes from blockchain")
                
        except Exception as e:
            logger.error(f"Error syncing nodes with blockchain: {e}")
            
    async def _update_node_in_db(self, node_address: str, endpoint: str, status: str):
        """Update node information in database"""
        try:
            from app import app
            with app.app_context():
                node = NodeOperator.query.filter_by(
                    node_address=node_address.lower()
                ).first()
                
                if not node:
                    node = NodeOperator(
                        operator_id=f"node-{node_address[:8]}",
                        node_address=node_address.lower(),
                        public_key="",
                        status=status
                    )
                    db.session.add(node)
                else:
                    node.status = status
                    node.last_seen = datetime.utcnow()
                    
                db.session.commit()
                
        except Exception as e:
            logger.error(f"Error updating node in database: {e}")
            
    def monitor_node_events(self):
        """Monitor blockchain for node registry events"""
        try:
            if not self.contract:
                return
                
            # Create event filters
            node_registered_filter = self.contract.events.NodeRegistered.create_filter(
                fromBlock='latest'
            )
            
            node_deactivated_filter = self.contract.events.NodeDeactivated.create_filter(
                fromBlock='latest'
            )
            
            # Check for new events periodically
            # This would typically run in a background task
            
        except Exception as e:
            logger.error(f"Error monitoring node events: {e}")