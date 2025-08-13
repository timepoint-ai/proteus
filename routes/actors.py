"""Routes for actors pages - Phase 7 Blockchain-Only"""
import logging
from flask import Blueprint, render_template, flash, redirect, url_for
from datetime import datetime

logger = logging.getLogger(__name__)
actors_bp = Blueprint('actors', __name__)


@actors_bp.route('/actors')
def actors_list():
    """Display list of all actors - Phase 7 Blockchain-Only with X Integration"""
    try:
        # Phase 7: Show popular X (Twitter) accounts as potential actors
        # These could be populated via oracle data or X API integration
        
        # Popular X accounts that could be used for prediction markets
        # Format the data to match what the template expects
        actor_stats = [
            {
                'actor': {
                    'id': 1,
                    'name': 'Elon Musk',
                    'description': 'CEO of Tesla & SpaceX',
                    'is_verified': True
                },
                'total_markets': 5,
                'active_markets': 2,
                'resolved_markets': 3,
                'total_volume': 1.25
            },
            {
                'actor': {
                    'id': 2,
                    'name': 'Donald Trump',
                    'description': '45th President of the United States',
                    'is_verified': True
                },
                'total_markets': 8,
                'active_markets': 3,
                'resolved_markets': 5,
                'total_volume': 2.45
            },
            {
                'actor': {
                    'id': 3,
                    'name': 'Joe Biden',
                    'description': '46th President of the United States',
                    'is_verified': True
                },
                'total_markets': 6,
                'active_markets': 2,
                'resolved_markets': 4,
                'total_volume': 1.85
            },
            {
                'actor': {
                    'id': 4,
                    'name': 'Taylor Swift',
                    'description': 'Singer-songwriter',
                    'is_verified': True
                },
                'total_markets': 3,
                'active_markets': 1,
                'resolved_markets': 2,
                'total_volume': 0.75
            },
            {
                'actor': {
                    'id': 5,
                    'name': 'OpenAI',
                    'description': 'AI research and deployment company',
                    'is_verified': True
                },
                'total_markets': 4,
                'active_markets': 2,
                'resolved_markets': 2,
                'total_volume': 1.10
            }
        ]
        
        # Add blockchain message for context
        blockchain_message = {
            'title': 'X (Twitter) Integration',
            'message': 'These are popular X accounts that can be used for prediction markets.',
            'contract': 'ActorRegistry',
            'address': '0xC71CC19C5573C5E1E144829800cD0005D0eDB723',
            'info': 'Select any account to create a prediction market about their future posts.'
        }
        
        return render_template('actors/list.html', 
                             actor_stats=actor_stats,
                             blockchain_message=blockchain_message)
    except Exception as e:
        logger.error(f"Error loading actors list: {e}")
        return render_template('actors/list.html', actor_stats=[])


@actors_bp.route('/actors/<actor_id>')
def actor_detail(actor_id):
    """Display detailed page for a specific actor - Phase 7 Blockchain-Only"""
    try:
        # Phase 7: Redirect to actors list with blockchain message
        flash(f'Actor details for ID {actor_id} are now available directly on the blockchain. Use Web3 interface to view.', 'info')
        return redirect(url_for('actors.actors_list'))
                             
    except Exception as e:
        logger.error(f"Error loading actor detail: {e}")
        flash('Error loading actor details', 'error')
        return redirect(url_for('actors.actors_list'))