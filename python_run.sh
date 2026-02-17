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