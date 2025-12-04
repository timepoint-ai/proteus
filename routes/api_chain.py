"""
Phase 3: Chain-only API routes
All data fetched directly from blockchain, no database dependencies
"""

from flask import Blueprint, request, jsonify
import logging
from datetime import datetime
from web3 import Web3
from services.blockchain_base import BaseBlockchainService
from utils.api_errors import (
    error_response, success_response, not_found, blockchain_error, ErrorCode
)
import json
import os

logger = logging.getLogger(__name__)

api_chain_bp = Blueprint('api_chain', __name__)

# Initialize blockchain service
blockchain_service = BaseBlockchainService()

# Load contract ABIs
def load_contract_abi(contract_name):
    """Load contract ABI from artifacts"""
    artifact_paths = {
        'EnhancedPredictionMarket': 'artifacts/contracts/src/EnhancedPredictionMarket.sol/EnhancedPredictionMarket.json',
        'ActorRegistry': 'artifacts/contracts/src/ActorRegistry.sol/ActorRegistry.json',
        'DecentralizedOracle': 'artifacts/contracts/src/DecentralizedOracle.sol/DecentralizedOracle.json',
        'PayoutManager': 'artifacts/contracts/src/PayoutManager.sol/PayoutManager.json',
        'GenesisNFT': 'artifacts/contracts/src/GenesisNFT.sol/GenesisNFT.json'
    }
    
    if contract_name not in artifact_paths:
        return None
    
    artifact_path = artifact_paths[contract_name]
    if os.path.exists(artifact_path):
        with open(artifact_path, 'r') as f:
            artifact = json.load(f)
            return artifact.get('abi', [])
    return None

@api_chain_bp.route('/actors', methods=['GET'])
def get_actors_chain():
    """Get all actors from ActorRegistry contract"""
    try:
        # Get ActorRegistry contract
        actor_registry = blockchain_service.contracts.get('ActorRegistry')
        if not actor_registry:
            # Return empty result if contract not available
            return jsonify({
                'actors': [],
                'total': 0,
                'source': 'blockchain'
            })
        
        actors_data = []
        
        try:
            # Query ActorRegistered events using get_logs
            event_signature = actor_registry.events.ActorRegistered()
            logs = blockchain_service.w3.eth.get_logs({
                'fromBlock': 0,
                'toBlock': 'latest',
                'address': actor_registry.address,
                'topics': [event_signature.event_topic]
            })
            
            # Process each actor
            actor_addresses = set()
            for log in logs:
                try:
                    decoded = actor_registry.events.ActorRegistered().process_log(log)
                    actor_address = decoded['args']['actorAddress']
                    
                    if actor_address not in actor_addresses:
                        actor_addresses.add(actor_address)
                        
                        # Get actor details from contract if possible
                        try:
                            actor_info = actor_registry.functions.getActor(actor_address).call()
                            actors_data.append({
                                'address': actor_address,
                                'name': actor_info[0] if len(actor_info) > 0 else 'Unknown',
                                'x_username': actor_info[1] if len(actor_info) > 1 else '',
                                'verified': actor_info[2] if len(actor_info) > 2 else False,
                                'block_number': log['blockNumber']
                            })
                        except:
                            # If can't get details, add basic info
                            actors_data.append({
                                'address': actor_address,
                                'name': 'Unknown',
                                'x_username': '',
                                'verified': False,
                                'block_number': log['blockNumber']
                            })
                except Exception as e:
                    logger.debug(f"Could not process actor log: {e}")
                    
        except Exception as e:
            logger.debug(f"Could not query actor events: {e}")
            # Return empty result if events can't be queried
        
        return jsonify({
            'actors': actors_data,
            'total': len(actors_data),
            'source': 'blockchain'
        })
        
    except Exception as e:
        logger.error(f"Error fetching actors from chain: {e}")
        return jsonify({
            'actors': [],
            'total': 0,
            'source': 'blockchain',
            'error': str(e)
        })

