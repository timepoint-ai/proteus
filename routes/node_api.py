"""
Node API endpoints for multi-node communication
"""

from flask import Blueprint, request, jsonify
import logging
from datetime import datetime, timezone
# from models import db, NodeOperator  # Phase 7: Models removed

logger = logging.getLogger(__name__)

node_api_bp = Blueprint('node_api', __name__, url_prefix='/api')

@node_api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for nodes"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'service': 'clockchain_node'
    })

@node_api_bp.route('/nodes/<address>', methods=['GET'])
def get_node_status(address):
    """Get node registration status"""
    try:
        node = NodeOperator.query.filter_by(node_address=address.lower()).first()
        if node:
            return jsonify({
                'is_registered': True,
                'is_active': node.status == 'active',
                'operator_id': node.operator_id,
                'created_at': node.created_at.isoformat()
            })
        else:
            return jsonify({
                'is_registered': False,
                'is_active': False
            })
    except Exception as e:
        logger.error(f"Error checking node status: {e}")
        return jsonify({'error': str(e)}), 500

@node_api_bp.route('/nodes/register', methods=['POST'])
def register_node():
    """Register a new node"""
    try:
        data = request.get_json()
        
        address = data.get('address', '').lower()
        name = data.get('name', 'Unnamed Node')
        node_id = data.get('node_id')
        endpoint = data.get('endpoint')
        
        if not address:
            return jsonify({'error': 'Address required'}), 400
            
        # Check if node already exists
        existing = NodeOperator.query.filter_by(node_address=address).first()
        if existing:
            return jsonify({
                'message': 'Node already registered',
                'node_id': str(existing.id)
            })
            
        # Generate a dummy public key for now (in production, would be provided)
        import secrets
        public_key = secrets.token_hex(32)
        
        # Create new node
        node = NodeOperator()
        node.operator_id = node_id or f"operator_{address[:8]}"
        node.public_key = public_key
        node.node_address = endpoint or f"http://{node_id}:5000"
        node.status = 'pending'  # Needs consensus to activate
        
        db.session.add(node)
        db.session.commit()
        
        logger.info(f"New node registered: {address} ({name})")
        
        return jsonify({
            'message': 'Node registered successfully',
            'node_id': str(node.id),
            'requires_consensus': True
        })
        
    except Exception as e:
        logger.error(f"Error registering node: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@node_api_bp.route('/nodes/heartbeat', methods=['POST'])
def node_heartbeat():
    """Receive heartbeat from node"""
    try:
        data = request.get_json()
        
        node_id = data.get('node_id')
        address = data.get('address', '').lower()
        timestamp = data.get('timestamp')
        metrics = data.get('metrics', {})
        
        if not address:
            return jsonify({'error': 'Address required'}), 400
            
        # Update node last seen
        node = NodeOperator.query.filter_by(node_address=address).first()
        if not node:
            return jsonify({'error': 'Node not registered'}), 404
            
        # Update node metrics (in a real implementation, would store these)
        node.last_seen = datetime.now(timezone.utc)
        db.session.commit()
        
        return jsonify({
            'status': 'acknowledged',
            'node_active': node.status == 'active'
        })
        
    except Exception as e:
        logger.error(f"Error processing heartbeat: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@node_api_bp.route('/nodes', methods=['GET'])
def list_nodes():
    """List all registered nodes"""
    try:
        nodes = NodeOperator.query.all()
        return jsonify({
            'nodes': [
                {
                    'id': str(node.id),
                    'operator_id': node.operator_id,
                    'node_address': node.node_address,
                    'is_active': node.status == 'active',
                    'status': node.status,
                    'last_seen': node.last_seen.isoformat() if node.last_seen else None,
                    'created_at': node.created_at.isoformat()
                }
                for node in nodes
            ],
            'total': len(nodes)
        })
    except Exception as e:
        logger.error(f"Error listing nodes: {e}")
        return jsonify({'error': str(e)}), 500