#!/bin/bash
# Clockchain Secondary Node Test Script

echo "Testing Clockchain Secondary Node Setup..."

# Load node environment
if [ -f ".env.node" ]; then
    export $(cat .env.node | grep -v '^#' | xargs)
fi

# Activate venv if it exists
if [ -d "node_venv" ]; then
    source node_venv/bin/activate
fi

# Run tests
python3 -c "
import sys
import os

print('=== Node Configuration Test ===')

# Check environment variables
required_vars = ['NODE_ID', 'NODE_ADDRESS', 'NODE_PRIVATE_KEY', 'BASE_RPC_URL']
missing_vars = []

for var in required_vars:
    if not os.getenv(var):
        missing_vars.append(var)
    else:
        print(f'✓ {var}: {os.getenv(var)[:20]}...' if var.endswith('KEY') else f'✓ {var}: {os.getenv(var)}')

if missing_vars:
    print(f'✗ Missing environment variables: {missing_vars}')
    sys.exit(1)

print('\n=== Python Dependencies Test ===')

try:
    import eth_account
    print('✓ eth_account installed')
except ImportError:
    print('✗ eth_account not installed')
    sys.exit(1)

try:
    import web3
    print('✓ web3 installed')
except ImportError:
    print('✗ web3 not installed')
    sys.exit(1)

try:
    import websocket
    print('✓ websocket-client installed')
except ImportError:
    print('✗ websocket-client not installed')
    sys.exit(1)

try:
    import requests
    print('✓ requests installed')
except ImportError:
    print('✗ requests not installed')
    sys.exit(1)

try:
    import dotenv
    print('✓ python-dotenv installed')
except ImportError:
    print('✗ python-dotenv not installed')
    sys.exit(1)

print('\n=== Blockchain Connection Test ===')

try:
    from web3 import Web3
    w3 = Web3(Web3.HTTPProvider(os.getenv('BASE_RPC_URL')))
    if w3.is_connected():
        block = w3.eth.block_number
        print(f'✓ Connected to BASE Sepolia (block: {block})')
        
        # Check node balance
        address = os.getenv('NODE_ADDRESS')
        balance = w3.eth.get_balance(address)
        eth_balance = w3.from_wei(balance, 'ether')
        print(f'✓ Node balance: {eth_balance} ETH')
        
        if balance == 0:
            print('⚠ Warning: Node wallet has 0 balance. Please fund it.')
    else:
        print('✗ Cannot connect to BASE Sepolia')
        sys.exit(1)
except Exception as e:
    print(f'✗ Blockchain connection error: {e}')
    sys.exit(1)

print('\n=== Primary Node Connection Test ===')

try:
    import requests
    primary_url = os.getenv('PRIMARY_NODE_URL', 'http://localhost:5000')
    response = requests.get(f'{primary_url}/api/health', timeout=5)
    if response.status_code == 200:
        print(f'✓ Connected to primary node at {primary_url}')
    else:
        print(f'⚠ Primary node returned status {response.status_code}')
except requests.exceptions.ConnectionError:
    print('⚠ Cannot connect to primary node (is it running?)')
except Exception as e:
    print(f'⚠ Primary node connection error: {e}')

print('\n=== All tests completed ===')
"