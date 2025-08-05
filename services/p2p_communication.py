"""
P2P Communication Service (Phase 12)
WebRTC-based peer-to-peer communication for decentralized node network
"""

import logging
import json
import asyncio
from typing import Optional, Dict, List, Callable
import websockets
from collections import defaultdict

logger = logging.getLogger(__name__)

class P2PCommunicationService:
    """WebRTC-based P2P communication for decentralized operations"""
    
    def __init__(self, node_id: str, signaling_server: str = "ws://localhost:8765"):
        self.node_id = node_id
        self.signaling_server = signaling_server
        self.peers = {}  # peer_id -> connection
        self.message_handlers = defaultdict(list)
        self.websocket = None
        self.running = False
        
        # WebRTC configuration
        self.rtc_configuration = {
            'iceServers': [
                {'urls': 'stun:stun.l.google.com:19302'},
                {'urls': 'stun:stun1.l.google.com:19302'}
            ]
        }
        
    async def connect(self):
        """Connect to signaling server and start P2P network"""
        try:
            self.websocket = await websockets.connect(self.signaling_server)
            self.running = True
            
            # Register node
            await self.websocket.send(json.dumps({
                'type': 'register',
                'node_id': self.node_id
            }))
            
            logger.info(f"P2P node {self.node_id} connected to signaling server")
            
            # Start message handler
            asyncio.create_task(self._handle_messages())
            
        except Exception as e:
            logger.error(f"Failed to connect to signaling server: {e}")
            raise
            
    async def _handle_messages(self):
        """Handle incoming messages from signaling server"""
        try:
            while self.running and self.websocket:
                message = await self.websocket.recv()
                data = json.loads(message)
                
                if data['type'] == 'peer_list':
                    await self._handle_peer_list(data['peers'])
                elif data['type'] == 'offer':
                    await self._handle_offer(data)
                elif data['type'] == 'answer':
                    await self._handle_answer(data)
                elif data['type'] == 'ice_candidate':
                    await self._handle_ice_candidate(data)
                elif data['type'] == 'peer_message':
                    await self._handle_peer_message(data)
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info("Connection to signaling server closed")
        except Exception as e:
            logger.error(f"Error handling messages: {e}")
        finally:
            self.running = False
            
    async def _handle_peer_list(self, peers: List[str]):
        """Handle updated peer list from signaling server"""
        logger.info(f"Received peer list: {peers}")
        
        # Connect to new peers
        for peer_id in peers:
            if peer_id != self.node_id and peer_id not in self.peers:
                asyncio.create_task(self._connect_to_peer(peer_id))
                
    async def _connect_to_peer(self, peer_id: str):
        """Initiate P2P connection to a peer"""
        try:
            # Create WebRTC offer (simplified for now)
            offer = {
                'type': 'offer',
                'from': self.node_id,
                'to': peer_id,
                'sdp': 'mock_sdp_offer'  # In real implementation, use actual WebRTC
            }
            
            if self.websocket:
                await self.websocket.send(json.dumps(offer))
                logger.info(f"Sent offer to peer {peer_id}")
            
        except Exception as e:
            logger.error(f"Error connecting to peer {peer_id}: {e}")
            
    async def _handle_offer(self, data: Dict):
        """Handle WebRTC offer from peer"""
        try:
            peer_id = data['from']
            
            # Create answer (simplified)
            answer = {
                'type': 'answer',
                'from': self.node_id,
                'to': peer_id,
                'sdp': 'mock_sdp_answer'
            }
            
            if self.websocket:
                await self.websocket.send(json.dumps(answer))
            
            # Mark peer as connected
            self.peers[peer_id] = {
                'status': 'connected',
                'connection_time': asyncio.get_event_loop().time()
            }
            
            logger.info(f"Connected to peer {peer_id}")
            
        except Exception as e:
            logger.error(f"Error handling offer: {e}")
            
    async def _handle_answer(self, data: Dict):
        """Handle WebRTC answer from peer"""
        peer_id = data['from']
        self.peers[peer_id] = {
            'status': 'connected',
            'connection_time': asyncio.get_event_loop().time()
        }
        logger.info(f"Peer {peer_id} accepted connection")
        
    async def _handle_ice_candidate(self, data: Dict):
        """Handle ICE candidate for WebRTC connection"""
        # In real implementation, would handle ICE candidates
        pass
        
    async def _handle_peer_message(self, data: Dict):
        """Handle message from peer"""
        peer_id = data['from']
        message_type = data['message_type']
        content = data['content']
        
        # Call registered handlers
        for handler in self.message_handlers[message_type]:
            try:
                await handler(peer_id, content)
            except Exception as e:
                logger.error(f"Error in message handler: {e}")
                
    async def broadcast_message(self, message_type: str, content: Dict):
        """Broadcast message to all connected peers"""
        message = {
            'type': 'broadcast',
            'from': self.node_id,
            'message_type': message_type,
            'content': content
        }
        
        for peer_id in self.peers:
            if self.peers[peer_id]['status'] == 'connected':
                await self.send_to_peer(peer_id, message)
                
    async def send_to_peer(self, peer_id: str, message: Dict):
        """Send message to specific peer"""
        try:
            if self.websocket:
                await self.websocket.send(json.dumps({
                    'type': 'peer_message',
                    'from': self.node_id,
                    'to': peer_id,
                    'message_type': message.get('message_type'),
                    'content': message.get('content')
                }))
                
        except Exception as e:
            logger.error(f"Error sending to peer {peer_id}: {e}")
            
    def register_handler(self, message_type: str, handler: Callable):
        """Register handler for specific message type"""
        self.message_handlers[message_type].append(handler)
        
    async def disconnect(self):
        """Disconnect from P2P network"""
        self.running = False
        
        if self.websocket:
            await self.websocket.close()
            
        logger.info(f"P2P node {self.node_id} disconnected")
        
    def get_connected_peers(self) -> List[str]:
        """Get list of connected peers"""
        return [
            peer_id for peer_id, info in self.peers.items()
            if info['status'] == 'connected'
        ]
        
    async def request_data_from_peers(self, data_type: str, params: Dict) -> List[Dict]:
        """Request data from all connected peers"""
        request_id = f"{self.node_id}_{asyncio.get_event_loop().time()}"
        responses = []
        
        # Send request to all peers
        await self.broadcast_message('data_request', {
            'request_id': request_id,
            'data_type': data_type,
            'params': params
        })
        
        # Wait for responses (simplified - in real implementation would use futures)
        await asyncio.sleep(2)
        
        return responses
        
    async def sync_with_peers(self):
        """Synchronize blockchain state with peers"""
        logger.info("Starting peer synchronization")
        
        # Request latest block info from peers
        responses = await self.request_data_from_peers('block_info', {
            'requested_fields': ['block_number', 'block_hash']
        })
        
        # Compare and sync if needed
        # (Implementation would compare responses and sync missing data)
        
        logger.info("Peer synchronization complete")