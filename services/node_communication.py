import logging
import json
import asyncio
import websockets
import requests
from typing import Dict, Any, List, Optional
from threading import Thread
import time
from app import redis_client
from config import Config
from utils.crypto import CryptoUtils

logger = logging.getLogger(__name__)

class NodeCommunicationService:
    def __init__(self):
        self.crypto_utils = CryptoUtils()
        self.known_nodes = Config.KNOWN_NODES
        self.node_id = Config.NODE_OPERATOR_ID
        self.running = False
        self.websocket_connections = {}
        
    def start_communication_service(self):
        """Start the node communication service"""
        try:
            self.running = True
            
            # Start WebSocket server in a separate thread
            ws_thread = Thread(target=self._start_websocket_server)
            ws_thread.daemon = True
            ws_thread.start()
            
            # Start periodic health check
            health_thread = Thread(target=self._periodic_health_check)
            health_thread.daemon = True
            health_thread.start()
            
            # Connect to known nodes
            self._connect_to_known_nodes()
            
            logger.info("Node communication service started")
            
        except Exception as e:
            logger.error(f"Error starting communication service: {e}")
            
    def stop_communication_service(self):
        """Stop the node communication service"""
        try:
            self.running = False
            
            # Close WebSocket connections
            for node_id, ws in self.websocket_connections.items():
                asyncio.create_task(ws.close())
                
            logger.info("Node communication service stopped")
            
        except Exception as e:
            logger.error(f"Error stopping communication service: {e}")
            
    def _start_websocket_server(self):
        """Start WebSocket server for incoming connections"""
        try:
            asyncio.run(self._websocket_server())
        except Exception as e:
            logger.error(f"Error in WebSocket server: {e}")
            
    async def _websocket_server(self):
        """WebSocket server coroutine"""
        try:
            async def handle_client(websocket, path):
                try:
                    await self._handle_websocket_connection(websocket)
                except websockets.exceptions.ConnectionClosed:
                    logger.info("WebSocket connection closed")
                except Exception as e:
                    logger.error(f"Error handling WebSocket connection: {e}")
                    
            server = await websockets.serve(handle_client, "0.0.0.0", 8001)
            logger.info("WebSocket server started on port 8001")
            
            await server.wait_closed()
            
        except Exception as e:
            logger.error(f"Error starting WebSocket server: {e}")
            
    async def _handle_websocket_connection(self, websocket):
        """Handle incoming WebSocket connection"""
        try:
            # Wait for identification message
            auth_message = await websocket.recv()
            auth_data = json.loads(auth_message)
            
            if auth_data.get('type') != 'auth':
                await websocket.close(code=4000, reason="Authentication required")
                return
                
            node_id = auth_data.get('node_id')
            signature = auth_data.get('signature')
            
            # Verify node identity
            if not self._verify_node_identity(node_id, signature):
                await websocket.close(code=4001, reason="Invalid authentication")
                return
                
            # Store connection
            self.websocket_connections[node_id] = websocket
            
            # Send confirmation
            await websocket.send(json.dumps({
                'type': 'auth_success',
                'node_id': self.node_id,
                'timestamp': time.time()
            }))
            
            logger.info(f"Node {node_id} connected via WebSocket")
            
            # Handle messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self._handle_node_message(node_id, data)
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON from node {node_id}")
                except Exception as e:
                    logger.error(f"Error handling message from node {node_id}: {e}")
                    
        except Exception as e:
            logger.error(f"Error in WebSocket connection handler: {e}")
            
    def _verify_node_identity(self, node_id: str, signature: str) -> bool:
        """Verify node identity using cryptographic signature"""
        try:
            # In a real implementation, this would verify the signature
            # against the node's public key stored in the database
            from models import NodeOperator
            from app import db
            
            node = NodeOperator.query.filter_by(operator_id=node_id).first()
            if not node:
                logger.error(f"Unknown node: {node_id}")
                return False
                
            # Verify signature (simplified - in real implementation use proper crypto)
            message = f"auth:{node_id}:{int(time.time())}"
            return self.crypto_utils.verify_signature(message, signature, node.public_key)
            
        except Exception as e:
            logger.error(f"Error verifying node identity: {e}")
            return False
            
    async def _handle_node_message(self, sender_id: str, data: Dict[str, Any]):
        """Handle message from another node"""
        try:
            message_type = data.get('type')
            
            if message_type == 'ping':
                await self._handle_ping(sender_id)
            elif message_type == 'node_proposal':
                await self._handle_node_proposal(data)
            elif message_type == 'node_approved':
                await self._handle_node_approved(data)
            elif message_type == 'actor_proposal':
                await self._handle_actor_proposal(data)
            elif message_type == 'actor_approved':
                await self._handle_actor_approved(data)
            elif message_type == 'oracle_submission':
                await self._handle_oracle_submission(data)
            elif message_type == 'bet_created':
                await self._handle_bet_created(data)
            elif message_type == 'stake_placed':
                await self._handle_stake_placed(data)
            elif message_type == 'reconciliation_request':
                await self._handle_reconciliation_request(data)
            else:
                logger.warning(f"Unknown message type from {sender_id}: {message_type}")
                
        except Exception as e:
            logger.error(f"Error handling message from {sender_id}: {e}")
            
    async def _handle_ping(self, sender_id: str):
        """Handle ping from another node"""
        try:
            # Update last seen time
            from models import NodeOperator
            from app import db
            
            node = NodeOperator.query.filter_by(operator_id=sender_id).first()
            if node:
                node.last_seen = datetime.now(timezone.utc)
                db.session.commit()
                
            # Send pong response
            if sender_id in self.websocket_connections:
                await self.websocket_connections[sender_id].send(json.dumps({
                    'type': 'pong',
                    'node_id': self.node_id,
                    'timestamp': time.time()
                }))
                
        except Exception as e:
            logger.error(f"Error handling ping from {sender_id}: {e}")
            
    async def _handle_node_proposal(self, data: Dict[str, Any]):
        """Handle node proposal from another node"""
        try:
            # Store proposal in Redis for processing
            redis_client.setex(
                f"node_proposal:{data['candidate_id']}", 
                3600, 
                json.dumps(data)
            )
            
            logger.info(f"Received node proposal: {data['candidate_id']}")
            
        except Exception as e:
            logger.error(f"Error handling node proposal: {e}")
            
    async def _handle_node_approved(self, data: Dict[str, Any]):
        """Handle node approval notification"""
        try:
            logger.info(f"Node approved: {data['candidate_id']}")
            
        except Exception as e:
            logger.error(f"Error handling node approval: {e}")
            
    async def _handle_actor_proposal(self, data: Dict[str, Any]):
        """Handle actor proposal from another node"""
        try:
            # Store proposal in Redis for processing
            redis_client.setex(
                f"actor_proposal:{data['actor_id']}", 
                3600, 
                json.dumps(data)
            )
            
            logger.info(f"Received actor proposal: {data['name']}")
            
        except Exception as e:
            logger.error(f"Error handling actor proposal: {e}")
            
    async def _handle_actor_approved(self, data: Dict[str, Any]):
        """Handle actor approval notification"""
        try:
            logger.info(f"Actor approved: {data['name']}")
            
        except Exception as e:
            logger.error(f"Error handling actor approval: {e}")
            
    async def _handle_oracle_submission(self, data: Dict[str, Any]):
        """Handle oracle submission from another node"""
        try:
            # Process oracle submission
            from services.oracle import OracleService
            oracle_service = OracleService()
            
            success = oracle_service.submit_oracle_statement(
                data['bet_id'],
                data['oracle_wallet'],
                data['submitted_text'],
                data['signature']
            )
            
            if success:
                logger.info(f"Processed oracle submission for bet {data['bet_id']}")
            else:
                logger.error(f"Failed to process oracle submission for bet {data['bet_id']}")
                
        except Exception as e:
            logger.error(f"Error handling oracle submission: {e}")
            
    async def _handle_bet_created(self, data: Dict[str, Any]):
        """Handle bet creation notification"""
        try:
            logger.info(f"Bet created: {data['bet_id']}")
            
        except Exception as e:
            logger.error(f"Error handling bet creation: {e}")
            
    async def _handle_stake_placed(self, data: Dict[str, Any]):
        """Handle stake placement notification"""
        try:
            logger.info(f"Stake placed: {data['stake_id']} on bet {data['bet_id']}")
            
        except Exception as e:
            logger.error(f"Error handling stake placement: {e}")
            
    async def _handle_reconciliation_request(self, data: Dict[str, Any]):
        """Handle reconciliation request from another node"""
        try:
            # Process reconciliation request
            from services.ledger import LedgerService
            ledger_service = LedgerService()
            
            start_time = data['start_time_ms']
            end_time = data['end_time_ms']
            
            success = ledger_service.reconcile_time_entries(start_time, end_time)
            
            if success:
                logger.info(f"Processed reconciliation request for range {start_time} - {end_time}")
            else:
                logger.error(f"Failed to process reconciliation request")
                
        except Exception as e:
            logger.error(f"Error handling reconciliation request: {e}")
            
    def broadcast_message(self, message: Dict[str, Any]):
        """Broadcast message to all connected nodes"""
        try:
            # Add node ID and timestamp
            message['sender_id'] = self.node_id
            message['timestamp'] = time.time()
            
            # Sign the message
            message_str = json.dumps(message, sort_keys=True)
            message['signature'] = self.crypto_utils.sign_message(message_str)
            
            # Send via WebSocket to connected nodes
            for node_id, websocket in self.websocket_connections.items():
                try:
                    asyncio.create_task(websocket.send(json.dumps(message)))
                except Exception as e:
                    logger.error(f"Error sending message to node {node_id}: {e}")
                    
            # Also try HTTP fallback for known nodes
            self._broadcast_http(message)
            
            logger.info(f"Broadcasted message type: {message['type']}")
            
        except Exception as e:
            logger.error(f"Error broadcasting message: {e}")
            
    def sign_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Sign a message with node's private key"""
        try:
            message_str = json.dumps(message, sort_keys=True)
            signature = self.crypto_utils.sign_message(message_str)
            message['signature'] = signature
            return message
        except Exception as e:
            logger.error(f"Error signing message: {e}")
            return message
            
    def verify_message(self, message: Dict[str, Any]) -> bool:
        """Verify a message signature"""
        try:
            if 'signature' not in message:
                return False
                
            # Extract signature and remove it from message for verification
            signature = message.pop('signature')
            message_str = json.dumps(message, sort_keys=True)
            
            # Verify the signature
            is_valid = self.crypto_utils.verify_message(message_str, signature)
            
            # Restore signature to message
            message['signature'] = signature
            
            return is_valid
        except Exception as e:
            logger.error(f"Error verifying message: {e}")
            return False
            
    def _broadcast_http(self, message: Dict[str, Any]):
        """Broadcast message via HTTP as fallback"""
        try:
            for node_address in self.known_nodes:
                try:
                    response = requests.post(
                        f"http://{node_address}/api/node/message",
                        json=message,
                        timeout=5
                    )
                    if response.status_code == 200:
                        logger.debug(f"Message sent to {node_address} via HTTP")
                    else:
                        logger.warning(f"HTTP message failed to {node_address}: {response.status_code}")
                        
                except requests.RequestException as e:
                    logger.warning(f"HTTP message failed to {node_address}: {e}")
                    
        except Exception as e:
            logger.error(f"Error in HTTP broadcast: {e}")
            
    def _connect_to_known_nodes(self):
        """Connect to known nodes via WebSocket"""
        try:
            for node_address in self.known_nodes:
                try:
                    # Start connection in background
                    connect_thread = Thread(target=self._connect_to_node, args=(node_address,))
                    connect_thread.daemon = True
                    connect_thread.start()
                    
                except Exception as e:
                    logger.error(f"Error connecting to {node_address}: {e}")
                    
        except Exception as e:
            logger.error(f"Error connecting to known nodes: {e}")
            
    def _connect_to_node(self, node_address: str):
        """Connect to a specific node via WebSocket"""
        try:
            asyncio.run(self._websocket_client(node_address))
        except Exception as e:
            logger.error(f"Error in WebSocket client to {node_address}: {e}")
            
    async def _websocket_client(self, node_address: str):
        """WebSocket client coroutine"""
        try:
            uri = f"ws://{node_address}:8001"
            
            async with websockets.connect(uri) as websocket:
                # Send authentication
                auth_message = {
                    'type': 'auth',
                    'node_id': self.node_id,
                    'signature': self.crypto_utils.sign_message(f"auth:{self.node_id}:{int(time.time())}")
                }
                
                await websocket.send(json.dumps(auth_message))
                
                # Wait for confirmation
                response = await websocket.recv()
                response_data = json.loads(response)
                
                if response_data.get('type') == 'auth_success':
                    logger.info(f"Connected to node {node_address}")
                    
                    # Handle messages
                    async for message in websocket:
                        try:
                            data = json.loads(message)
                            await self._handle_node_message(response_data['node_id'], data)
                        except Exception as e:
                            logger.error(f"Error handling message from {node_address}: {e}")
                else:
                    logger.error(f"Authentication failed with {node_address}")
                    
        except Exception as e:
            logger.error(f"Error in WebSocket client to {node_address}: {e}")
            
    def _periodic_health_check(self):
        """Periodic health check for connected nodes"""
        try:
            while self.running:
                try:
                    # Send ping to all connected nodes
                    ping_message = {
                        'type': 'ping',
                        'node_id': self.node_id,
                        'timestamp': time.time()
                    }
                    
                    for node_id, websocket in self.websocket_connections.items():
                        try:
                            asyncio.create_task(websocket.send(json.dumps(ping_message)))
                        except Exception as e:
                            logger.error(f"Error sending ping to {node_id}: {e}")
                            
                    # Sleep for 30 seconds
                    time.sleep(30)
                    
                except Exception as e:
                    logger.error(f"Error in periodic health check: {e}")
                    time.sleep(30)
                    
        except Exception as e:
            logger.error(f"Error in periodic health check thread: {e}")
            
    def get_connection_status(self) -> Dict[str, Any]:
        """Get current connection status"""
        try:
            return {
                'node_id': self.node_id,
                'connected_nodes': list(self.websocket_connections.keys()),
                'connection_count': len(self.websocket_connections),
                'known_nodes': self.known_nodes,
                'service_running': self.running
            }
            
        except Exception as e:
            logger.error(f"Error getting connection status: {e}")
            return {
                'node_id': self.node_id,
                'connected_nodes': [],
                'connection_count': 0,
                'known_nodes': [],
                'service_running': False,
                'error': str(e)
            }

from datetime import datetime, timezone
