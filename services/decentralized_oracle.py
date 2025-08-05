"""
Decentralized Oracle Service
Handles on-chain oracle operations with IPFS integration
"""

import logging
import json
import base64
from typing import Optional, Dict, List, Tuple
from web3 import Web3
from eth_account import Account

logger = logging.getLogger(__name__)

class DecentralizedOracleService:
    """Service for decentralized oracle operations"""
    
    def __init__(self, blockchain_service):
        self.blockchain = blockchain_service
        self.w3 = blockchain_service.w3
        
        # Load DecentralizedOracle contract
        self.contract_address = None
        self.contract = None
        self._load_contract()
        
        # Initialize IPFS client (mock for now)
        self.ipfs_client = None
        logger.info("IPFS client mock initialized (real IPFS integration pending)")
            
        # Gas estimates for operations
        self.gas_estimates = {
            'submit_oracle_data': 500000,  # Higher due to on-chain Levenshtein calculation
        }
        
    def _load_contract(self):
        """Load DecentralizedOracle contract ABI and address"""
        try:
            # Load from deployment file if available
            with open('deployments/base-sepolia.json', 'r') as f:
                deployments = json.load(f)
                
            if 'DecentralizedOracle' in deployments:
                self.contract_address = deployments['DecentralizedOracle']['address']
                
                # Load ABI from artifact
                with open('artifacts/contracts/src/DecentralizedOracle.sol/DecentralizedOracle.json', 'r') as f:
                    artifact = json.load(f)
                    abi = artifact['abi']
                    
                self.contract = self.w3.eth.contract(
                    address=Web3.to_checksum_address(self.contract_address),
                    abi=abi
                )
                logger.info(f"DecentralizedOracle contract loaded at {self.contract_address}")
        except FileNotFoundError:
            logger.warning("DecentralizedOracle deployment or ABI not found")
        except Exception as e:
            logger.error(f"Error loading DecentralizedOracle contract: {e}")
            
    def upload_screenshot_to_ipfs(self, screenshot_base64: str) -> Optional[str]:
        """Upload screenshot to IPFS and return hash"""
        if not self.ipfs_client:
            logger.warning("IPFS client not available, using mock hash")
            # For testing, return a mock IPFS hash
            return f"Qm{Web3.keccak(text=screenshot_base64).hex()[:44]}"
            
        try:
            # Decode base64 to bytes
            screenshot_bytes = base64.b64decode(screenshot_base64)
            
            # Upload to IPFS
            result = self.ipfs_client.add(screenshot_bytes)
            ipfs_hash = result['Hash']
            
            logger.info(f"Screenshot uploaded to IPFS: {ipfs_hash}")
            return ipfs_hash
            
        except Exception as e:
            logger.error(f"Error uploading to IPFS: {e}")
            return None
            
    def submit_oracle_data(
        self,
        node_wallet_address: str,
        node_private_key: str,
        market_id: str,
        submission_id: str,
        actual_text: str,
        screenshot_base64: str,
        predicted_text: str
    ) -> Optional[str]:
        """Submit oracle data on-chain with IPFS screenshot"""
        if not self.contract:
            logger.error("DecentralizedOracle contract not loaded")
            return None
            
        try:
            # Upload screenshot to IPFS
            ipfs_hash = self.upload_screenshot_to_ipfs(screenshot_base64)
            if not ipfs_hash:
                logger.error("Failed to upload screenshot to IPFS")
                return None
                
            # Convert IDs to bytes32
            market_id_bytes = Web3.to_bytes(hexstr=market_id)  # type: ignore
            submission_id_bytes = Web3.to_bytes(hexstr=submission_id)  # type: ignore
            
            # Build transaction
            account = Account.from_key(node_private_key)
            nonce = self.w3.eth.get_transaction_count(account.address)
            
            # Estimate gas
            gas_price = self.w3.eth.gas_price
            gas_limit = self.gas_estimates['submit_oracle_data']
            
            # Build transaction
            transaction = self.contract.functions.submitOracleData(
                market_id_bytes,
                submission_id_bytes,
                actual_text,
                ipfs_hash,
                predicted_text
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
                logger.info(f"Oracle data submitted successfully. Tx: {tx_hash.hex()}")
                
                # Parse events
                self._parse_oracle_events(receipt)
                
                return tx_hash.hex()
            else:
                logger.error("Transaction failed for submitting oracle data")
                return None
                
        except Exception as e:
            logger.error(f"Error submitting oracle data: {e}")
            return None
            
    def _parse_oracle_events(self, receipt):
        """Parse events from oracle submission transaction"""
        if not self.contract:
            return
            
        try:
            # Parse OracleDataSubmitted events
            oracle_submitted_events = self.contract.events.OracleDataSubmitted().process_receipt(receipt)
            for event in oracle_submitted_events:
                logger.info(f"Oracle data submitted: {event['args']}")
                
            # Parse ConsensusReached events
            consensus_events = self.contract.events.ConsensusReached().process_receipt(receipt)
            for event in consensus_events:
                logger.info(f"Consensus reached for submission: {event['args']}")
                
            # Parse MarketAutoResolved events
            resolved_events = self.contract.events.MarketAutoResolved().process_receipt(receipt)
            for event in resolved_events:
                logger.info(f"Market auto-resolved: {event['args']}")
                
        except Exception as e:
            logger.error(f"Error parsing oracle events: {e}")
            
    def get_oracle_data(self, market_id: str, submission_id: str) -> Optional[Dict]:
        """Get oracle data for a submission"""
        if not self.contract:
            return None
            
        try:
            market_id_bytes = Web3.to_bytes(hexstr=market_id)  # type: ignore
            submission_id_bytes = Web3.to_bytes(hexstr=submission_id)  # type: ignore
            
            result = self.contract.functions.getOracleData(
                market_id_bytes,
                submission_id_bytes
            ).call()
            
            return {
                'actual_text': result[0],
                'screenshot_ipfs': result[1],
                'levenshtein_distance': result[2],
                'validator_count': result[3],
                'consensus_reached': result[4]
            }
            
        except Exception as e:
            logger.error(f"Error getting oracle data: {e}")
            return None
            
    def has_oracle_validated(
        self,
        market_id: str,
        submission_id: str,
        oracle_address: str
    ) -> bool:
        """Check if an oracle has already validated a submission"""
        if not self.contract:
            return False
            
        try:
            market_id_bytes = Web3.to_bytes(hexstr=market_id)  # type: ignore
            submission_id_bytes = Web3.to_bytes(hexstr=submission_id)  # type: ignore
            oracle_address = Web3.to_checksum_address(oracle_address)
            
            return self.contract.functions.hasOracleValidated(
                market_id_bytes,
                submission_id_bytes,
                oracle_address
            ).call()
            
        except Exception as e:
            logger.error(f"Error checking oracle validation: {e}")
            return False
            
    def calculate_on_chain_levenshtein(self, text_a: str, text_b: str) -> Optional[int]:
        """Calculate Levenshtein distance on-chain (for testing)"""
        if not self.contract:
            return None
            
        try:
            distance = self.contract.functions.calculateLevenshteinDistance(
                text_a,
                text_b
            ).call()
            
            return distance
            
        except Exception as e:
            logger.error(f"Error calculating on-chain Levenshtein: {e}")
            return None
            
    def get_ipfs_content(self, ipfs_hash: str) -> Optional[bytes]:
        """Retrieve content from IPFS"""
        if not self.ipfs_client:
            logger.warning("IPFS client not available")
            return None
            
        try:
            content = self.ipfs_client.cat(ipfs_hash)
            return content
            
        except Exception as e:
            logger.error(f"Error retrieving from IPFS: {e}")
            return None
            
    def verify_screenshot_integrity(
        self,
        market_id: str,
        submission_id: str,
        expected_hash: str
    ) -> bool:
        """Verify screenshot integrity from IPFS"""
        try:
            # Get oracle data
            oracle_data = self.get_oracle_data(market_id, submission_id)
            if not oracle_data:
                return False
                
            # Compare IPFS hashes
            return oracle_data['screenshot_ipfs'] == expected_hash
            
        except Exception as e:
            logger.error(f"Error verifying screenshot integrity: {e}")
            return False