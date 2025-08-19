from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
import json
import logging
from datetime import datetime, timedelta
from services.time_sync import TimeSyncService
from services.blockchain_base import BaseBlockchainService
from web3 import Web3

logger = logging.getLogger(__name__)
clockchain_bp = Blueprint('clockchain', __name__)
time_sync_service = TimeSyncService()

# Initialize blockchain service
blockchain_service = BaseBlockchainService()

@clockchain_bp.route('/clockchain')
def clockchain_view():
    """Display the Clockchain timeline view - Phase 7 Blockchain-Only"""
    try:
        # Get current Pacific time
        time_status = time_sync_service.get_time_health_status()
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = 10  # Show 10 items per page
        
        # Calculate time range
        current_time = datetime.utcnow()
        current_time_ms = int(current_time.timestamp() * 1000)
        
        # Initialize timeline segments - Phase 7: All data from blockchain
        timeline_segments = []
        
        # Try to get actual markets from blockchain
        try:
            # Check if we have the EnhancedPredictionMarket contract  
            if hasattr(blockchain_service, 'contracts') and blockchain_service.contracts.get('EnhancedPredictionMarket'):
                # Try to get all markets (up to 100 for now)
                for market_id in range(0, 100):  # Try first 100 market IDs
                    try:
                        if blockchain_service.contracts:
                            market = blockchain_service.contracts['EnhancedPredictionMarket'].functions.markets(market_id).call()
                            
                            # Only process if we got valid market data
                            if market and len(market) > 5:
                                # Convert market data to timeline segment
                                segment = {
                                    'id': str(market_id),  # Use actual market ID
                                    'actor': {
                                        'id': market_id,
                                        'x_username': market[2] if len(market) > 2 and market[2] else 'Unknown',  # actorName
                                        'display_name': market[2] if len(market) > 2 and market[2] else 'Unknown Actor',
                                        'verified': False,
                                        'follower_count': 0,
                                        'is_test_account': False
                                    },
                                    'start_time': datetime.fromtimestamp(market[3]) if len(market) > 3 else datetime.now(),  # startTime
                                    'end_time': datetime.fromtimestamp(market[4]) if len(market) > 4 else datetime.now(),  # endTime
                                    'start_ms': market[3] * 1000 if len(market) > 3 else 0,
                                    'end_ms': market[4] * 1000 if len(market) > 4 else 0,
                                    'status': 'resolved' if len(market) > 5 and market[5] else 'active',  # isResolved
                                    'submission_count': len(market[6]) if len(market) > 6 and market[6] else 0,
                                    'total_volume': str(Web3.from_wei(market[7], 'ether')) if len(market) > 7 and market[7] else '0',
                                    'currency': 'ETH',
                                    'predicted_text': market[1] if len(market) > 1 else '',  # question
                                    'creator_wallet': market[0][:10] + '...' if len(market) > 0 and market[0] else '0x...',  # creator address shortened
                                    'initial_stake': '0.01',
                                    'stake_count': 1,
                                    'oracle_allowed': market[4] < int(current_time.timestamp()) if len(market) > 4 else False,
                                    'time_until_oracle': max(0, market[4] - int(current_time.timestamp())) if len(market) > 4 else 0,
                                    'submissions': [],
                                    'competing_bets': []
                                }
                                timeline_segments.append(segment)
                    except Exception as e:
                        logger.debug(f"Error fetching market {market_id}: {e}")
                        continue
        except Exception as e:
            logger.error(f"Error fetching markets from blockchain: {e}")
            
        # If no markets found, just keep the list empty
        # Phase 7: Only show real blockchain data, no placeholders
        
        # Blockchain stats (placeholder for now)
        active_market_count = 0
        total_bet_volume = 0
        total_count = len(timeline_segments)
        has_more_pages = False
        
        return render_template('clockchain/timeline.html',
                             time_status=time_status,
                             timeline_segments=timeline_segments,
                             current_page=page,
                             has_more_pages=has_more_pages,
                             current_time_ms=current_time_ms,
                             active_bet_count=active_market_count,
                             total_bet_volume=str(total_bet_volume),
                             total_count=total_count,
                             displayed_count=len(timeline_segments),
                             view_type='all')
        
    except Exception as e:
        logger.error(f"Error loading clockchain view: {e}")
        return render_template('clockchain/timeline.html',
                             time_status={},
                             timeline_segments=[],
                             hours_before=24,
                             hours_after=24,
                             current_time_ms=0,
                             min_time_ms=0,
                             max_time_ms=0,
                             active_bet_count=0,
                             total_bet_volume='0',
                             total_count=0,
                             displayed_count=0,
                             has_more_records=False,
                             now_marker_shown=False)

