"""
Mock Node Registry for testing without deployed contracts
Implements Coinbase Base-compatible testing mechanism
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from web3 import Web3
from decimal import Decimal

logger = logging.getLogger(__name__)


class MockNodeRegistry:
    """Mock NodeRegistry contract for testing"""
    
    def __init__(self):
        self.nodes = {}
        self.votes = {}
        self.minimum_stake = Web3.to_wei(100, 'ether')  # 100 BASE
        self.vote_counter = 0
        
    def registerNode(self, endpoint: str, **kwargs) -> Dict:
        """Mock node registration"""
        sender = kwargs.get('from', '0x' + '0' * 40)
        value = kwargs.get('value', self.minimum_stake)
        
        if value < self.minimum_stake:
            raise ValueError("Insufficient stake")
            
        self.nodes[sender] = {
            'operator': sender,
            'stake': value,
            'reputation': 100,
            'active': False,  # Requires vote
            'registrationTime': datetime.utcnow().timestamp(),
            'lastActiveTime': datetime.utcnow().timestamp(),
            'endpoint': endpoint,
            'totalRewards': 0,
            'slashCount': 0
        }
        
        # Create activation vote
        self.vote_counter += 1
        self.votes[self.vote_counter] = {
            'subject': sender,
            'votesFor': 0,
            'votesAgainst': 0,
            'deadline': datetime.utcnow().timestamp() + 86400,
            'executed': False
        }
        
        return {'status': 1, 'gasUsed': 150000}
        
    def getNodeDetails(self, operator: str) -> Tuple:
        """Get node details"""
        if operator in self.nodes:
            node = self.nodes[operator]
            return (
                node['stake'],
                node['reputation'],
                node['active'],
                node['endpoint'],
                node['totalRewards']
            )
        return (0, 0, False, '', 0)
        
    def getActiveNodes(self) -> List[str]:
        """Get list of active nodes"""
        return [addr for addr, node in self.nodes.items() if node['active']]
        
    def updateHeartbeat(self, **kwargs) -> Dict:
        """Update node heartbeat"""
        sender = kwargs.get('from', '0x' + '0' * 40)
        if sender in self.nodes and self.nodes[sender]['active']:
            self.nodes[sender]['lastActiveTime'] = datetime.utcnow().timestamp()
            return {'status': 1, 'gasUsed': 50000}
        raise ValueError("Not an active node")
        
    def voteOnNode(self, vote_id: int, support: bool, **kwargs) -> Dict:
        """Vote on node activation"""
        if vote_id in self.votes and not self.votes[vote_id]['executed']:
            if support:
                self.votes[vote_id]['votesFor'] += 1
            else:
                self.votes[vote_id]['votesAgainst'] += 1
                
            # Auto-execute if threshold reached (simplified)
            total_votes = self.votes[vote_id]['votesFor'] + self.votes[vote_id]['votesAgainst']
            if total_votes >= 2:  # Simple threshold for testing
                self.votes[vote_id]['executed'] = True
                subject = self.votes[vote_id]['subject']
                if self.votes[vote_id]['votesFor'] > self.votes[vote_id]['votesAgainst']:
                    self.nodes[subject]['active'] = True
                    
            return {'status': 1, 'gasUsed': 100000}
        raise ValueError("Invalid vote")
        
    def MINIMUM_STAKE(self) -> int:
        """Get minimum stake requirement"""
        return self.minimum_stake


class MockNodeRegistryService:
    """Service wrapper for mock NodeRegistry"""
    
    def __init__(self):
        self.contract = MockNodeRegistry()
        self.web3 = MockWeb3()
        self.node_registry_address = '0x' + '1234567890' * 4  # Mock address
        
    async def register_node(self, endpoint: str, private_key: str) -> Optional[str]:
        """Register a new node with stake"""
        try:
            # Mock account from private key
            account_address = '0x' + private_key[:40].ljust(40, '0')
            
            # Mock registration
            result = self.contract.registerNode(
                endpoint,
                **{'from': account_address, 'value': self.contract.minimum_stake}
            )
            
            if result['status'] == 1:
                logger.info(f"Mock node registered: {account_address}")
                return '0x' + 'a' * 64  # Mock tx hash
                
        except Exception as e:
            logger.error(f"Mock registration failed: {e}")
            return None
            
    def get_node_details(self, node_address: str) -> Optional[Tuple]:
        """Get on-chain node details"""
        return self.contract.getNodeDetails(node_address)
        
    def get_active_nodes(self) -> List[str]:
        """Get list of active node addresses"""
        return self.contract.getActiveNodes()
        
    async def update_heartbeat(self, private_key: str) -> bool:
        """Update node heartbeat"""
        try:
            account_address = '0x' + private_key[:40].ljust(40, '0')
            result = self.contract.updateHeartbeat(**{'from': account_address})
            return result['status'] == 1
        except Exception as e:
            logger.error(f"Mock heartbeat failed: {e}")
            return False
            
    async def vote_on_node(self, vote_id: int, support: bool, private_key: str) -> bool:
        """Vote on node activation"""
        try:
            account_address = '0x' + private_key[:40].ljust(40, '0')
            result = self.contract.voteOnNode(
                vote_id, 
                support,
                **{'from': account_address}
            )
            return result['status'] == 1
        except Exception as e:
            logger.error(f"Mock vote failed: {e}")
            return False


class MockWeb3:
    """Mock Web3 instance for testing"""
    
    def __init__(self):
        self.eth = MockEth()
        
    @staticmethod
    def to_checksum_address(address: str) -> str:
        """Mock checksum address"""
        return address
        
    @staticmethod
    def from_wei(value: int, unit: str) -> Decimal:
        """Convert from wei"""
        if unit == 'ether':
            return Decimal(value) / Decimal(10**18)
        return Decimal(value)
        
    @staticmethod
    def to_wei(value: int, unit: str) -> int:
        """Convert to wei"""
        if unit == 'ether':
            return value * 10**18
        return value


class MockEth:
    """Mock eth module"""
    
    def __init__(self):
        self.chain_id = 84532  # BASE Sepolia
        self.gas_price = 1000000000  # 1 gwei
        
    def get_transaction_count(self, address: str) -> int:
        """Mock nonce"""
        return 0
        
    def wait_for_transaction_receipt(self, tx_hash: str) -> Dict:
        """Mock transaction receipt"""
        return {
            'status': 1,
            'gasUsed': 100000,
            'blockNumber': 12345
        }