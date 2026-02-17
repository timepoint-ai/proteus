from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
import json
import logging
import asyncio
import os
from datetime import datetime, timedelta, timezone
from services.time_sync import TimeSyncService
from services.blockchain_base import BaseBlockchainService
from services.v2_resolution import get_resolution_service
from utils.api_errors import (
    error_response, success_response, validation_error, not_found,
    unauthorized, internal_error, blockchain_error, ErrorCode
)
from web3 import Web3

logger = logging.getLogger(__name__)
proteus_bp = Blueprint('proteus', __name__)
time_sync_service = TimeSyncService()

# Initialize blockchain service
blockchain_service = BaseBlockchainService()

@proteus_bp.route('/proteus')
def proteus_view():
    """Display the Proteus timeline view - PredictionMarketV2"""
    try:
        # Get current Pacific time
        time_status = time_sync_service.get_time_health_status()

        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = 10  # Show 10 items per page

        # Calculate time range
        current_time = datetime.now(timezone.utc)
        current_time_ms = int(current_time.timestamp() * 1000)

        # Initialize timeline segments - V2: All data from PredictionMarketV2
        timeline_segments = []

        # Try to get actual markets from PredictionMarketV2
        try:
            market_count = blockchain_service.get_v2_market_count()
            logger.info(f"Found {market_count} markets on PredictionMarketV2 contract")

            # Limit to 20 markets to avoid excessive blockchain calls
            for market_id in range(0, min(market_count, 20)):
                try:
                    market = blockchain_service.get_v2_market(market_id)

                    if market:
                        # Get submission count for this market
                        submission_ids = blockchain_service.get_v2_market_submissions(market_id)

                        # V2 market structure: actor_handle, end_time, total_pool, resolved, winning_submission_id, creator
                        segment = {
                            'id': str(market_id),
                            'actor': {
                                'id': market_id,
                                'x_username': market.get('actor_handle', 'Unknown'),
                                'display_name': f"@{market.get('actor_handle', 'Unknown')}",
                                'verified': False,
                                'follower_count': 0,
                                'is_test_account': False
                            },
                            'start_time': None,  # V2 doesn't have start_time
                            'end_time': datetime.fromtimestamp(market['end_time']) if market.get('end_time') else datetime.now(),
                            'start_ms': 0,  # V2 doesn't have start_time
                            'end_ms': market.get('end_time', 0) * 1000,
                            'status': 'resolved' if market.get('resolved') else 'active',
                            'submission_count': len(submission_ids),
                            'total_volume': str(market.get('total_pool', 0)),
                            'currency': 'ETH',
                            'predicted_text': f"Predict @{market.get('actor_handle', 'Unknown')}'s next post",
                            'creator_wallet': market.get('creator', '0x')[:10] + '...',
                            'initial_stake': '0',  # V2: market creation is free
                            'stake_count': len(submission_ids),
                            'oracle_allowed': market.get('end_time', 0) < int(current_time.timestamp()),
                            'time_until_oracle': max(0, market.get('end_time', 0) - int(current_time.timestamp())),
                            'submissions': [],
                            'competing_bets': [],
                            'target_tweet_id': '',  # V2 doesn't have this
                            'xcom_only': True  # V2 is always X.com only
                        }
                        timeline_segments.append(segment)
                except Exception as e:
                    logger.debug(f"Error fetching market {market_id}: {e}")
                    continue
        except Exception as e:
            logger.error(f"Error fetching markets from blockchain: {e}")

        # If no markets found, just keep the list empty
        # V2: Only show real blockchain data, no placeholders

        # Blockchain stats
        active_market_count = sum(1 for s in timeline_segments if s['status'] == 'active')
        total_bet_volume = sum(float(s['total_volume']) for s in timeline_segments)
        total_count = len(timeline_segments)
        has_more_pages = False

        return render_template('proteus/timeline.html',
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
        logger.error(f"Error loading proteus view: {e}")
        return render_template('proteus/timeline.html',
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

@proteus_bp.route('/api/proteus/events')
def get_proteus_events():
    """Get proteus events for a specific time range - V2 Blockchain-Only"""
    try:
        # Get time range from query params
        start_ms = request.args.get('start_ms', type=int)
        end_ms = request.args.get('end_ms', type=int)

        if not start_ms or not end_ms:
            return validation_error('start_ms and end_ms parameters required')

        # V2: Return empty events for now (all data on blockchain)
        events = []

        return jsonify({
            'events': events,
            'count': len(events),
            'message': 'V2: All data on blockchain. Use Web3 interface or blockchain API endpoints.'
        })

    except Exception as e:
        logger.error(f"Error getting proteus events: {e}")
        return internal_error('Failed to get events')

@proteus_bp.route('/proteus/markets/create')
@proteus_bp.route('/proteus/create')
def create_market():
    """Display market creation form"""
    return render_template('markets/create.html')

@proteus_bp.route('/proteus/market/<market_id>')
@proteus_bp.route('/proteus/market/blockchain-message')
def market_detail(market_id='blockchain-message'):
    """Display detailed view of a prediction market - PredictionMarketV2"""
    try:
        # V2: Only show real blockchain data
        market_data = None

        # Try to fetch from PredictionMarketV2 contract
        try:
            market = blockchain_service.get_v2_market(int(market_id))

            if market:
                # Get submissions for this market
                submission_ids = blockchain_service.get_v2_market_submissions(int(market_id))
                submissions = []
                for sub_id in submission_ids:
                    sub = blockchain_service.get_v2_submission(sub_id)
                    if sub:
                        # V2 submission: market_id, submitter, predicted_text, amount, claimed
                        submissions.append({
                            'id': sub_id,
                            'submitter': sub.get('submitter', '0x'),
                            'predicted_text': sub.get('predicted_text', ''),
                            'amount': sub.get('amount', 0),
                            'claimed': sub.get('claimed', False),
                            'is_winner': market.get('resolved') and market.get('winning_submission_id') == sub_id
                        })

                # V2 market fields
                end_time = datetime.fromtimestamp(market['end_time']) if market.get('end_time') else None
                actor_handle = market.get('actor_handle', 'Unknown')

                market_data = {
                    'id': market_id,
                    'creator': market.get('creator', 'Not found'),
                    'predicted_text': f"Predict @{actor_handle}'s next post",
                    'actor': actor_handle,
                    'actor_handle': actor_handle,
                    'target_tweet_id': '',  # V2 doesn't use this
                    'xcom_only': True,  # V2 is always X.com focused
                    'time_range': f"Ends: {end_time.strftime('%Y-%m-%d %H:%M')}" if end_time else 'From blockchain',
                    'start_time': None,  # V2 doesn't have start_time
                    'end_time': end_time,
                    'initial_stake': 'Free',  # V2: market creation is free
                    'total_volume': f"{market.get('total_pool', 0)} ETH",
                    'total_pool': market.get('total_pool', 0),
                    'platform_fee_collected': '7% on payout',  # V2 collects fees on claim
                    'status': 'resolved' if market.get('resolved') else 'active',
                    'resolved': market.get('resolved', False),
                    'winning_submission_id': market.get('winning_submission_id'),
                    'bets_placed': len(submissions),
                    'oracle_eligible': end_time and end_time < datetime.now() if end_time else False,
                    'created_at': None,  # V2 doesn't store creation time
                    'submissions': submissions
                }
        except Exception as e:
            logger.debug(f"Could not fetch market {market_id} from blockchain: {e}")

        # If no data found, show error
        if not market_data:
            flash('Market not found on blockchain', 'error')
            return redirect(url_for('proteus.proteus_view'))

        return render_template('proteus/market_detail.html', market=market_data)
    except Exception as e:
        logger.error(f"Error loading market detail: {e}")
        flash('Error loading market details', 'error')
        return redirect(url_for('proteus.proteus_view'))


@proteus_bp.route('/proteus/submission/<submission_id>')
def submission_detail(submission_id):
    """Display detailed view of a submission - V2 Blockchain-Only"""
    try:
        # V2: Redirect to proteus view with message
        flash('Submission details are now available directly on the blockchain. Use Web3 interface to view.', 'info')
        return redirect(url_for('proteus.proteus_view'))

    except Exception as e:
        logger.error(f"Error loading submission detail: {e}")
        flash('Error loading submission details', 'error')
        return redirect(url_for('proteus.proteus_view'))


@proteus_bp.route('/proteus/resolved')
def resolved_view():
    """Display resolved prediction markets - PredictionMarketV2"""
    try:
        # Get current Pacific time
        time_status = time_sync_service.get_time_health_status()

        # Calculate time range
        current_time = datetime.now(timezone.utc)
        current_time_ms = int(current_time.timestamp() * 1000)

        # Initialize timeline segments for resolved markets
        resolved_segments = []

        # Try to get resolved markets from PredictionMarketV2
        try:
            market_count = blockchain_service.get_v2_market_count()

            for market_id in range(0, min(market_count, 20)):
                try:
                    market = blockchain_service.get_v2_market(market_id)

                    # Only process resolved markets
                    if market and market.get('resolved'):
                        submission_ids = blockchain_service.get_v2_market_submissions(market_id)
                        actor_handle = market.get('actor_handle', 'Unknown')

                        segment = {
                            'id': str(market_id),
                            'actor': {
                                'id': market_id,
                                'x_username': actor_handle,
                                'display_name': f"@{actor_handle}",
                                'verified': False,
                                'follower_count': 0,
                                'is_test_account': False
                            },
                            'start_time': None,
                            'end_time': datetime.fromtimestamp(market['end_time']) if market.get('end_time') else datetime.now(),
                            'start_ms': 0,
                            'end_ms': market.get('end_time', 0) * 1000,
                            'status': 'resolved',
                            'submission_count': len(submission_ids),
                            'total_volume': str(market.get('total_pool', 0)),
                            'currency': 'ETH',
                            'predicted_text': f"Predict @{actor_handle}'s next post",
                            'creator_wallet': market.get('creator', '0x')[:10] + '...',
                            'initial_stake': '0',
                            'stake_count': len(submission_ids),
                            'oracle_allowed': True,
                            'time_until_oracle': 0,
                            'submissions': [],
                            'competing_bets': [],
                            'winning_submission_id': market.get('winning_submission_id')
                        }
                        resolved_segments.append(segment)
                except Exception as e:
                    logger.debug(f"Error fetching market {market_id}: {e}")
                    continue
        except Exception as e:
            logger.error(f"Error fetching resolved markets from blockchain: {e}")

        # Sort by end time (most recent first)
        resolved_segments.sort(key=lambda x: x['end_ms'], reverse=True)

        return render_template('proteus/timeline.html',
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
        return redirect(url_for('proteus.proteus_view'))


@proteus_bp.route('/proteus/active')
def active_view():
    """Display active prediction markets - PredictionMarketV2"""
    try:
        # Get current Pacific time
        time_status = time_sync_service.get_time_health_status()

        # Calculate time range
        current_time = datetime.now(timezone.utc)
        current_time_ms = int(current_time.timestamp() * 1000)

        # Initialize timeline segments for active markets
        active_segments = []

        # Try to get active markets from PredictionMarketV2
        try:
            market_count = blockchain_service.get_v2_market_count()

            for market_id in range(0, min(market_count, 20)):
                try:
                    market = blockchain_service.get_v2_market(market_id)

                    # Only process active markets (not resolved and end time in future)
                    if market and not market.get('resolved'):
                        end_time = market.get('end_time', 0)
                        if end_time > int(current_time.timestamp()):
                            submission_ids = blockchain_service.get_v2_market_submissions(market_id)
                            actor_handle = market.get('actor_handle', 'Unknown')

                            segment = {
                                'id': str(market_id),
                                'actor': {
                                    'id': market_id,
                                    'x_username': actor_handle,
                                    'display_name': f"@{actor_handle}",
                                    'verified': False,
                                    'follower_count': 0,
                                    'is_test_account': False
                                },
                                'start_time': None,
                                'end_time': datetime.fromtimestamp(end_time),
                                'start_ms': 0,
                                'end_ms': end_time * 1000,
                                'status': 'active',
                                'submission_count': len(submission_ids),
                                'total_volume': str(market.get('total_pool', 0)),
                                'currency': 'ETH',
                                'predicted_text': f"Predict @{actor_handle}'s next post",
                                'creator_wallet': market.get('creator', '0x')[:10] + '...',
                                'initial_stake': '0',
                                'stake_count': len(submission_ids),
                                'oracle_allowed': False,
                                'time_until_oracle': end_time - int(current_time.timestamp()),
                                'submissions': [],
                                'competing_bets': []
                            }
                            active_segments.append(segment)
                except Exception as e:
                    logger.debug(f"Error fetching market {market_id}: {e}")
                    continue
        except Exception as e:
            logger.error(f"Error fetching active markets from blockchain: {e}")

        # Sort by end time (soonest first)
        active_segments.sort(key=lambda x: x['end_ms'])

        total_volume = sum(float(s['total_volume']) for s in active_segments)

        return render_template('proteus/timeline.html',
                             time_status=time_status,
                             timeline_segments=active_segments,
                             current_page=1,
                             has_more_pages=False,
                             current_time_ms=current_time_ms,
                             active_bet_count=len(active_segments),
                             total_bet_volume=str(total_volume),
                             total_count=len(active_segments),
                             displayed_count=len(active_segments),
                             view_type='active')

    except Exception as e:
        logger.error(f"Error loading active view: {e}")
        flash('Error loading active markets', 'error')
        return redirect(url_for('proteus.proteus_view'))


# API endpoint to serve contract ABI
@proteus_bp.route('/api/contract-abi/<contract_name>')
def get_contract_abi(contract_name):
    """Serve contract ABI for frontend use"""
    try:
        import os
        abi_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'abi', f'{contract_name}.json')

        if os.path.exists(abi_path):
            with open(abi_path, 'r') as f:
                abi = json.load(f)
            return jsonify(abi)
        else:
            return not_found('ABI', contract_name)

    except Exception as e:
        logger.error(f"Error loading ABI for {contract_name}: {e}")
        return internal_error('Failed to load ABI')


# ====================================================================
# ADMIN RESOLUTION ENDPOINTS (V2)
# ====================================================================
# These endpoints allow admins to resolve markets and manage platform fees.
# Security: Requires ADMIN_API_KEY in header for sensitive operations.
# ====================================================================

def verify_admin_key():
    """Verify admin API key from request headers"""
    admin_key = os.environ.get('ADMIN_API_KEY')
    if not admin_key:
        # If no admin key configured, allow access (dev mode)
        return True
    provided_key = request.headers.get('X-Admin-Key')
    return provided_key == admin_key


@proteus_bp.route('/api/admin/resolution-stats')
def get_resolution_stats():
    """Get overall resolution statistics"""
    try:
        resolution_service = get_resolution_service()
        stats = resolution_service.get_resolution_stats()
        return success_response(stats)
    except Exception as e:
        logger.error(f"Error getting resolution stats: {e}")
        return blockchain_error(f'Failed to get resolution stats: {str(e)}')


@proteus_bp.route('/api/admin/pending-markets')
def get_pending_markets():
    """Get markets pending resolution"""
    try:
        resolution_service = get_resolution_service()
        pending = resolution_service.get_pending_markets()
        return success_response({
            'pending_markets': pending,
            'count': len(pending)
        })
    except Exception as e:
        logger.error(f"Error getting pending markets: {e}")
        return blockchain_error(f'Failed to get pending markets: {str(e)}')


@proteus_bp.route('/api/admin/market/<int:market_id>/details')
def get_market_resolution_details(market_id):
    """Get detailed market info for resolution"""
    try:
        resolution_service = get_resolution_service()
        market = resolution_service.get_market_for_resolution(market_id)
        if not market:
            return not_found('Market', market_id)
        return success_response(market)
    except Exception as e:
        logger.error(f"Error getting market details: {e}")
        return blockchain_error(f'Failed to get market details: {str(e)}')


@proteus_bp.route('/api/admin/resolve-market/<int:market_id>', methods=['POST'])
def resolve_market(market_id):
    """Resolve a market with actual tweet text

    Request body:
    {
        "actual_text": "The exact tweet text",
        "tweet_url": "Optional: https://x.com/user/status/123..."
    }

    If tweet_url is provided and actual_text is empty, will attempt to fetch tweet.
    """
    if not verify_admin_key():
        return unauthorized('Invalid admin key')

    try:
        data = request.get_json() or {}
        actual_text = data.get('actual_text', '').strip()
        tweet_url = data.get('tweet_url', '').strip()

        resolution_service = get_resolution_service()

        # If no actual text but tweet URL provided, fetch it
        if not actual_text and tweet_url:
            # Get market to find actor handle
            market = resolution_service.get_market_for_resolution(market_id)
            if not market:
                return not_found('Market', market_id)

            # Run async tweet fetch
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                tweet_data = loop.run_until_complete(
                    resolution_service.fetch_actual_tweet(market['actor_handle'], tweet_url)
                )
                if tweet_data:
                    actual_text = tweet_data.get('text', '')
                else:
                    return error_response(ErrorCode.INVALID_REQUEST, 'Could not fetch tweet from URL', 400)
            finally:
                loop.close()

        if not actual_text:
            return validation_error('actual_text is required (or provide tweet_url)', 'actual_text')

        # Resolve the market
        result = resolution_service.resolve_market(market_id, actual_text)

        if result['success']:
            return success_response({
                'market_id': market_id,
                'tx_hash': result['tx_hash'],
                'gas_used': result.get('gas_used'),
                'block_number': result.get('block_number'),
                'actual_text': actual_text
            })
        else:
            # If we have unsigned_tx, it's a partial success (key not configured)
            if result.get('unsigned_tx'):
                return success_response({
                    'market_id': market_id,
                    'unsigned_tx': result.get('unsigned_tx'),
                    'message': 'Owner key not configured. Sign transaction manually.'
                })
            return error_response(ErrorCode.CONTRACT_ERROR, result.get('error', 'Resolution failed'), 400)

    except Exception as e:
        logger.error(f"Error resolving market {market_id}: {e}")
        return blockchain_error(f'Failed to resolve market: {str(e)}')


@proteus_bp.route('/api/admin/auto-resolve-market/<int:market_id>', methods=['POST'])
def auto_resolve_market(market_id):
    """Auto-resolve market by fetching tweet from URL

    Request body:
    {
        "tweet_url": "https://x.com/user/status/123..."
    }
    """
    if not verify_admin_key():
        return unauthorized('Invalid admin key')

    try:
        data = request.get_json() or {}
        tweet_url = data.get('tweet_url', '').strip()

        if not tweet_url:
            return validation_error('tweet_url is required', 'tweet_url')

        resolution_service = get_resolution_service()

        # Run async auto-resolution
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                resolution_service.auto_resolve_market(market_id, tweet_url)
            )
        finally:
            loop.close()

        if result['success']:
            return success_response({
                'market_id': market_id,
                'tx_hash': result['tx_hash'],
                'tweet_text': result.get('tweet_text'),
                'gas_used': result.get('gas_used')
            })
        else:
            return error_response(ErrorCode.CONTRACT_ERROR, result.get('error', 'Auto-resolution failed'), 400)

    except Exception as e:
        logger.error(f"Error auto-resolving market {market_id}: {e}")
        return blockchain_error(f'Failed to auto-resolve market: {str(e)}')


@proteus_bp.route('/api/admin/withdraw-fees', methods=['POST'])
def withdraw_platform_fees():
    """Withdraw accumulated platform fees (owner only)"""
    if not verify_admin_key():
        return unauthorized('Invalid admin key')

    try:
        resolution_service = get_resolution_service()
        result = resolution_service.withdraw_fees()

        if result['success']:
            return success_response({
                'tx_hash': result['tx_hash'],
                'amount': result['amount']
            })
        else:
            return error_response(ErrorCode.CONTRACT_ERROR, result.get('error', 'Fee withdrawal failed'), 400)

    except Exception as e:
        logger.error(f"Error withdrawing fees: {e}")
        return blockchain_error(f'Failed to withdraw fees: {str(e)}')


@proteus_bp.route('/proteus/admin/resolution')
def resolution_dashboard():
    """Admin dashboard for market resolution"""
    try:
        resolution_service = get_resolution_service()
        stats = resolution_service.get_resolution_stats()
        pending = resolution_service.get_pending_markets()

        return render_template('proteus/admin_resolution.html',
                             stats=stats,
                             pending_markets=pending)
    except Exception as e:
        logger.error(f"Error loading resolution dashboard: {e}")
        flash('Error loading resolution dashboard', 'error')
        return redirect(url_for('proteus.proteus_view'))
