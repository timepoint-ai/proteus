#!/usr/bin/env python3
"""
Deployment helper script for BASE blockchain contracts
"""

import json
import os
import sys
from web3 import Web3
from eth_account import Account
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_contract_artifact(contract_name):
    """Load contract ABI and bytecode from artifacts"""
    artifact_path = f"artifacts/contracts/src/{contract_name}.sol/{contract_name}.json"
    with open(artifact_path, 'r') as f:
        return json.load(f)

def deploy_contracts(network='testnet'):
    """Deploy all Proteus Markets contracts to BASE"""
    
    # Network configuration
    if network == 'mainnet':
        rpc_url = os.environ.get('BASE_RPC_URL', 'https://mainnet.base.org')
        chain_id = 8453
        deployment_file = 'deployment-mainnet.json'
    else:
        rpc_url = os.environ.get('BASE_SEPOLIA_RPC_URL', 'https://sepolia.base.org')
        chain_id = 84532
        deployment_file = 'deployment-sepolia.json'
        
    # Initialize Web3
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    # Check connection
    if not w3.is_connected():
        logger.error(f"Failed to connect to {network} at {rpc_url}")
        return False
        
    logger.info(f"Connected to {network} (chain ID: {chain_id})")
    
    # Get deployer account
    private_key = os.environ.get('DEPLOYER_PRIVATE_KEY')
    if not private_key:
        logger.error("DEPLOYER_PRIVATE_KEY not found in environment")
        return False
        
    account = Account.from_key(private_key)
    deployer_address = account.address
    
    logger.info(f"Deploying from address: {deployer_address}")
    
    # Check balance
    balance = w3.eth.get_balance(deployer_address)
    balance_eth = w3.from_wei(balance, 'ether')
    logger.info(f"Deployer balance: {balance_eth} ETH")
    
    if balance_eth < 0.01:
        logger.error("Insufficient balance for deployment")
        return False
        
    deployed_contracts = {}
    
    try:
        # Deploy contracts in order
        # Note: ClockchainOracle is a legacy contract name — deployed on-chain as ClockchainOracle
        contracts_to_deploy = [
            'NodeRegistry',
            'ClockchainOracle',
            'PayoutManager',
            'PredictionMarket'
        ]
        
        for contract_name in contracts_to_deploy:
            logger.info(f"Deploying {contract_name}...")
            
            # Load artifact
            artifact = load_contract_artifact(contract_name)
            abi = artifact['abi']
            bytecode = artifact['bytecode']
            
            # Create contract instance
            Contract = w3.eth.contract(abi=abi, bytecode=bytecode)
            
            # Estimate gas
            gas_estimate = Contract.constructor().estimate_gas({'from': deployer_address})
            gas_price = w3.eth.gas_price
            
            logger.info(f"Estimated gas: {gas_estimate}, Gas price: {w3.from_wei(gas_price, 'gwei')} gwei")
            
            # Build transaction
            transaction = Contract.constructor().build_transaction({
                'from': deployer_address,
                'gas': int(gas_estimate * 1.2),  # Add 20% buffer
                'gasPrice': gas_price,
                'nonce': w3.eth.get_transaction_count(deployer_address),
                'chainId': chain_id
            })
            
            # Sign and send transaction
            signed_txn = w3.eth.account.sign_transaction(transaction, private_key)
            tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            logger.info(f"Transaction sent: {tx_hash.hex()}")
            
            # Wait for confirmation
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            
            if receipt['status'] == 1:
                contract_address = receipt['contractAddress']
                deployed_contracts[contract_name] = contract_address
                logger.info(f"{contract_name} deployed at: {contract_address}")
            else:
                logger.error(f"Failed to deploy {contract_name}")
                return False
                
        # Save deployment info
        deployment_info = {
            'network': network,
            'chainId': chain_id,
            'deployer': deployer_address,
            'contracts': deployed_contracts,
            'timestamp': w3.eth.get_block('latest')['timestamp']
        }
        
        with open(deployment_file, 'w') as f:
            json.dump(deployment_info, f, indent=2)
            
        logger.info(f"Deployment info saved to {deployment_file}")
        
        # Initialize contracts
        logger.info("Initializing contracts...")
        
        # Set contract addresses in PredictionMarket
        pm_address = deployed_contracts['PredictionMarket']
        pm_contract = w3.eth.contract(
            address=w3.to_checksum_address(pm_address),
            abi=load_contract_artifact('PredictionMarket')['abi']
        )
        
        # Initialize with other contract addresses
        init_tx = pm_contract.functions.initialize(
            deployed_contracts['ClockchainOracle'],
            deployed_contracts['PayoutManager'],
            deployed_contracts['NodeRegistry']
        ).build_transaction({
            'from': deployer_address,
            'gas': 100000,
            'gasPrice': gas_price,
            'nonce': w3.eth.get_transaction_count(deployer_address),
            'chainId': chain_id
        })
        
        signed_init_tx = w3.eth.account.sign_transaction(init_tx, private_key)
        init_hash = w3.eth.send_raw_transaction(signed_init_tx.rawTransaction)
        
        logger.info(f"Initialization transaction: {init_hash.hex()}")
        
        init_receipt = w3.eth.wait_for_transaction_receipt(init_hash)
        if init_receipt['status'] == 1:
            logger.info("Contracts initialized successfully!")
        else:
            logger.error("Failed to initialize contracts")
            
        return True
        
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        return False

def verify_deployment(network='testnet'):
    """Verify deployed contracts"""
    
    deployment_file = f"deployment-{network}.json"
    if not os.path.exists(deployment_file):
        logger.error(f"Deployment file {deployment_file} not found")
        return False
        
    with open(deployment_file, 'r') as f:
        deployment = json.load(f)
        
    logger.info(f"Verifying contracts on {network}...")
    logger.info(f"Deployed contracts: {json.dumps(deployment['contracts'], indent=2)}")
    
    # Network configuration
    if network == 'mainnet':
        rpc_url = os.environ.get('BASE_RPC_URL', 'https://mainnet.base.org')
    else:
        rpc_url = os.environ.get('BASE_SEPOLIA_RPC_URL', 'https://sepolia.base.org')
        
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    for contract_name, address in deployment['contracts'].items():
        code = w3.eth.get_code(address)
        if code != b'':
            logger.info(f"✓ {contract_name} at {address} is deployed")
        else:
            logger.error(f"✗ {contract_name} at {address} has no code")
            
    return True

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Deploy Proteus Markets contracts to BASE')
    parser.add_argument('--network', choices=['testnet', 'mainnet'], default='testnet',
                       help='Network to deploy to')
    parser.add_argument('--verify', action='store_true',
                       help='Verify existing deployment')
    
    args = parser.parse_args()
    
    if args.verify:
        verify_deployment(args.network)
    else:
        deploy_contracts(args.network)