"""
V2 Resolution Service for PredictionMarketV2
Bridges X.com API with the V2 smart contract's resolveMarket() function
"""

import os
import logging
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from decimal import Decimal
from web3 import Web3
from eth_account import Account

from services.blockchain_base import BaseBlockchainService
from services.xcom_api_service import XComAPIService

logger = logging.getLogger(__name__)


class V2ResolutionService:
    """Service to resolve PredictionMarketV2 markets using X.com data"""

    def __init__(self):
        self.blockchain = BaseBlockchainService()
        self.xcom = XComAPIService()

        # Owner wallet for signing transactions (contract owner only can resolve)
        self.owner_private_key = os.environ.get('OWNER_PRIVATE_KEY')
        self.owner_address = os.environ.get('OWNER_ADDRESS', '0x21a85AD98641827BFd89F4d5bC2fEB72F98aaecA')

        # Verify owner account if private key provided
        if self.owner_private_key:
            try:
                account = Account.from_key(self.owner_private_key)
                if account.address.lower() != self.owner_address.lower():
                    logger.warning(f"Owner address mismatch: expected {self.owner_address}, got {account.address}")
                else:
                    logger.info(f"V2 Resolution Service initialized with owner: {self.owner_address}")
            except Exception as e:
                logger.error(f"Error validating owner key: {e}")
                self.owner_private_key = None
        else:
            logger.warning("OWNER_PRIVATE_KEY not set - resolution will require manual signing")

    def get_pending_markets(self) -> List[Dict[str, Any]]:
        """Get markets that are past end time but not yet resolved"""
        try:
            pending = []
            market_count = self.blockchain.get_v2_market_count()
            current_time = int(datetime.now().timestamp())

            for market_id in range(market_count):
                market = self.blockchain.get_v2_market(market_id)
                if market:
                    # Market is pending if: not resolved AND end time has passed
                    if not market['resolved'] and market['end_time'] < current_time:
                        # Get submission count
                        submissions = self.blockchain.get_v2_market_submissions(market_id)
                        market['submission_count'] = len(submissions)
                        market['can_resolve'] = len(submissions) >= 2  # Need 2+ submissions
                        # Format end_time for display
                        market['end_time_formatted'] = datetime.fromtimestamp(market['end_time']).strftime('%Y-%m-%d %H:%M')
                        pending.append(market)

            return pending
        except Exception as e:
            logger.error(f"Error getting pending markets: {e}")
            return []

    def get_market_for_resolution(self, market_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed market info needed for resolution"""
        try:
            market = self.blockchain.get_v2_market(market_id)
            if not market:
                return None

            # Get all submissions with their predicted texts
            submission_ids = self.blockchain.get_v2_market_submissions(market_id)
            submissions = []
            for sub_id in submission_ids:
                sub = self.blockchain.get_v2_submission(sub_id)
                if sub:
                    submissions.append(sub)

            market['submissions'] = submissions
            market['submission_count'] = len(submissions)

            # Check resolution eligibility
            current_time = int(datetime.now().timestamp())
            market['can_resolve'] = (
                not market['resolved'] and
                market['end_time'] < current_time and
                len(submissions) >= 2
            )

            return market
        except Exception as e:
            logger.error(f"Error getting market {market_id} for resolution: {e}")
            return None

    async def fetch_actual_tweet(self, actor_handle: str, tweet_url: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Fetch actual tweet for resolution

        Args:
            actor_handle: The X.com handle to fetch tweet from
            tweet_url: Optional specific tweet URL to verify

        Returns:
            Dict with tweet data including 'text' field, or None if not found
        """
        try:
            if tweet_url:
                # Fetch specific tweet by URL
                tweet_id = self.xcom.extract_tweet_id_from_url(tweet_url)
                if tweet_id:
                    tweet_data = await self.xcom.fetch_tweet_by_id(tweet_id)
                    if tweet_data:
                        # Verify it's from the expected user
                        if tweet_data.get('author_username', '').lower() == actor_handle.lower():
                            return tweet_data
                        else:
                            logger.warning(f"Tweet author mismatch: expected {actor_handle}, got {tweet_data.get('author_username')}")
                            return None

            # Otherwise fetch most recent tweet from user
            # This would typically be used for automated resolution
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(hours=24)  # Look back 24 hours

            tweets = await self.xcom.fetch_tweets_by_username(
                username=actor_handle,
                start_time=start_time,
                end_time=end_time,
                max_results=10
            )

            if tweets:
                # Return most recent tweet
                return tweets[0]

            return None

        except Exception as e:
            logger.error(f"Error fetching tweet for {actor_handle}: {e}")
            return None

    def resolve_market(self, market_id: int, actual_text: str) -> Dict[str, Any]:
        """Resolve a market with the actual tweet text

        Args:
            market_id: The market ID to resolve
            actual_text: The actual tweet text to compare against predictions

        Returns:
            Dict with 'success', 'tx_hash', 'error' fields
        """
        result = {
            'success': False,
            'tx_hash': None,
            'error': None,
            'market_id': market_id
        }

        try:
            # Validate market exists and can be resolved
            market = self.blockchain.get_v2_market(market_id)
            if not market:
                result['error'] = f"Market {market_id} not found"
                return result

            if market['resolved']:
                result['error'] = f"Market {market_id} is already resolved"
                return result

            current_time = int(datetime.now().timestamp())
            if market['end_time'] >= current_time:
                result['error'] = f"Market {market_id} has not ended yet"
                return result

            # Check minimum submissions
            submission_ids = self.blockchain.get_v2_market_submissions(market_id)
            if len(submission_ids) < 2:
                result['error'] = f"Market {market_id} needs at least 2 submissions (has {len(submission_ids)})"
                return result

            # Validate actual text
            if not actual_text or not actual_text.strip():
                result['error'] = "Actual text cannot be empty"
                return result

            if len(actual_text) > 280:
                result['error'] = f"Actual text too long ({len(actual_text)} chars, max 280)"
                return result

            # Get contract
            contract = self.blockchain.contracts.get('PredictionMarketV2')
            if not contract:
                result['error'] = "PredictionMarketV2 contract not loaded"
                return result

            # Check if we have owner key for signing
            if not self.owner_private_key:
                # Return unsigned transaction data for manual signing
                result['error'] = "Owner private key not configured - manual signing required"
                result['unsigned_tx'] = {
                    'to': contract.address,
                    'data': contract.encodeABI(fn_name='resolveMarket', args=[market_id, actual_text]),
                    'chainId': self.blockchain.chain_id
                }
                return result

            # Build and sign transaction
            account = Account.from_key(self.owner_private_key)

            # Verify this is the contract owner
            contract_owner = contract.functions.owner().call()
            if account.address.lower() != contract_owner.lower():
                result['error'] = f"Account {account.address} is not the contract owner ({contract_owner})"
                return result

            # Build transaction
            nonce = self.blockchain.w3.eth.get_transaction_count(account.address)
            gas_price = self.blockchain.w3.eth.gas_price

            # Estimate gas - Levenshtein calculation can be expensive
            try:
                gas_estimate = contract.functions.resolveMarket(market_id, actual_text).estimate_gas({
                    'from': account.address
                })
                gas_limit = int(gas_estimate * 1.5)  # Add 50% buffer for Levenshtein
            except Exception as e:
                logger.warning(f"Gas estimation failed: {e}, using default")
                gas_limit = 3000000  # High default for Levenshtein

            tx = contract.functions.resolveMarket(market_id, actual_text).build_transaction({
                'from': account.address,
                'nonce': nonce,
                'gas': gas_limit,
                'gasPrice': gas_price,
                'chainId': self.blockchain.chain_id
            })

            # Sign transaction
            signed_tx = self.blockchain.w3.eth.account.sign_transaction(tx, self.owner_private_key)

            # Send transaction
            tx_hash = self.blockchain.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            tx_hash_hex = tx_hash.hex()

            logger.info(f"Resolution transaction sent for market {market_id}: {tx_hash_hex}")

            # Wait for receipt
            receipt = self.blockchain.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

            if receipt['status'] == 1:
                result['success'] = True
                result['tx_hash'] = tx_hash_hex
                result['gas_used'] = receipt['gasUsed']
                result['block_number'] = receipt['blockNumber']
                logger.info(f"Market {market_id} resolved successfully in block {receipt['blockNumber']}")
            else:
                result['error'] = "Transaction failed"
                result['tx_hash'] = tx_hash_hex
                logger.error(f"Resolution transaction failed for market {market_id}")

            return result

        except Exception as e:
            logger.error(f"Error resolving market {market_id}: {e}")
            result['error'] = str(e)
            return result

    async def auto_resolve_market(self, market_id: int, tweet_url: str) -> Dict[str, Any]:
        """Automatically resolve a market by fetching tweet and calling resolveMarket

        Args:
            market_id: The market ID to resolve
            tweet_url: URL of the actual tweet to use for resolution

        Returns:
            Dict with resolution result
        """
        result = {
            'success': False,
            'tx_hash': None,
            'error': None,
            'market_id': market_id,
            'tweet_text': None
        }

        try:
            # Get market details
            market = self.get_market_for_resolution(market_id)
            if not market:
                result['error'] = f"Market {market_id} not found"
                return result

            if not market['can_resolve']:
                if market['resolved']:
                    result['error'] = "Market already resolved"
                elif market['submission_count'] < 2:
                    result['error'] = f"Need at least 2 submissions (has {market['submission_count']})"
                else:
                    result['error'] = "Market not eligible for resolution"
                return result

            # Fetch actual tweet
            actor_handle = market['actor_handle']
            tweet_data = await self.fetch_actual_tweet(actor_handle, tweet_url)

            if not tweet_data:
                result['error'] = f"Could not fetch tweet for @{actor_handle}"
                return result

            actual_text = tweet_data.get('text', '')
            if not actual_text:
                result['error'] = "Tweet has no text content"
                return result

            result['tweet_text'] = actual_text

            # Resolve market with actual text
            resolution_result = self.resolve_market(market_id, actual_text)

            result['success'] = resolution_result['success']
            result['tx_hash'] = resolution_result.get('tx_hash')
            result['error'] = resolution_result.get('error')
            result['gas_used'] = resolution_result.get('gas_used')

            return result

        except Exception as e:
            logger.error(f"Error auto-resolving market {market_id}: {e}")
            result['error'] = str(e)
            return result

    def withdraw_fees(self) -> Dict[str, Any]:
        """Withdraw accumulated platform fees (owner only)

        Returns:
            Dict with 'success', 'tx_hash', 'amount', 'error' fields
        """
        result = {
            'success': False,
            'tx_hash': None,
            'amount': None,
            'error': None
        }

        try:
            contract = self.blockchain.contracts.get('PredictionMarketV2')
            if not contract:
                result['error'] = "PredictionMarketV2 contract not loaded"
                return result

            if not self.owner_private_key:
                result['error'] = "Owner private key not configured"
                return result

            account = Account.from_key(self.owner_private_key)

            # Get pending fees
            pending_fees = self.blockchain.get_v2_pending_fees(account.address)
            if pending_fees <= 0:
                result['error'] = "No fees to withdraw"
                return result

            result['amount'] = str(pending_fees)

            # Build transaction
            nonce = self.blockchain.w3.eth.get_transaction_count(account.address)
            gas_price = self.blockchain.w3.eth.gas_price

            tx = contract.functions.withdrawFees().build_transaction({
                'from': account.address,
                'nonce': nonce,
                'gas': 100000,
                'gasPrice': gas_price,
                'chainId': self.blockchain.chain_id
            })

            # Sign and send
            signed_tx = self.blockchain.w3.eth.account.sign_transaction(tx, self.owner_private_key)
            tx_hash = self.blockchain.w3.eth.send_raw_transaction(signed_tx.raw_transaction)

            # Wait for receipt
            receipt = self.blockchain.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)

            if receipt['status'] == 1:
                result['success'] = True
                result['tx_hash'] = tx_hash.hex()
                logger.info(f"Fees withdrawn: {pending_fees} ETH, tx: {tx_hash.hex()}")
            else:
                result['error'] = "Transaction failed"
                result['tx_hash'] = tx_hash.hex()

            return result

        except Exception as e:
            logger.error(f"Error withdrawing fees: {e}")
            result['error'] = str(e)
            return result

    def get_resolution_stats(self) -> Dict[str, Any]:
        """Get overall resolution statistics"""
        try:
            market_count = self.blockchain.get_v2_market_count()
            resolved_count = 0
            pending_count = 0
            active_count = 0
            total_pool = Decimal(0)

            current_time = int(datetime.now().timestamp())

            for market_id in range(market_count):
                market = self.blockchain.get_v2_market(market_id)
                if market:
                    total_pool += Decimal(str(market['total_pool']))
                    if market['resolved']:
                        resolved_count += 1
                    elif market['end_time'] < current_time:
                        pending_count += 1
                    else:
                        active_count += 1

            # Get pending platform fees
            pending_fees = self.blockchain.get_v2_pending_fees(self.owner_address)

            return {
                'total_markets': market_count,
                'resolved_markets': resolved_count,
                'pending_resolution': pending_count,
                'active_markets': active_count,
                'total_pool': str(total_pool),
                'pending_platform_fees': str(pending_fees),
                'owner_address': self.owner_address,
                'owner_key_configured': bool(self.owner_private_key),
                'xcom_api_configured': self.xcom.get_api_status()['api_configured']
            }
        except Exception as e:
            logger.error(f"Error getting resolution stats: {e}")
            return {}


# Singleton instance
_resolution_service = None

def get_resolution_service() -> V2ResolutionService:
    """Get or create resolution service singleton"""
    global _resolution_service
    if _resolution_service is None:
        _resolution_service = V2ResolutionService()
    return _resolution_service
