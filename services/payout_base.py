# UPDATED FOR PHASE 1: This service now reads from blockchain only.
# Database writes have been disabled and database reads are being phased out.

import logging
from decimal import Decimal
from typing import Dict, Any, List, Optional
# from app import db  # Phase 7: Database removed
# from models import PredictionMarket, Submission, Bet, Transaction  # Phase 7: Models removed
from services.blockchain_base import BaseBlockchainService
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class BasePayoutService:
    """Payout service for BASE blockchain integration"""
    
    def __init__(self):
        self.blockchain = BaseBlockchainService()
    # self.platform_fee_percentage = Decimal(os.environ.get('PLATFORM_FEE', '7')) / Decimal('100')  # Phase 7: Database removed
        
    def calculate_payouts(self, market_id: int) -> Dict[str, Any]:
        """Calculate payouts for a resolved market
        
        PHASE 1: This method now reads from blockchain only.
        Database reads will be replaced with blockchain calls.
        """
        try:
            # Phase 1: Read market data from blockchain
            market = self.blockchain.get_market(market_id)
    # if not market or not market.get('resolved'):  # Phase 7: Database removed
                logger.error(f"Market {market_id} not found or not resolved")
                return {'error': 'Market not resolved'}
                
    # winning_submission_id = market.get('winning_submission_id')  # Phase 7: Database removed
            if not winning_submission_id:
                logger.error(f"Market {market_id} has no winning submission")
                return {'error': 'No winning submission'}
                
            # Get winning submission from blockchain
            winning_submission = self.blockchain.get_submission(winning_submission_id)
            if not winning_submission:
                logger.error(f"Winning submission {winning_submission_id} not found")
                return {'error': 'Winning submission not found'}
                
            # Phase 1: Payout calculation is now handled by PayoutManager contract
            # The complex payout logic below is deprecated and will be removed
            return {
                'status': 'success',
                'message': 'Payout calculation is now handled by the PayoutManager smart contract',
                'market_id': market_id,
                'winning_submission_id': winning_submission_id,
    # 'contract_address': self.blockchain.contracts.get('PayoutManager').address if self.blockchain.contracts.get('PayoutManager') else None,  # Phase 7: Database removed
                'note': 'Please use the PayoutManager contract directly for payout operations'
            }
            
            # DEPRECATED: Database-based payout logic below
            # This code will be removed in Phase 2
            
            # Calculate total losing pool
            losing_pool = Decimal('0')
            winning_pool = Decimal('0')
            
            for submission in all_submissions:
                # Get all bets for this submission
    # bets = Bet.query.filter_by(submission_id=submission.id).all()  # Phase 7: Database removed
                total_bets = sum(Decimal(str(bet.amount)) for bet in bets)
                
                # Add initial stake
                total_stake = Decimal(str(submission.initial_stake_amount)) + total_bets
                
                if submission.id == market.winning_submission_id:
                    winning_pool = total_stake
                else:
                    losing_pool += total_stake
                    
            # Calculate platform fees
            total_volume = winning_pool + losing_pool
            platform_fees = total_volume * self.platform_fee_percentage
            distributable_pool = losing_pool - (losing_pool * self.platform_fee_percentage)
            
            # Calculate individual payouts
            payouts = []
            
            # Payout for winning submission creator
            creator_payout = {
                'recipient': winning_submission.creator_wallet,
                'type': 'submission_creator',
                'stake': Decimal(str(winning_submission.initial_stake_amount)),
                'winnings': Decimal('0'),
                'total': Decimal(str(winning_submission.initial_stake_amount))
            }
            
            if winning_pool > 0:
                creator_share = (creator_payout['stake'] / winning_pool) * distributable_pool
                creator_payout['winnings'] = creator_share
                creator_payout['total'] = creator_payout['stake'] + creator_share
                
            payouts.append(creator_payout)
            
            # Payouts for winning bettors
    # winning_bets = Bet.query.filter_by(submission_id=market.winning_submission_id).all()  # Phase 7: Database removed
            
            for bet in winning_bets:
                bet_amount = Decimal(str(bet.amount))
                winnings = Decimal('0')
                
                if winning_pool > 0:
                    bet_share = (bet_amount / winning_pool) * distributable_pool
                    winnings = bet_share
                    
                payout = {
                    'recipient': bet.bettor_wallet,
                    'type': 'bet',
                    'bet_id': str(bet.id),
                    'stake': bet_amount,
                    'winnings': winnings,
                    'total': bet_amount + winnings
                }
                
                payouts.append(payout)
                
                # Update bet with payout amount
                bet.payout_amount = bet_amount + winnings
                
            # Update market with fee info
            market.platform_fee_collected = platform_fees
            market.total_volume = total_volume
            
    # db.session.commit()  # Phase 7: Database removed
            
            return {
                'market_id': str(market_id),
                'winning_submission_id': str(market.winning_submission_id),
                'total_volume': str(total_volume),
                'winning_pool': str(winning_pool),
                'losing_pool': str(losing_pool),
                'platform_fees': str(platform_fees),
                'distributable_pool': str(distributable_pool),
                'payouts': payouts,
                'payout_count': len(payouts),
                'total_payout': str(sum(p['total'] for p in payouts))
            }
            
        except Exception as e:
            logger.error(f"Error calculating payouts: {e}")
            return {'error': str(e)}
            
    def process_payouts(self, market_id: str, private_key: str) -> Dict[str, Any]:
        """Process actual payouts on BASE blockchain"""
        try:
            # Calculate payouts first
            payout_info = self.calculate_payouts(market_id)
            if 'error' in payout_info:
                return payout_info
                
            processed_payouts = []
            failed_payouts = []
            
            # Load contract deployment info
    # deployment_file = 'deployment-sepolia.json' if os.environ.get('NETWORK') == 'testnet' else 'deployment-mainnet.json'  # Phase 7: Database removed
            if os.path.exists(deployment_file):
                self.blockchain.load_contracts(deployment_file)
            else:
                logger.warning("Contract deployment file not found, using manual payouts")
                
            for payout in payout_info['payouts']:
                try:
                    # Process payout through smart contract
                    if self.blockchain.contracts['PayoutManager']:
                        # Use PayoutManager contract
                        tx_data = self.blockchain.claim_payout(
                            int(market_id),
                            payout['recipient']
                        )
                        
                        tx_hash = self.blockchain.send_transaction(
                            tx_data['function'],
                            tx_data['params'],
                            private_key
                        )
                    else:
                        # Manual payout
                        tx_hash = self.blockchain.send_transaction(
                            None,  # No function, direct transfer
                            {
                                'to': payout['recipient'],
                                'value': self.blockchain.w3.to_wei(payout['total'], 'ether'),
                                'from': self.blockchain.w3.eth.account.from_key(private_key).address
                            },
                            private_key
                        )
                        
                    if tx_hash:
                        # Create transaction record
                        transaction = Transaction(
                            transaction_hash=tx_hash,
                            from_address=self.blockchain.w3.eth.account.from_key(private_key).address,
                            to_address=payout['recipient'],
                            amount=payout['total'],
                            transaction_type='payout',
                            related_market_id=market_id,
                            platform_fee=Decimal('0')
                        )
    # db.session.add(transaction)  # Phase 7: Database removed
                        
                        # Update bet payout status
                        if payout['type'] == 'bet' and 'bet_id' in payout:
    # bet = Bet.query.get(payout['bet_id'])  # Phase 7: Database removed
                            if bet:
                                bet.payout_tx_hash = tx_hash
                                bet.status = 'won'
                                
                        processed_payouts.append({
                            'recipient': payout['recipient'],
                            'amount': str(payout['total']),
                            'tx_hash': tx_hash
                        })
                        
                        logger.info(f"Processed payout of {payout['total']} to {payout['recipient']}")
                    else:
                        failed_payouts.append(payout)
                        
                except Exception as e:
                    logger.error(f"Error processing payout to {payout['recipient']}: {e}")
                    failed_payouts.append(payout)
                    
    # db.session.commit()  # Phase 7: Database removed
            
            return {
                'market_id': str(market_id),
                'processed': processed_payouts,
                'failed': failed_payouts,
                'total_processed': len(processed_payouts),
                'total_failed': len(failed_payouts)
            }
            
        except Exception as e:
            logger.error(f"Error processing payouts: {e}")
    # db.session.rollback()  # Phase 7: Database removed
            return {'error': str(e)}
            
    def estimate_payout_gas(self, market_id: str) -> Dict[str, Any]:
        """Estimate gas costs for processing payouts"""
        try:
            payout_info = self.calculate_payouts(market_id)
            if 'error' in payout_info:
                return payout_info
                
            gas_prices = self.blockchain.estimate_gas_price()
            
            # Estimate gas per payout (typical BASE payout)
            gas_per_payout = 50000  # Approximate gas for contract payout
            total_gas = gas_per_payout * len(payout_info['payouts'])
            
            gas_costs = {
                'payouts': len(payout_info['payouts']),
                'gas_per_payout': gas_per_payout,
                'total_gas': total_gas,
                'standard_cost': self.blockchain.w3.from_wei(total_gas * gas_prices['standard'], 'ether'),
                'fast_cost': self.blockchain.w3.from_wei(total_gas * gas_prices['fast'], 'ether'),
                'slow_cost': self.blockchain.w3.from_wei(total_gas * gas_prices['slow'], 'ether'),
                'gas_prices': {
                    'standard': gas_prices['standard'],
                    'fast': gas_prices['fast'],
                    'slow': gas_prices['slow']
                }
            }
            
            return gas_costs
            
        except Exception as e:
            logger.error(f"Error estimating gas: {e}")
            return {'error': str(e)}
            
    def batch_process_payouts(self, market_ids: List[str], private_key: str) -> Dict[str, Any]:
        """Process payouts for multiple markets in batch"""
        results = {
            'processed_markets': [],
            'failed_markets': [],
            'total_payouts': 0,
            'total_gas_used': 0
        }
        
        for market_id in market_ids:
            try:
                result = self.process_payouts(market_id, private_key)
                if 'error' not in result:
                    results['processed_markets'].append(market_id)
                    results['total_payouts'] += result['total_processed']
                else:
                    results['failed_markets'].append({
                        'market_id': market_id,
                        'error': result['error']
                    })
            except Exception as e:
                logger.error(f"Error processing market {market_id}: {e}")
                results['failed_markets'].append({
                    'market_id': market_id,
                    'error': str(e)
                })
                
        return results