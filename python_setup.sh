#!/bin/bash

# Proteus Secondary Node Setup Script
# Usage: ./python_setup.sh [--venv] [--no-install] [--generate-reqs]

echo "============================================"
echo "Proteus Secondary Node Setup"
echo "============================================"

# Parse command line arguments
USE_VENV=false
INSTALL_DEPS=true
GENERATE_REQS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --venv)
            USE_VENV=true
            shift
            ;;
        --no-install)
            INSTALL_DEPS=false
            shift
            ;;
        --generate-reqs)
            GENERATE_REQS=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--venv] [--no-install] [--generate-reqs]"
            exit 1
            ;;
    esac
done

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

echo "Python version: $(python3 --version)"

# Setup virtual environment if requested
if [ "$USE_VENV" = true ]; then
    echo "Setting up virtual environment..."
    python3 -m venv node_venv
    source node_venv/bin/activate
    echo "Virtual environment activated"
fi

# Generate requirements.txt if requested
if [ "$GENERATE_REQS" = true ]; then
    echo "Generating requirements.txt..."
    cat > requirements_node.txt << EOF
# Proteus Secondary Node Requirements
eth-account==0.11.0
web3==6.15.1
python-dotenv==1.0.1
requests==2.31.0
websocket-client==1.7.0
EOF
    echo "Requirements file generated: requirements_node.txt"
fi

# Install dependencies if not skipped
if [ "$INSTALL_DEPS" = true ]; then
    echo "Installing dependencies..."
    
    if [ -f "requirements_node.txt" ]; then
        pip install -r requirements_node.txt
    else
        # Install minimal dependencies directly
        pip install eth-account web3 python-dotenv requests websocket-client
    fi
    
    echo "Dependencies installed"
fi

# Generate node wallet and configuration
echo "Generating node configuration..."

# Create .env file if it doesn't exist
if [ ! -f ".env.node" ]; then
    echo "Creating node environment configuration..."
    
    # Generate new wallet
    WALLET_INFO=$(python3 -c "
from eth_account import Account
account = Account.create()
print(f'{account.address}:{account.key.hex()}')
")
    
    NODE_ADDRESS=$(echo $WALLET_INFO | cut -d: -f1)
    NODE_PRIVATE_KEY=$(echo $WALLET_INFO | cut -d: -f2)
    
    # Generate node ID
    NODE_ID="node_$(date +%s)"
    
    # Create .env.node file
    cat > .env.node << EOF
# Proteus Secondary Node Configuration
# Generated on $(date)

# Node Identity
NODE_ID=$NODE_ID
NODE_NAME="Secondary Test Node"
NODE_ADDRESS=$NODE_ADDRESS
NODE_PRIVATE_KEY=$NODE_PRIVATE_KEY

# Network Configuration
PRIMARY_NODE_URL=http://localhost:5000
WS_URL=ws://localhost:5001
DATABASE_URL=\${DATABASE_URL}

# Blockchain Configuration
BASE_RPC_URL=https://sepolia.base.org
CHAIN_ID=84532

# Contract Addresses (BASE Sepolia)
PREDICTION_MARKET_ADDRESS=0x06D194A64e5276b6Be33bbe4e3e6a644a68358b3
ORACLE_CONTRACT_ADDRESS=0xFcdCB8bafa5505E33487ED32eE3F8b14b65E37f9
NODE_REGISTRY_ADDRESS=0xA69C842F335dfE1F69288a70054A34018282218d
PAYOUT_MANAGER_ADDRESS=0x142F944868596Eb0b35340f29a727b0560B130f7

# Optional: X.com API (if available)
X_API_KEY=\${X_API_KEY}
X_API_KEY_SECRET=\${X_API_KEY_SECRET}
X_BEARER_TOKEN=\${X_BEARER_TOKEN}
EOF

    echo "✓ Generated node wallet: $NODE_ADDRESS"
    echo "✓ Generated node ID: $NODE_ID"
    echo "✓ Configuration saved to .env.node"
    
    # Create secure backup
    cp .env.node .env.node.backup
    chmod 600 .env.node .env.node.backup
    
    echo ""
    echo "IMPORTANT: Save these credentials securely!"
    echo "Node Address: $NODE_ADDRESS"
    echo "Node ID: $NODE_ID"
    echo ""
    echo "To fund this node wallet, send BASE Sepolia ETH to: $NODE_ADDRESS"
    echo "Faucet: https://www.coinbase.com/faucets/base-ethereum-sepolia-faucet"
else
    echo "✓ Using existing node configuration from .env.node"
fi

# Create run scripts if they don't exist
if [ ! -f "python_run.sh" ]; then
    echo "Creating run script..."
    cat > python_run.sh << 'EOF'
#!/bin/bash
# Proteus Secondary Node Run Script

echo "Starting Proteus Secondary Node..."

# Load node environment
if [ -f ".env.node" ]; then
    export $(cat .env.node | grep -v '^#' | xargs)
fi

# Activate venv if it exists
if [ -d "node_venv" ]; then
    source node_venv/bin/activate
fi

# Run the node
python3 proteus_node_monolith.py
EOF
    chmod +x python_run.sh
fi

if [ ! -f "python_test.sh" ]; then
    echo "Creating test script..."
    cat > python_test.sh << 'EOF'
#!/bin/bash
# Proteus Secondary Node Test Script

echo "Testing Proteus Secondary Node Setup..."

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
EOF
    chmod +x python_test.sh
fi

echo ""
echo "============================================"
echo "Setup completed successfully!"
echo "============================================"
echo ""
echo "Next steps:"
echo "1. Review configuration in .env.node"
echo "2. Fund your node wallet with BASE Sepolia ETH"
echo "3. Run tests: ./python_test.sh"
echo "4. Start node: ./python_run.sh"
echo ""

if [ "$USE_VENV" = true ]; then
    echo "Note: Virtual environment is activated. To deactivate, run: deactivate"
fi