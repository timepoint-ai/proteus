"""Routes for actors pages - Phase 7 Blockchain-Only"""
import logging
from flask import Blueprint, render_template, flash, redirect, url_for
from datetime import datetime

logger = logging.getLogger(__name__)
actors_bp = Blueprint('actors', __name__)


@actors_bp.route('/actors')
def actors_list():
    """Display list of all actors - Phase 7 Blockchain-Only"""
    try:
        # Phase 7: All actor data is now on blockchain
        # Redirect to blockchain interface with message
        flash('Actor data is now available directly on the blockchain through the ActorRegistry contract. Use Web3 interface to view.', 'info')
        
        # Return empty template with blockchain message
        blockchain_message = {
            'title': 'Actors on Blockchain',
            'message': 'All actor data is now stored on the BASE Sepolia blockchain.',
            'contract': 'ActorRegistry',
            'address': '0xC71CC19C5573C5E1E144829800cD0005D0eDB723',
            'info': 'Use the Web3 interface or blockchain explorer to view actor information.'
        }
        
        return render_template('actors/list.html', 
                             actor_stats=[],
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