@api_chain_bp.route('/markets', methods=['GET'])
def get_markets_chain():
    """Get all markets from EnhancedPredictionMarket contract"""
    try:
        # Get contract
        market_contract = blockchain_service.contracts.get('EnhancedPredictionMarket')
        if not market_contract:
            # Return empty result if contract not available
            return jsonify({
                'markets': [],
                'total': 0,
                'source': 'blockchain'
            })
        
        markets_data = []
        
        try:
            # Query MarketCreated events using get_logs
            event_signature = market_contract.events.MarketCreated()
            logs = blockchain_service.w3.eth.get_logs({
                'fromBlock': 0,
                'toBlock': 'latest',
                'address': market_contract.address,
                'topics': [event_signature.event_topic]
            })
            
            for log in logs:
                try:
                    decoded = market_contract.events.MarketCreated().process_log(log)
                    market_id = decoded['args']['marketId']
                    
                    # Try to get market details from contract
                    try:
                        market_info = market_contract.functions.getMarket(market_id).call()
                        markets_data.append({
                            'id': market_id,
                            'actor_address': market_info[0] if len(market_info) > 0 else '0x0',
                            'start_time': market_info[1] if len(market_info) > 1 else 0,
                            'end_time': market_info[2] if len(market_info) > 2 else 0,
                            'status': market_info[3] if len(market_info) > 3 else 'unknown',
                            'total_volume': str(market_info[4]) if len(market_info) > 4 else '0',
                            'block_number': log['blockNumber'],
                            'transaction_hash': log['transactionHash'].hex()
                        })
                    except:
                        # If can't get details, add basic info
                        markets_data.append({
                            'id': market_id,
                            'actor_address': '0x0',
                            'start_time': 0,
                            'end_time': 0,
                            'status': 'unknown',
                            'total_volume': '0',
                            'block_number': log['blockNumber'],
                            'transaction_hash': log['transactionHash'].hex()
                        })
                except Exception as e:
                    logger.debug(f"Could not process market log: {e}")
                    
        except Exception as e:
            logger.debug(f"Could not query market events: {e}")
            # Return empty result if events can't be queried
        
        # Filter by status if requested
        status = request.args.get('status')
        if status:
            markets_data = [m for m in markets_data if m['status'] == status]
        
        return jsonify({
            'markets': markets_data,
            'total': len(markets_data),
            'source': 'blockchain'
        })
        
    except Exception as e:
        logger.error(f"Error fetching markets from chain: {e}")
        return jsonify({
            'markets': [],
            'total': 0,
            'source': 'blockchain',
            'error': str(e)
        })

