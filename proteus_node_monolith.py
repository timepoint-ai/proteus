#!/usr/bin/env python3
"""
Proteus Markets Secondary Node Monolith
A simple, self-contained node implementation for testing multi-node functionality
"""

import os
import sys
import json
import time
import logging
import requests
import threading
import websocket
from datetime import datetime, timezone
from eth_account import Account
from web3 import Web3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('proteus_node')

class ProteusNode:
    """Simple secondary node implementation"""
    
    def __init__(self):
        # Node identity
        self.node_id = os.getenv('NODE_ID', f'node_{int(time.time())}')
        self.node_name = os.getenv('NODE_NAME', 'Secondary Node')
        
        # Network configuration
        self.primary_node_url = os.getenv('PRIMARY_NODE_URL', 'http://localhost:5000')
        self.ws_url = os.getenv('WS_URL', 'ws://localhost:5001')
        
        # Blockchain configuration
        self.rpc_url = os.getenv('BASE_RPC_URL', 'https://sepolia.base.org')
        self.chain_id = int(os.getenv('CHAIN_ID', '84532'))
        
        # Node wallet
        self.private_key = os.getenv('NODE_PRIVATE_KEY')
        self.address = os.getenv('NODE_ADDRESS')
        
        # Contract addresses
        self.contracts = {
            'prediction_market': os.getenv('PREDICTION_MARKET_ADDRESS'),
            'oracle': os.getenv('ORACLE_CONTRACT_ADDRESS'),
            'node_registry': os.getenv('NODE_REGISTRY_ADDRESS'),
            'payout_manager': os.getenv('PAYOUT_MANAGER_ADDRESS')
        }
        
        # Initialize Web3
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        
        # Node state
        self.is_registered = False
        self.is_active = False
        self.consensus_proposals = {}
        self.health_metrics = {
            'uptime': 0,
            'last_heartbeat': None,
            'consensus_participation': 0,
            'oracle_submissions': 0
        }
        
        # WebSocket connection
        self.ws = None
        self.ws_connected = False
        
    def initialize(self):
        """Initialize the node"""
        logger.info(f"Initializing {self.node_name} ({self.node_id})")
        
        # Verify wallet
        if not self.private_key or not self.address:
            logger.error("Node wallet not configured")
            return False
            
        # Verify blockchain connection
        try:
            block_number = self.w3.eth.block_number
            logger.info(f"Connected to BASE Sepolia at block {block_number}")
        except Exception as e:
            logger.error(f"Failed to connect to blockchain: {e}")
            return False
            
        # Check node registration
        self.check_registration()
        
        return True
        
    def check_registration(self):
        """Check if node is registered on-chain"""
        try:
            # Check with primary node API
            response = requests.get(f"{self.primary_node_url}/api/nodes/{self.address}")
            if response.status_code == 200:
                data = response.json()
                self.is_registered = data.get('is_registered', False)
                self.is_active = data.get('is_active', False)
                logger.info(f"Node registration status: registered={self.is_registered}, active={self.is_active}")
            else:
                logger.warning("Could not check registration status")
        except Exception as e:
            logger.error(f"Error checking registration: {e}")
            
    def register_node(self):
        """Register this node with the network"""
        if self.is_registered:
            logger.info("Node already registered")
            return True
            
        try:
            # Register via primary node API
            data = {
                'address': self.address,
                'name': self.node_name,
                'node_id': self.node_id,
                'endpoint': f"http://{self.node_id}:5000"
            }
            
            response = requests.post(
                f"{self.primary_node_url}/api/nodes/register",
                json=data
            )
            
            if response.status_code == 200:
                logger.info("Node registration submitted")
                self.is_registered = True
                return True
            else:
                logger.error(f"Registration failed: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error registering node: {e}")
            return False
            
    def connect_websocket(self):
        """Connect to primary node via WebSocket"""
        def on_message(ws, message):
            try:
                data = json.loads(message)
                self.handle_ws_message(data)
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                
        def on_error(ws, error):
            logger.error(f"WebSocket error: {error}")
            
        def on_close(ws, close_status_code, close_msg):
            logger.info("WebSocket connection closed")
            self.ws_connected = False
            
        def on_open(ws):
            logger.info("WebSocket connection established")
            self.ws_connected = True
            # Send node identification
            self.send_ws_message({
                'type': 'node_identify',
                'node_id': self.node_id,
                'address': self.address
            })
            
        try:
            self.ws = websocket.WebSocketApp(
                self.ws_url,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
                on_open=on_open
            )
            
            # Run WebSocket in separate thread
            ws_thread = threading.Thread(target=self.ws.run_forever)
            ws_thread.daemon = True
            ws_thread.start()
            
        except Exception as e:
            logger.error(f"Failed to connect WebSocket: {e}")
            
    def send_ws_message(self, message):
        """Send message via WebSocket"""
        if self.ws and self.ws_connected:
            try:
                self.ws.send(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending WebSocket message: {e}")
                
    def handle_ws_message(self, data):
        """Handle incoming WebSocket messages"""
        msg_type = data.get('type')
        
        if msg_type == 'consensus_proposal':
            self.handle_consensus_proposal(data)
        elif msg_type == 'oracle_request':
            self.handle_oracle_request(data)
        elif msg_type == 'heartbeat_request':
            self.send_heartbeat()
        else:
            logger.debug(f"Received message type: {msg_type}")
            
    def handle_consensus_proposal(self, data):
        """Handle consensus proposal from network"""
        proposal_id = data.get('proposal_id')
        proposal_type = data.get('proposal_type')
        proposal_data = data.get('data')
        
        logger.info(f"Received consensus proposal {proposal_id} of type {proposal_type}")
        
        # Simple voting logic - vote yes for now
        vote = True
        
        # Send vote
        self.send_ws_message({
            'type': 'consensus_vote',
            'proposal_id': proposal_id,
            'vote': vote,
            'node_id': self.node_id
        })
        
        self.health_metrics['consensus_participation'] += 1
        
    def handle_oracle_request(self, data):
        """Handle oracle data request"""
        market_id = data.get('market_id')
        logger.info(f"Received oracle request for market {market_id}")
        
        # In a real implementation, would fetch and validate data
        # For now, acknowledge receipt
        self.send_ws_message({
            'type': 'oracle_acknowledge',
            'market_id': market_id,
            'node_id': self.node_id
        })
        
    def send_heartbeat(self):
        """Send heartbeat to network"""
        self.health_metrics['last_heartbeat'] = datetime.now(timezone.utc).isoformat()
        
        heartbeat_data = {
            'type': 'heartbeat',
            'node_id': self.node_id,
            'address': self.address,
            'timestamp': self.health_metrics['last_heartbeat'],
            'metrics': {
                'uptime': self.health_metrics['uptime'],
                'consensus_participation': self.health_metrics['consensus_participation'],
                'oracle_submissions': self.health_metrics['oracle_submissions']
            }
        }
        
        # Send via WebSocket
        self.send_ws_message(heartbeat_data)
        
        # Also send via HTTP API
        try:
            response = requests.post(
                f"{self.primary_node_url}/api/nodes/heartbeat",
                json=heartbeat_data
            )
            if response.status_code == 200:
                logger.debug("Heartbeat sent successfully")
        except Exception as e:
            logger.error(f"Error sending heartbeat: {e}")
            
    def monitor_contracts(self):
        """Monitor smart contracts for events"""
        logger.info("Starting contract monitoring")
        
        while True:
            try:
                # Get latest block
                latest_block = self.w3.eth.block_number
                
                # Check for events (simplified)
                # In real implementation, would use event filters
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error monitoring contracts: {e}")
                time.sleep(60)
                
    def run_health_monitor(self):
        """Run health monitoring loop"""
        start_time = time.time()
        
        while True:
            try:
                # Update uptime
                self.health_metrics['uptime'] = int(time.time() - start_time)
                
                # Send heartbeat every 60 seconds
                self.send_heartbeat()
                
                # Check registration status
                if not self.is_registered:
                    self.check_registration()
                    
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in health monitor: {e}")
                time.sleep(60)
                
    def run(self):
        """Main node execution loop"""
        logger.info(f"Starting {self.node_name}")
        
        # Initialize node
        if not self.initialize():
            logger.error("Failed to initialize node")
            return
            
        # Register node if needed
        if not self.is_registered:
            self.register_node()
            
        # Connect WebSocket
        self.connect_websocket()
        
        # Start monitoring threads
        health_thread = threading.Thread(target=self.run_health_monitor)
        health_thread.daemon = True
        health_thread.start()
        
        contract_thread = threading.Thread(target=self.monitor_contracts)
        contract_thread.daemon = True
        contract_thread.start()
        
        logger.info("Node is running. Press Ctrl+C to stop.")
        
        # Keep main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down node...")
            if self.ws:
                self.ws.close()
            

if __name__ == "__main__":
    # Generate wallet if not exists
    if not os.getenv('NODE_PRIVATE_KEY'):
        logger.info("Generating new node wallet...")
        account = Account.create()
        logger.info(f"Generated wallet address: {account.address}")
        logger.info(f"Private key: {account.key.hex()}")
        logger.info("Please set NODE_PRIVATE_KEY and NODE_ADDRESS environment variables")
        sys.exit(1)
        
    # Create and run node
    node = ProteusNode()
    node.run()