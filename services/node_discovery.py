"""
Node Discovery Service for P2P Network
Implements DHT-based peer discovery and management
"""

import asyncio
import json
import logging
import socket
import time
from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta
import websockets
from threading import Thread, Lock

from config import Config
# from models import NodeOperator, db  # Phase 7: Models removed
from utils.crypto import CryptoUtils

logger = logging.getLogger(__name__)


class NodeDiscovery:
    """P2P node discovery using DHT-like mechanism"""
    
    def __init__(self):
        self.crypto_utils = CryptoUtils()
        self.known_nodes: Set[str] = set(Config.KNOWN_NODES)
        self.active_peers: Dict[str, Dict] = {}
        self.bootstrap_nodes = [
            "ws://clockchain-seed1.base.org:8545",
            "ws://clockchain-seed2.base.org:8545", 
            "ws://clockchain-seed3.base.org:8545"
        ]
        self.dht: Dict[str, List[str]] = {}  # Simplified DHT
        self.node_id = Config.NODE_OPERATOR_ID
        self.endpoint = Config.NODE_ENDPOINT
        self.running = False
        self.lock = Lock()
        
        # Node health tracking
        self.ping_interval = 30  # seconds
        self.timeout_threshold = 90  # seconds
        self.last_ping_times: Dict[str, float] = {}
        
    async def start_discovery(self):
        """Start the node discovery service"""
        try:
            self.running = True
            logger.info("Starting node discovery service")
            
            # Start WebSocket server for incoming connections
            asyncio.create_task(self._start_discovery_server())
            
            # Connect to bootstrap nodes
            await self._connect_to_bootstrap_nodes()
            
            # Start periodic tasks
            asyncio.create_task(self._periodic_peer_discovery())
            asyncio.create_task(self._periodic_health_check())
            
            logger.info(f"Node discovery started with ID: {self.node_id}")
            
        except Exception as e:
            logger.error(f"Error starting node discovery: {e}")
            
    async def stop_discovery(self):
        """Stop the node discovery service"""
        self.running = False
        logger.info("Node discovery service stopped")
        
    async def _start_discovery_server(self):
        """Start WebSocket server for peer connections"""
        try:
            async def handle_peer(websocket, path):
                peer_id = None
                try:
                    # Handshake
                    handshake_data = await websocket.recv()
                    handshake = json.loads(handshake_data)
                    
    # if handshake.get('type') == 'handshake':  # Phase 7: Database removed
    # peer_id = handshake.get('node_id')  # Phase 7: Database removed
    # peer_endpoint = handshake.get('endpoint')  # Phase 7: Database removed
                        
                        # Verify signature
                        if self._verify_peer_signature(handshake):
                            # Add to active peers
                            with self.lock:
                                self.active_peers[peer_id] = {
                                    'endpoint': peer_endpoint,
                                    'websocket': websocket,
                                    'connected_at': time.time(),
                                    'last_seen': time.time()
                                }
                            
                            # Send acknowledgment
                            ack = {
                                'type': 'handshake_ack',
                                'node_id': self.node_id,
                                'endpoint': self.endpoint,
                                'peers': list(self.active_peers.keys())
                            }
                            await websocket.send(json.dumps(ack))
                            
                            logger.info(f"New peer connected: {peer_id}")
                            
                            # Handle messages from peer
                            await self._handle_peer_messages(websocket, peer_id)
                            
                except Exception as e:
                    logger.error(f"Error handling peer {peer_id}: {e}")
                finally:
                    if peer_id and peer_id in self.active_peers:
                        with self.lock:
                            del self.active_peers[peer_id]
                        logger.info(f"Peer disconnected: {peer_id}")
                        
            # Start server
            server = await websockets.serve(
                handle_peer, 
                "0.0.0.0", 
                Config.P2P_PORT
            )
            logger.info(f"Discovery server listening on port {Config.P2P_PORT}")
            
            # Keep server running
            await asyncio.Future()  # Run forever
            
        except Exception as e:
            logger.error(f"Error in discovery server: {e}")
            
    async def _connect_to_bootstrap_nodes(self):
        """Connect to bootstrap nodes for initial peer discovery"""
        for bootstrap in self.bootstrap_nodes:
            try:
                if bootstrap not in self.known_nodes:
                    await self._connect_to_peer(bootstrap)
            except Exception as e:
                logger.warning(f"Could not connect to bootstrap node {bootstrap}: {e}")
                
    async def _connect_to_peer(self, endpoint: str) -> Optional[websockets.WebSocketClientProtocol]:
        """Connect to a peer node"""
        try:
            websocket = await websockets.connect(endpoint)
            
            # Send handshake
            handshake = {
                'type': 'handshake',
                'node_id': self.node_id,
                'endpoint': self.endpoint,
                'timestamp': time.time()
            }
            
            # Sign handshake
            signature = self.crypto_utils.sign_message(json.dumps(handshake))
            handshake['signature'] = signature
            
            await websocket.send(json.dumps(handshake))
            
            # Wait for acknowledgment
            ack_data = await websocket.recv()
            ack = json.loads(ack_data)
            
    # if ack.get('type') == 'handshake_ack':  # Phase 7: Database removed
    # peer_id = ack.get('node_id')  # Phase 7: Database removed
    # peer_endpoint = ack.get('endpoint')  # Phase 7: Database removed
    # new_peers = ack.get('peers', [])  # Phase 7: Database removed
                
                # Add to active peers
                with self.lock:
                    self.active_peers[peer_id] = {
                        'endpoint': peer_endpoint,
                        'websocket': websocket,
                        'connected_at': time.time(),
                        'last_seen': time.time()
                    }
                    
                    # Add new peers to known nodes
                    for peer in new_peers:
                        if peer not in self.known_nodes and peer != self.node_id:
    # self.known_nodes.add(peer)  # Phase 7: Database removed
                            
                logger.info(f"Connected to peer: {peer_id}")
                
                # Handle messages in background
                asyncio.create_task(self._handle_peer_messages(websocket, peer_id))
                
                return websocket
                
        except Exception as e:
            logger.error(f"Error connecting to peer {endpoint}: {e}")
            return None
            
    async def _handle_peer_messages(self, websocket, peer_id: str):
        """Handle incoming messages from a peer"""
        try:
            while self.running:
                message_data = await websocket.recv()
                message = json.loads(message_data)
    # msg_type = message.get('type')  # Phase 7: Database removed
                
                if msg_type == 'ping':
                    # Respond to ping
                    pong = {'type': 'pong', 'timestamp': time.time()}
                    await websocket.send(json.dumps(pong))
                    
                    # Update last seen
                    with self.lock:
                        if peer_id in self.active_peers:
                            self.active_peers[peer_id]['last_seen'] = time.time()
                            
                elif msg_type == 'peer_request':
                    # Share known peers
                    peers = list(self.active_peers.keys())[:10]  # Limit to 10
                    response = {
                        'type': 'peer_response',
                        'peers': peers
                    }
                    await websocket.send(json.dumps(response))
                    
                elif msg_type == 'dht_store':
                    # Store in DHT
    # key = message.get('key')  # Phase 7: Database removed
    # value = message.get('value')  # Phase 7: Database removed
                    if key and value:
                        with self.lock:
                            if key not in self.dht:
                                self.dht[key] = []
                            self.dht[key].append(value)
                            
                elif msg_type == 'dht_lookup':
                    # Lookup in DHT
    # key = message.get('key')  # Phase 7: Database removed
    # values = self.dht.get(key, [])  # Phase 7: Database removed
                    response = {
                        'type': 'dht_response',
                        'key': key,
                        'values': values
                    }
                    await websocket.send(json.dumps(response))
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Connection closed with peer {peer_id}")
        except Exception as e:
            logger.error(f"Error handling messages from {peer_id}: {e}")
            
    async def _periodic_peer_discovery(self):
        """Periodically discover new peers"""
        while self.running:
            try:
                # Request peers from active connections
                for peer_id, peer_info in list(self.active_peers.items()):
                    try:
                        websocket = peer_info['websocket']
                        request = {'type': 'peer_request'}
                        await websocket.send(json.dumps(request))
                    except:
                        pass
                        
                # Try connecting to known but inactive nodes
                for node in list(self.known_nodes):
                    if node not in self.active_peers:
                        asyncio.create_task(self._connect_to_peer(node))
                        
                # Update database with active nodes
                await self._update_node_registry()
                
            except Exception as e:
                logger.error(f"Error in peer discovery: {e}")
                
            # Wait before next discovery round
            await asyncio.sleep(60)  # Every minute
            
    async def _periodic_health_check(self):
        """Check health of connected peers"""
        while self.running:
            try:
                # Send ping to all peers
                disconnected_peers = []
                
                for peer_id, peer_info in list(self.active_peers.items()):
                    try:
                        websocket = peer_info['websocket']
                        ping = {'type': 'ping', 'timestamp': time.time()}
                        await websocket.send(json.dumps(ping))
                        
                        # Check for timeout
    # last_seen = peer_info.get('last_seen', 0)  # Phase 7: Database removed
                        if time.time() - last_seen > self.timeout_threshold:
                            disconnected_peers.append(peer_id)
                            
                    except Exception as e:
                        logger.warning(f"Failed to ping peer {peer_id}: {e}")
                        disconnected_peers.append(peer_id)
                        
                # Remove disconnected peers
                with self.lock:
                    for peer_id in disconnected_peers:
                        if peer_id in self.active_peers:
                            del self.active_peers[peer_id]
                            logger.info(f"Removed inactive peer: {peer_id}")
                            
            except Exception as e:
                logger.error(f"Error in health check: {e}")
                
            await asyncio.sleep(self.ping_interval)
            
    async def _update_node_registry(self):
        """Update node registry in database"""
        try:
            from app import app
            
            with app.app_context():
                # Update known nodes
                for peer_id in self.active_peers:
    # node = NodeOperator.query.filter_by(operator_id=peer_id).first()  # Phase 7: Database removed
                    if node:
                        node.last_seen = datetime.utcnow()
                        node.status = 'active'
                    else:
                        # Create new node entry
                        peer_info = self.active_peers[peer_id]
                        node = NodeOperator(
                            operator_id=peer_id,
                            public_key='',  # Would be exchanged during handshake
                            node_address=peer_info['endpoint'],
                            status='active'
                        )
    # db.session.add(node)  # Phase 7: Database removed
                        
                # Mark inactive nodes
                inactive_threshold = datetime.utcnow() - timedelta(seconds=self.timeout_threshold)
    # NodeOperator.query.filter(  # Phase 7: Database removed
                    NodeOperator.last_seen < inactive_threshold,
                    NodeOperator.status == 'active'
                ).update({'status': 'inactive'})
                
    # db.session.commit()  # Phase 7: Database removed
                
        except Exception as e:
            logger.error(f"Error updating node registry: {e}")
            
    def _verify_peer_signature(self, handshake: Dict) -> bool:
        """Verify peer's handshake signature"""
        try:
            # In production, verify against peer's public key
            # For now, accept all valid JSON handshakes
            return 'node_id' in handshake and 'endpoint' in handshake
        except:
            return False
            
    async def discover_peers(self) -> List[str]:
        """Get list of active peer endpoints"""
        with self.lock:
            return [info['endpoint'] for info in self.active_peers.values()]
            
    def get_active_peer_count(self) -> int:
        """Get number of active peers"""
        return len(self.active_peers)
        
    def get_peer_info(self, peer_id: str) -> Optional[Dict]:
        """Get information about a specific peer"""
    # return self.active_peers.get(peer_id)  # Phase 7: Database removed
        
    async def broadcast_to_peers(self, message: Dict):
        """Broadcast a message to all active peers"""
        failed_peers = []
        
        for peer_id, peer_info in list(self.active_peers.items()):
            try:
                websocket = peer_info['websocket']
                await websocket.send(json.dumps(message))
            except Exception as e:
                logger.warning(f"Failed to broadcast to peer {peer_id}: {e}")
                failed_peers.append(peer_id)
                
        # Remove failed peers
        with self.lock:
            for peer_id in failed_peers:
                if peer_id in self.active_peers:
                    del self.active_peers[peer_id]