@api_chain_bp.route('/stats', methods=['GET'])
def get_stats_chain():
    """Get platform statistics from blockchain"""
    try:
        stats = {
            'total_markets': 0,
            'active_markets': 0,
            'resolved_markets': 0,
            'total_volume': '0',
            'total_actors': 0,
            'genesis_nft_holders': 0,
            'gas_price': '0',
            'source': 'blockchain'
        }
        
        # Get markets count
        market_contract = blockchain_service.contracts.get('EnhancedPredictionMarket')
        if market_contract:
            try:
                # Query events for statistics
                filter = market_contract.events.MarketCreated.create_filter(from_block=0, to_block='latest')
                events = filter.get_all_entries()
                stats['total_markets'] = len(events)
                
                # Count by status (would need to query each market)
                active_count = 0
                resolved_count = 0
                total_volume = 0
                
                for event in events:
                    try:
                        market_id = event['args']['marketId']
                        market_info = market_contract.functions.getMarket(market_id).call()
                        
                        if len(market_info) > 3:
                            status = market_info[3]
                            if status == 'active':
                                active_count += 1
                            elif status == 'resolved':
                                resolved_count += 1
                        
                        if len(market_info) > 4:
                            total_volume += int(market_info[4])
                    except:
                        pass
                
                stats['active_markets'] = active_count
                stats['resolved_markets'] = resolved_count
                stats['total_volume'] = str(total_volume)
                
            except Exception as e:
                logger.warning(f"Could not fetch market stats: {e}")
        
        # Get actors count
        actor_registry = blockchain_service.contracts.get('ActorRegistry')
        if actor_registry:
            try:
                filter = actor_registry.events.ActorRegistered.create_filter(from_block=0, to_block='latest')
                events = filter.get_all_entries()
                stats['total_actors'] = len(set(e['args']['actorAddress'] for e in events))
            except Exception as e:
                logger.warning(f"Could not fetch actor count: {e}")
        
        # Get Genesis NFT holders count
        genesis_nft = blockchain_service.contracts.get('GenesisNFT')
        if genesis_nft:
            try:
                # Get total supply
                total_supply = genesis_nft.functions.totalSupply().call()
                stats['genesis_nft_holders'] = total_supply
            except Exception as e:
                logger.warning(f"Could not fetch NFT stats: {e}")
        
        # Get current gas price
        try:
            gas_price = blockchain_service.w3.eth.gas_price
            stats['gas_price'] = str(gas_price)
        except:
            pass
        
        return jsonify(stats)

    except Exception as e:
        logger.error(f"Error fetching stats from chain: {e}")
        return blockchain_error(f'Failed to fetch platform stats: {str(e)}')

@api_chain_bp.route('/market/<market_id>', methods=['GET'])
def get_market_detail_chain(market_id):
    """Get detailed market information from blockchain"""
    try:
        market_contract = blockchain_service.contracts.get('EnhancedPredictionMarket')
        if not market_contract:
            return error_response(ErrorCode.SERVICE_UNAVAILABLE, 'Market contract not available', 503)
        
        # Get market details
        market_info = market_contract.functions.getMarket(int(market_id)).call()
        
        # Get submissions for this market
        submission_filter = market_contract.events.SubmissionCreated.create_filter(
            from_block=0,
            to_block='latest',
            argument_filters={'marketId': int(market_id)}
        )
        submission_events = submission_filter.get_all_entries()
        
        submissions = []
        for event in submission_events:
            submissions.append({
                'id': event['args']['submissionId'] if 'submissionId' in event['args'] else len(submissions),
                'creator': event['args']['creator'] if 'creator' in event['args'] else '0x0',
                'predicted_text': event['args']['predictedText'] if 'predictedText' in event['args'] else '',
                'stake': str(event['args']['stake']) if 'stake' in event['args'] else '0',
                'block_number': event['blockNumber']
            })
        
        # Get bets for this market
        bet_filter = market_contract.events.BetPlaced.create_filter(
            from_block=0,
            to_block='latest',
            argument_filters={'marketId': int(market_id)}
        )
        bet_events = bet_filter.get_all_entries()
        
        total_bet_volume = sum(int(e['args']['amount']) for e in bet_events if 'amount' in e['args'])
        
        return jsonify({
            'market': {
                'id': market_id,
                'actor_address': market_info[0] if len(market_info) > 0 else '0x0',
                'start_time': market_info[1] if len(market_info) > 1 else 0,
                'end_time': market_info[2] if len(market_info) > 2 else 0,
                'status': market_info[3] if len(market_info) > 3 else 'unknown',
                'total_volume': str(market_info[4]) if len(market_info) > 4 else '0',
                'submissions': submissions,
                'bet_count': len(bet_events),
                'bet_volume': str(total_bet_volume)
            },
            'source': 'blockchain'
        })

    except Exception as e:
        logger.error(f"Error fetching market detail from chain: {e}")
        return blockchain_error(f'Failed to fetch market details: {str(e)}')

