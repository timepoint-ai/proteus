# Clockchain Secondary Node Setup

This guide helps you set up and run a secondary Clockchain node for testing multi-node functionality.

## Quick Start

1. **Run Setup Script**
   ```bash
   ./python_setup.sh
   ```
   This will:
   - Generate a new node wallet automatically
   - Create configuration file `.env.node`
   - Install minimal Python dependencies

2. **Fund Your Node Wallet**
   - Check the generated wallet address in `.env.node`
   - Send BASE Sepolia ETH to your node address
   - Faucet: https://www.coinbase.com/faucets/base-ethereum-sepolia-faucet

3. **Test Your Setup**
   ```bash
   ./python_test.sh
   ```
   This verifies:
   - Node configuration
   - Python dependencies
   - Blockchain connection
   - Primary node connectivity

4. **Run the Node**
   ```bash
   ./python_run.sh
   ```

## Setup Options

### With Virtual Environment
```bash
./python_setup.sh --venv
```

### Generate Requirements File
```bash
./python_setup.sh --generate-reqs
```

### Skip Dependency Installation
```bash
./python_setup.sh --no-install
```

## What the Secondary Node Does

- **Registers** with the primary node network
- **Participates** in consensus voting
- **Monitors** smart contracts on BASE Sepolia
- **Sends** heartbeats to maintain active status
- **Responds** to oracle requests (simplified)

## Environment Variables

The setup script automatically generates these in `.env.node`:

- `NODE_ID` - Unique identifier for this node
- `NODE_ADDRESS` - Ethereum wallet address
- `NODE_PRIVATE_KEY` - Wallet private key (keep secure!)
- `PRIMARY_NODE_URL` - URL of the main Clockchain node
- `BASE_RPC_URL` - BASE Sepolia RPC endpoint
- Contract addresses for all deployed smart contracts

## Troubleshooting

### Cannot connect to primary node
- Ensure the main Clockchain app is running on port 5000
- Check `PRIMARY_NODE_URL` in `.env.node`

### Node wallet has 0 balance
- Fund your node address with BASE Sepolia ETH
- Use the Coinbase faucet link above

### Dependencies not found
- Run `pip install -r requirements_node.txt`
- Or run setup again: `./python_setup.sh`

## Security Notes

- Keep `.env.node` secure - it contains private keys
- A backup is created at `.env.node.backup`
- Never commit these files to version control

## Architecture

The secondary node is a lightweight monolithic Python script that:
- Uses minimal dependencies
- Connects via HTTP API and WebSocket
- Maintains its own health metrics
- Can be easily deployed on separate machines

For production multi-node deployments, see the full documentation in `PYTHON_NODE.md`.