@clockchain_bp.route('/api/clockchain/events')
def get_clockchain_events():
    """Get clockchain events for a specific time range - Phase 7 Blockchain-Only"""
    try:
        # Get time range from query params
        start_ms = request.args.get('start_ms', type=int)
        end_ms = request.args.get('end_ms', type=int)
        
        if not start_ms or not end_ms:
            return jsonify({'error': 'start_ms and end_ms parameters required'}), 400
            
        # Phase 7: Return empty events for now (all data on blockchain)
        events = []
            
        return jsonify({
            'events': events,
            'count': len(events),
            'message': 'Phase 7: All data on blockchain. Use blockchain API endpoints.'
        })
        
    except Exception as e:
        logger.error(f"Error getting clockchain events: {e}")
        return jsonify({'error': 'Failed to get events'}), 500

@clockchain_bp.route('/clockchain/markets/create')
@clockchain_bp.route('/clockchain/create')
def create_market():
    """Display market creation form"""
    return render_template('markets/create.html')

@clockchain_bp.route('/clockchain/market/<market_id>')
@clockchain_bp.route('/clockchain/market/blockchain-message')
def market_detail(market_id='blockchain-message'):
    """Display detailed view of a prediction market - Phase 7 Blockchain-Only"""
    try:
        # Phase 7: Only show real blockchain data
        # Try to get market from blockchain
        market_data = None
        
        # Try to fetch from blockchain if contract is available
        if hasattr(blockchain_service, 'contracts') and blockchain_service.contracts.get('EnhancedPredictionMarket'):
            try:
                if blockchain_service.contracts:
                    contract = blockchain_service.contracts['EnhancedPredictionMarket']
                    # Try to get market data
                    market = contract.functions.markets(int(market_id)).call()
                    
                    if market and len(market) > 0:
                            market_data = {
                            'id': market_id,
                            'creator': market[0] if len(market) > 0 else 'Not found',
                            'predicted_text': market[1] if len(market) > 1 else 'No prediction text',
                            'actor': market[2] if len(market) > 2 else 'Unknown',
                            'time_range': 'From blockchain',
                            'initial_stake': '0 ETH',
                            'total_volume': str(Web3.from_wei(market[7], 'ether')) if len(market) > 7 else '0 ETH',
                            'status': 'resolved' if len(market) > 5 and market[5] else 'active',
                            'bets_placed': 0,
                            'oracle_eligible': True,
                            'created_at': datetime.now(),
                            'submissions': []
                        }
            except Exception as e:
                logger.debug(f"Could not fetch market {market_id} from blockchain: {e}")
        
        # If no data found, show error
        if not market_data:
            flash('Market not found on blockchain', 'error')
            return redirect(url_for('clockchain.clockchain_view'))
        
        return render_template('clockchain/market_detail.html', market=market_data)
    except Exception as e:
        logger.error(f"Error loading market detail: {e}")
        flash('Error loading market details', 'error')
        return redirect(url_for('clockchain.clockchain_view'))


@clockchain_bp.route('/clockchain/submission/<submission_id>')
def submission_detail(submission_id):
    """Display detailed view of a submission - Phase 7 Blockchain-Only"""
    try:
        # Phase 7: Redirect to clockchain view with message
        flash('Submission details are now available directly on the blockchain. Use Web3 interface to view.', 'info')
        return redirect(url_for('clockchain.clockchain_view'))
        
    except Exception as e:
        logger.error(f"Error loading submission detail: {e}")
        flash('Error loading submission details', 'error')
        return redirect(url_for('clockchain.clockchain_view'))