@api_chain_bp.route('/oracle/submissions/<market_id>', methods=['GET'])
def get_oracle_submissions_chain(market_id):
    """Get oracle submissions for a market from blockchain"""
    try:
        oracle_contract = blockchain_service.contracts.get('DecentralizedOracle')
        if not oracle_contract:
            return error_response(ErrorCode.SERVICE_UNAVAILABLE, 'Oracle contract not available', 503)
        
        # Query OracleDataSubmitted events for this market
        filter = oracle_contract.events.OracleDataSubmitted.create_filter(
            from_block=0,
            to_block='latest',
            argument_filters={'marketId': int(market_id)}
        )
        events = filter.get_all_entries()
        
        submissions = []
        for event in events:
            submissions.append({
                'oracle': event['args']['oracle'] if 'oracle' in event['args'] else '0x0',
                'actual_text': event['args']['actualText'] if 'actualText' in event['args'] else '',
                'source_url': event['args']['sourceUrl'] if 'sourceUrl' in event['args'] else '',
                'timestamp': event['args']['timestamp'] if 'timestamp' in event['args'] else 0,
                'block_number': event['blockNumber'],
                'transaction_hash': event['transactionHash'].hex()
            })
        
        return jsonify({
            'market_id': market_id,
            'submissions': submissions,
            'total': len(submissions),
            'source': 'blockchain'
        })

    except Exception as e:
        logger.error(f"Error fetching oracle submissions from chain: {e}")
        return blockchain_error(f'Failed to fetch oracle submissions: {str(e)}')

@api_chain_bp.route('/genesis/holders', methods=['GET'])
def get_genesis_holders():
    """Get Genesis NFT holders from blockchain"""
    try:
        genesis_nft = blockchain_service.contracts.get('GenesisNFT')
        if not genesis_nft:
            # Return empty result if contract not available
            return jsonify({
                'holders': [],
                'total_holders': 0,
                'total_supply': 100,
                'source': 'blockchain'
            })
        
        holders = []
        
        try:
            # Get Transfer events to track current holders
            event_signature = genesis_nft.events.Transfer()
            logs = blockchain_service.w3.eth.get_logs({
                'fromBlock': 0,
                'toBlock': 'latest',
                'address': genesis_nft.address,
                'topics': [event_signature.event_topic]
            })
            
            # Track ownership by processing transfers
            ownership = {}
            for log in logs:
                try:
                    decoded = genesis_nft.events.Transfer().process_log(log)
                    token_id = decoded['args']['tokenId']
                    to_address = decoded['args']['to']
                    from_address = decoded['args']['from']
                    
                    # Remove from previous owner
                    if from_address != '0x0000000000000000000000000000000000000000':
                        if from_address in ownership:
                            ownership[from_address].discard(token_id)
                    
                    # Add to new owner
                    if to_address != '0x0000000000000000000000000000000000000000':
                        if to_address not in ownership:
                            ownership[to_address] = set()
                        ownership[to_address].add(token_id)
                except Exception as e:
                    logger.debug(f"Could not process transfer log: {e}")
                    
        except Exception as e:
            logger.debug(f"Could not query transfer events: {e}")
            # Return empty result if events can't be queried
        
        # Format holder data
        for address, token_ids in ownership.items():
            if len(token_ids) > 0:  # Only include addresses that still hold tokens
                holders.append({
                    'address': address,
                    'token_count': len(token_ids),
                    'token_ids': list(token_ids),
                    'percentage_owned': len(token_ids)  # Out of 100 total
                })
        
        # Sort by token count
        holders.sort(key=lambda x: x['token_count'], reverse=True)
        
        return jsonify({
            'holders': holders,
            'total_holders': len(holders),
            'total_supply': 100,
            'source': 'blockchain'
        })
        
    except Exception as e:
        logger.error(f"Error fetching Genesis holders from chain: {e}")
        return jsonify({
            'holders': [],
            'total_holders': 0,
            'total_supply': 100,
            'source': 'blockchain',
            'error': str(e)
        })