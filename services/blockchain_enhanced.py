"""
Enhanced Blockchain Service for Phase 10
Manages interaction with fully on-chain EnhancedPredictionMarket
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
from services.actor_registry import ActorRegistryService

logger = logging.getLogger(__name__)


class EnhancedBlockchainService:
    """Service for interacting with fully on-chain prediction markets"""
    
    def __init__(self):
        self.blockchain = BaseBlockchainService()
        self.w3 = self.blockchain.w3
        self.actor_registry = ActorRegistryService()
        
        # Load contract address and ABI
        self.contract_address = os.getenv('ENHANCED_PREDICTION_MARKET_ADDRESS')
        if not self.contract_address:
            # Fall back to original if enhanced not deployed yet
            self.contract_address = os.getenv('PREDICTION_MARKET_ADDRESS')
            logger.warning("Using original prediction market address as fallback")
            
        # Load ABI from compiled contract
        abi_path = './contracts/artifacts/contracts/src/EnhancedPredictionMarket.sol/EnhancedPredictionMarket.json'
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
        
        # Gas estimates for operations
        self.gas_estimates = {
            'create_market': 500000,
            'create_submission': 300000,
            'place_bet': 200000,
            'claim_winnings': 150000,
            'resolve_market': 400000
        }
        
    def _get_minimal_abi(self) -> list:
        """Return minimal ABI for EnhancedPredictionMarket contract"""
        return [
            # View functions
            {
                "inputs": [{"name": "_marketId", "type": "uint256"}],
                "name": "markets",
                "outputs": [
                    {"name": "question", "type": "string"},
                    {"name": "actorUsername", "type": "string"},
                    {"name": "creator", "type": "address"},
                    {"name": "startTime", "type": "uint256"},
                    {"name": "endTime", "type": "uint256"},
                    {"name": "resolved", "type": "bool"},
                    {"name": "winningSubmissionId", "type": "uint256"},
                    {"name": "totalVolume", "type": "uint256"},
                    {"name": "platformFeeCollected", "type": "uint256"},
                    {"name": "submissionCount", "type": "uint256"},
                    {"name": "betCount", "type": "uint256"}
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "marketCount",
                "outputs": [{"name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            },
            # State-changing functions
            {
                "inputs": [
                    {"name": "_question", "type": "string"},
                    {"name": "_actorUsername", "type": "string"},
                    {"name": "_duration", "type": "uint256"},
                    {"name": "_oracleWallets", "type": "address[]"},
                    {"name": "_metadata", "type": "string"}
                ],
                "name": "createMarket",
                "outputs": [{"name": "", "type": "uint256"}],
                "stateMutability": "payable",
                "type": "function"
            },
            {
                "inputs": [
                    {"name": "_marketId", "type": "uint256"},
                    {"name": "_predictedText", "type": "string"},
                    {"name": "_submissionType", "type": "string"}
                ],
                "name": "createSubmission",
                "outputs": [{"name": "", "type": "uint256"}],
                "stateMutability": "payable",
                "type": "function"
            },
            {
                "inputs": [
                    {"name": "_submissionId", "type": "uint256"},
                    {"name": "_transactionHash", "type": "bytes32"}
                ],
                "name": "placeBet",
                "outputs": [{"name": "", "type": "uint256"}],
                "stateMutability": "payable",
                "type": "function"
            },
            # Events
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": True, "name": "marketId", "type": "uint256"},
                    {"indexed": True, "name": "creator", "type": "address"},
                    {"indexed": False, "name": "actorUsername", "type": "string"},
                    {"indexed": False, "name": "question", "type": "string"},
                    {"indexed": False, "name": "endTime", "type": "uint256"}
                ],
                "name": "MarketCreated",
                "type": "event"
            }
        ]
        
    def create_market(
        self,
        creator_address: str,
        private_key: str,
        question: str,
        actor_username: str,
        duration: int,
        oracle_wallets: List[str],
        metadata: Dict = None
    ) -> Optional[Dict]:
        """Create a fully on-chain prediction market"""
        try:
            # Verify actor exists and is active on-chain
            if not self.actor_registry.is_actor_active(actor_username):
                logger.error(f"Actor {actor_username} is not active on-chain")
                return None
                
            # Prepare metadata as JSON string
            metadata_str = json.dumps(metadata) if metadata else "{}"
            
            # Build transaction
            account = Account.from_key(private_key)
            nonce = self.w3.eth.get_transaction_count(account.address)
            
            # Estimate gas
            gas_price = self.w3.eth.gas_price
            gas_limit = self.gas_estimates['create_market']
            
            # Ensure oracle wallets are checksummed
            oracle_wallets_checksummed = [Web3.to_checksum_address(w) for w in oracle_wallets]
            
            # Build transaction
            transaction = self.contract.functions.createMarket(
                question,
                actor_username,
                duration,
                oracle_wallets_checksummed,
                metadata_str
            ).build_transaction({
                'from': account.address,
                'nonce': nonce,
                'gas': gas_limit,
                'gasPrice': gas_price,
                'chainId': self.blockchain.chain_id,
                'value': 0  # No value needed for market creation
            })
            
            # Sign and send transaction
            signed_txn = self.w3.eth.account.sign_transaction(transaction, private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt.status == 1:
                # Get market ID from events
                market_created_event = None
                for log in receipt.logs:
                    try:
                        parsed = self.contract.events.MarketCreated().process_log(log)
                        market_created_event = parsed
                        break
                    except:
                        continue
                        
                if market_created_event:
                    market_id = market_created_event['args']['marketId']
                    logger.info(f"Market created successfully. ID: {market_id}, Tx: {tx_hash.hex()}")
                    
                    return {
                        'market_id': market_id,
                        'tx_hash': tx_hash.hex(),
                        'contract_address': self.contract_address,
                        'gas_used': receipt.gasUsed,
                        'actor_username': actor_username,
                        'question': question,
                        'oracle_wallets': oracle_wallets
                    }
                else:
                    # Calculate market ID manually (marketCount - 1)
                    market_count = self.contract.functions.marketCount().call()
                    market_id = market_count - 1
                    logger.info(f"Market created (calculated ID: {market_id}), Tx: {tx_hash.hex()}")
                    
                    return {
                        'market_id': market_id,
                        'tx_hash': tx_hash.hex(),
                        'contract_address': self.contract_address,
                        'gas_used': receipt.gasUsed
                    }
            else:
                logger.error("Transaction failed for market creation")
                return None
                
        except Exception as e:
            logger.error(f"Error creating market: {e}")
            return None
            
    def create_submission(
        self,
        submitter_address: str,
        private_key: str,
        market_id: int,
        predicted_text: str,
        submission_type: str,
        stake_amount_eth: float
    ) -> Optional[Dict]:
        """Create a submission on a fully on-chain market"""
        try:
            # Validate submission type
            valid_types = ['original', 'competitor', 'null']
            if submission_type not in valid_types:
                logger.error(f"Invalid submission type: {submission_type}")
                return None
                
            # Build transaction
            account = Account.from_key(private_key)
            nonce = self.w3.eth.get_transaction_count(account.address)
            
            # Convert stake to wei
            stake_wei = Web3.to_wei(stake_amount_eth, 'ether')
            
            # Estimate gas
            gas_price = self.w3.eth.gas_price
            gas_limit = self.gas_estimates['create_submission']
            
            # Build transaction
            transaction = self.contract.functions.createSubmission(
                market_id,
                predicted_text,
                submission_type
            ).build_transaction({
                'from': account.address,
                'nonce': nonce,
                'gas': gas_limit,
                'gasPrice': gas_price,
                'chainId': self.blockchain.chain_id,
                'value': stake_wei
            })
            
            # Sign and send transaction
            signed_txn = self.w3.eth.account.sign_transaction(transaction, private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt.status == 1:
                # Get submission ID from events
                submission_created_event = None
                for log in receipt.logs:
                    try:
                        parsed = self.contract.events.SubmissionCreated().process_log(log)
                        submission_created_event = parsed
                        break
                    except:
                        continue
                        
                if submission_created_event:
                    submission_id = submission_created_event['args']['submissionId']
                else:
                    # Calculate submission ID manually
                    submission_count = self.contract.functions.totalSubmissionCount().call()
                    submission_id = submission_count - 1
                    
                logger.info(f"Submission created. ID: {submission_id}, Tx: {tx_hash.hex()}")
                
                return {
                    'submission_id': submission_id,
                    'market_id': market_id,
                    'tx_hash': tx_hash.hex(),
                    'gas_used': receipt.gasUsed,
                    'stake_amount': stake_amount_eth,
                    'submission_type': submission_type
                }
            else:
                logger.error("Transaction failed for submission creation")
                return None
                
        except Exception as e:
            logger.error(f"Error creating submission: {e}")
            return None
            
    def place_bet(
        self,
        bettor_address: str,
        private_key: str,
        submission_id: int,
        bet_amount_eth: float,
        transaction_hash: str = None
    ) -> Optional[Dict]:
        """Place a bet on a submission"""
        try:
            # Build transaction
            account = Account.from_key(private_key)
            nonce = self.w3.eth.get_transaction_count(account.address)
            
            # Convert bet to wei
            bet_wei = Web3.to_wei(bet_amount_eth, 'ether')
            
            # Generate unique transaction hash if not provided
            if not transaction_hash:
                transaction_hash = Web3.keccak(
                    text=f"{bettor_address}{submission_id}{bet_amount_eth}{datetime.now().isoformat()}"
                )
            else:
                transaction_hash = bytes.fromhex(transaction_hash.replace('0x', ''))
                
            # Estimate gas
            gas_price = self.w3.eth.gas_price
            gas_limit = self.gas_estimates['place_bet']
            
            # Build transaction
            transaction = self.contract.functions.placeBet(
                submission_id,
                transaction_hash
            ).build_transaction({
                'from': account.address,
                'nonce': nonce,
                'gas': gas_limit,
                'gasPrice': gas_price,
                'chainId': self.blockchain.chain_id,
                'value': bet_wei
            })
            
            # Sign and send transaction
            signed_txn = self.w3.eth.account.sign_transaction(transaction, private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt.status == 1:
                # Get bet ID from events
                bet_placed_event = None
                for log in receipt.logs:
                    try:
                        parsed = self.contract.events.BetPlaced().process_log(log)
                        bet_placed_event = parsed
                        break
                    except:
                        continue
                        
                if bet_placed_event:
                    bet_id = bet_placed_event['args']['betId']
                else:
                    # Calculate bet ID manually
                    bet_count = self.contract.functions.totalBetCount().call()
                    bet_id = bet_count - 1
                    
                logger.info(f"Bet placed. ID: {bet_id}, Tx: {tx_hash.hex()}")
                
                return {
                    'bet_id': bet_id,
                    'submission_id': submission_id,
                    'tx_hash': tx_hash.hex(),
                    'gas_used': receipt.gasUsed,
                    'bet_amount': bet_amount_eth
                }
            else:
                logger.error("Transaction failed for bet placement")
                return None
                
        except Exception as e:
            logger.error(f"Error placing bet: {e}")
            return None
            
    def get_market_details(self, market_id: int) -> Optional[Dict]:
        """Get complete market details from blockchain"""
        try:
            # Get market data
            market_data = self.contract.functions.markets(market_id).call()
            
            # Get additional details
            market_submissions = self.contract.functions.marketSubmissions(market_id).call()
            market_stats = self.contract.functions.marketStats(market_id).call()
            
            # Get actor details from registry
            actor_username = market_data[1]
            actor_details = self.actor_registry.get_actor(actor_username)
            
            return {
                'market_id': market_id,
                'question': market_data[0],
                'actor_username': actor_username,
                'actor_details': actor_details,
                'creator': market_data[2],
                'start_time': datetime.fromtimestamp(market_data[3]),
                'end_time': datetime.fromtimestamp(market_data[4]),
                'resolved': market_data[5],
                'winning_submission_id': market_data[6] if market_data[5] else None,
                'total_volume': Web3.from_wei(market_data[7], 'ether'),
                'platform_fee_collected': Web3.from_wei(market_data[8], 'ether'),
                'submission_count': market_data[9],
                'bet_count': market_data[10],
                'submission_ids': market_submissions,
                'stats': {
                    'total_submissions': market_stats[0],
                    'total_bets': market_stats[1],
                    'total_volume': Web3.from_wei(market_stats[2], 'ether'),
                    'highest_stake': Web3.from_wei(market_stats[3], 'ether'),
                    'top_bettor': market_stats[4],
                    'top_bettor_volume': Web3.from_wei(market_stats[5], 'ether'),
                    'average_bet_size': Web3.from_wei(market_stats[6], 'ether') if market_stats[1] > 0 else 0,
                    'last_activity_time': datetime.fromtimestamp(market_stats[7])
                }
            }
        except Exception as e:
            logger.error(f"Error getting market details: {e}")
            return None
            
    def get_submission_details(self, submission_id: int) -> Optional[Dict]:
        """Get complete submission details from blockchain"""
        try:
            # Get submission data
            submission_data = self.contract.functions.submissions(submission_id).call()
            
            # Get bet IDs for this submission
            bet_ids = self.contract.functions.submissionBets(submission_id).call()
            
            return {
                'submission_id': submission_id,
                'market_id': submission_data[0],
                'creator': submission_data[1],
                'predicted_text': submission_data[2],
                'stake': Web3.from_wei(submission_data[3], 'ether'),
                'total_bets': Web3.from_wei(submission_data[4], 'ether'),
                'bet_count': submission_data[5],
                'levenshtein_distance': submission_data[6],
                'is_winner': submission_data[7],
                'created_at': datetime.fromtimestamp(submission_data[8]),
                'submission_type': submission_data[9],
                'text_hash': submission_data[10].hex() if submission_data[10] else None,
                'bet_ids': bet_ids
            }
        except Exception as e:
            logger.error(f"Error getting submission details: {e}")
            return None
            
    def get_user_activity(self, user_address: str) -> Optional[Dict]:
        """Get all user activity from blockchain"""
        try:
            # Get user data
            user_data = self.contract.functions.getUserActivity(
                Web3.to_checksum_address(user_address)
            ).call()
            
            return {
                'market_ids': user_data[0],
                'submission_ids': user_data[1],
                'bet_ids': user_data[2],
                'total_volume': Web3.from_wei(user_data[3], 'ether'),
                'total_winnings': Web3.from_wei(user_data[4], 'ether')
            }
        except Exception as e:
            logger.error(f"Error getting user activity: {e}")
            return None
            
    def resolve_market(
        self,
        oracle_address: str,
        private_key: str,
        market_id: int,
        winning_submission_id: int,
        levenshtein_distances: List[int]
    ) -> Optional[str]:
        """Resolve a market (oracle only)"""
        try:
            # Build transaction
            account = Account.from_key(private_key)
            nonce = self.w3.eth.get_transaction_count(account.address)
            
            # Estimate gas
            gas_price = self.w3.eth.gas_price
            gas_limit = self.gas_estimates['resolve_market']
            
            # Build transaction
            transaction = self.contract.functions.resolveMarket(
                market_id,
                winning_submission_id,
                levenshtein_distances
            ).build_transaction({
                'from': account.address,
                'nonce': nonce,
                'gas': gas_limit,
                'gasPrice': gas_price,
                'chainId': self.blockchain.chain_id
            })
            
            # Sign and send transaction
            signed_txn = self.w3.eth.account.sign_transaction(transaction, private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt.status == 1:
                logger.info(f"Market {market_id} resolved. Winner: {winning_submission_id}, Tx: {tx_hash.hex()}")
                return tx_hash.hex()
            else:
                logger.error("Transaction failed for market resolution")
                return None
                
        except Exception as e:
            logger.error(f"Error resolving market: {e}")
            return None
            
    def claim_winnings(
        self,
        user_address: str,
        private_key: str,
        bet_id: int
    ) -> Optional[Dict]:
        """Claim winnings for a winning bet"""
        try:
            # Build transaction
            account = Account.from_key(private_key)
            nonce = self.w3.eth.get_transaction_count(account.address)
            
            # Estimate gas
            gas_price = self.w3.eth.gas_price
            gas_limit = self.gas_estimates['claim_winnings']
            
            # Build transaction
            transaction = self.contract.functions.claimWinnings(
                bet_id
            ).build_transaction({
                'from': account.address,
                'nonce': nonce,
                'gas': gas_limit,
                'gasPrice': gas_price,
                'chainId': self.blockchain.chain_id
            })
            
            # Sign and send transaction
            signed_txn = self.w3.eth.account.sign_transaction(transaction, private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt.status == 1:
                # Get payout amount from events
                payout_event = None
                for log in receipt.logs:
                    try:
                        parsed = self.contract.events.PayoutDistributed().process_log(log)
                        payout_event = parsed
                        break
                    except:
                        continue
                        
                payout_amount = 0
                if payout_event:
                    payout_amount = Web3.from_wei(payout_event['args']['amount'], 'ether')
                    
                logger.info(f"Winnings claimed. Bet ID: {bet_id}, Amount: {payout_amount} ETH, Tx: {tx_hash.hex()}")
                
                return {
                    'bet_id': bet_id,
                    'tx_hash': tx_hash.hex(),
                    'payout_amount': payout_amount,
                    'gas_used': receipt.gasUsed
                }
            else:
                logger.error("Transaction failed for claiming winnings")
                return None
                
        except Exception as e:
            logger.error(f"Error claiming winnings: {e}")
            return None