@clockchain_bp.route('/clockchain/resolved')
def resolved_view():
    """Display resolved prediction markets - Phase 7 Blockchain-Only"""
    try:
        # Get current Pacific time
        time_status = time_sync_service.get_time_health_status()
        
        # Calculate time range
        current_time = datetime.utcnow()
        current_time_ms = int(current_time.timestamp() * 1000)
        
        # Initialize timeline segments for resolved markets
        resolved_segments = []
        
        # Try to get resolved markets from blockchain
        try:
            if hasattr(blockchain_service, 'contracts') and blockchain_service.contracts.get('EnhancedPredictionMarket'):
                # Try to get all markets
                for market_id in range(0, 100):  # Check first 100 market IDs
                    try:
                        if blockchain_service.contracts:
                            market = blockchain_service.contracts['EnhancedPredictionMarket'].functions.markets(market_id).call()
                            
                            # Only process resolved markets
                            if market and len(market) > 5 and market[5]:  # isResolved = true
                                # Convert market data to timeline segment
                                segment = {
                                    'id': str(market_id),
                                    'actor': {
                                        'id': market_id,
                                        'x_username': market[2] if len(market) > 2 and market[2] else 'Unknown',
                                        'display_name': market[2] if len(market) > 2 and market[2] else 'Unknown Actor',
                                        'verified': False,
                                        'follower_count': 0,
                                        'is_test_account': False
                                    },
                                    'start_time': datetime.fromtimestamp(market[3]) if len(market) > 3 else datetime.now(),
                                    'end_time': datetime.fromtimestamp(market[4]) if len(market) > 4 else datetime.now(),
                                    'start_ms': market[3] * 1000 if len(market) > 3 else 0,
                                    'end_ms': market[4] * 1000 if len(market) > 4 else 0,
                                    'status': 'resolved',
                                    'submission_count': len(market[6]) if len(market) > 6 and market[6] else 0,
                                    'total_volume': str(Web3.from_wei(market[7], 'ether')) if len(market) > 7 and market[7] else '0',
                                    'currency': 'ETH',
                                    'predicted_text': market[1] if len(market) > 1 else '',
                                    'creator_wallet': market[0][:10] + '...' if len(market) > 0 and market[0] else '0x...',
                                    'initial_stake': '0.01',
                                    'stake_count': 1,
                                    'oracle_allowed': True,
                                    'time_until_oracle': 0,
                                    'submissions': [],
                                    'competing_bets': []
                                }
                                resolved_segments.append(segment)
                    except Exception as e:
                        logger.debug(f"Error fetching market {market_id}: {e}")
                        continue
        except Exception as e:
            logger.error(f"Error fetching resolved markets from blockchain: {e}")
        
        # Sort by end time (most recent first)
        resolved_segments.sort(key=lambda x: x['end_ms'], reverse=True)
        
        return render_template('clockchain/timeline.html',
                             time_status=time_status,
                             timeline_segments=resolved_segments,
                             current_page=1,
                             has_more_pages=False,
                             current_time_ms=current_time_ms,
                             active_bet_count=0,
                             total_bet_volume='0',
                             total_count=len(resolved_segments),
                             displayed_count=len(resolved_segments),
                             view_type='resolved')
                             
    except Exception as e:
        logger.error(f"Error loading resolved view: {e}")
        flash('Error loading resolved markets', 'error')
        return redirect(url_for('clockchain.clockchain_view'))
        
    except Exception as e:
        logger.error(f"Error loading resolved view: {e}")
        flash('Error loading resolved markets', 'error')
        return redirect(url_for('clockchain.clockchain_view'))


@clockchain_bp.route('/clockchain/active')
def active_view():
    """Display active prediction markets - Phase 7 Blockchain-Only"""
    try:
        # Phase 7: Redirect to clockchain view with message
        flash('Active markets are now available directly on the blockchain. Use Web3 interface to view.', 'info')
        return redirect(url_for('clockchain.clockchain_view'))
        
    except Exception as e:
        logger.error(f"Error loading active view: {e}")
        flash('Error loading active markets', 'error')
        return redirect(url_for('clockchain.clockchain_view'))
