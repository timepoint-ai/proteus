"""
Deploy Clockchain contracts to BASE Sepolia testnet with micro transactions
Uses industry best practices for penny contracts (0.001 BASE or less)
"""

import os
import sys
import json
import asyncio
import time
from web3 import Web3
from eth_account import Account
from decimal import Decimal
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Micro transaction amounts (industry best practice for testing)
MICRO_STAKE = Web3.to_wei(0.001, 'ether')  # 0.001 BASE for testing
MICRO_PLATFORM_FEE = Web3.to_wei(0.0001, 'ether')  # 0.0001 BASE fee


class TestContractDeployer:
    def __init__(self):
        # BASE Sepolia configuration
        self.w3 = Web3(Web3.HTTPProvider(Config.BASE_SEPOLIA_RPC_URL))
        self.chain_id = 84532  # BASE Sepolia
        
        # Load deployer account from environment
        self.deployer_key = os.getenv('DEPLOYER_PRIVATE_KEY')
        if not self.deployer_key:
            raise ValueError("DEPLOYER_PRIVATE_KEY not set in environment")
            
        self.account = Account.from_key(self.deployer_key)
        self.deployer_address = self.account.address
        
        logger.info(f"Deployer address: {self.deployer_address}")
        logger.info(f"Connected to BASE Sepolia: {self.w3.is_connected()}")
        
        # Check balance
        balance = self.w3.eth.get_balance(self.deployer_address)
        logger.info(f"Deployer balance: {Web3.from_wei(balance, 'ether')} ETH")
        
        if balance < Web3.to_wei(0.01, 'ether'):
            logger.warning("Low balance! Get BASE Sepolia ETH from faucet: https://www.coinbase.com/faucets/base-ethereum-goerli-faucet")
    
    def load_contract_artifact(self, contract_name):
        """Load contract ABI and bytecode from Hardhat artifacts"""
        artifact_path = f"artifacts/contracts/src/{contract_name}.sol/{contract_name}.json"
        
        try:
            with open(artifact_path, 'r') as f:
                artifact = json.load(f)
                return artifact['abi'], artifact['bytecode']
        except FileNotFoundError:
            logger.error(f"Contract artifact not found: {artifact_path}")
            logger.info("Run 'npx hardhat compile' to generate artifacts")
            return None, None
    
    async def deploy_contract(self, contract_name, *args):
        """Deploy a contract with micro gas settings"""
        abi, bytecode = self.load_contract_artifact(contract_name)
        if not abi or not bytecode:
            return None
            
        try:
            # Create contract instance
            contract = self.w3.eth.contract(abi=abi, bytecode=bytecode)
            
            # Get current gas price (usually < 0.002 gwei on BASE)
            gas_price = self.w3.eth.gas_price
            logger.info(f"Current gas price: {Web3.from_wei(gas_price, 'gwei')} gwei")
            
            # Build constructor transaction with fresh nonce
            nonce = self.w3.eth.get_transaction_count(self.deployer_address)
            constructor_tx = contract.constructor(*args).build_transaction({
                'from': self.deployer_address,
                'nonce': nonce,
                'gas': 3000000,  # 3M gas limit
                'gasPrice': gas_price + 1000000000,  # Add 1 gwei to avoid underpricing
                'chainId': self.chain_id
            })
            
            # Sign and send transaction
            signed_tx = self.account.sign_transaction(constructor_tx)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            
            logger.info(f"Deploying {contract_name}... TX: {tx_hash.hex()}")
            
            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt.status == 1:
                logger.info(f"✓ {contract_name} deployed at: {receipt.contractAddress}")
                logger.info(f"  Gas used: {receipt.gasUsed} ({Web3.from_wei(receipt.gasUsed * gas_price, 'ether')} ETH)")
                # Add delay between deployments to avoid nonce conflicts
                await asyncio.sleep(2)
                return receipt.contractAddress
            else:
                logger.error(f"✗ {contract_name} deployment failed")
                return None
                
        except Exception as e:
            logger.error(f"Error deploying {contract_name}: {e}")
            return None
    
    async def deploy_all_contracts(self):
        """Deploy all Clockchain contracts with micro amounts"""
        deployed = {}
        
        # 1. Deploy PredictionMarket first (no constructor args)
        logger.info("\n1. Deploying PredictionMarket...")
        prediction_market = await self.deploy_contract("PredictionMarket")
        if prediction_market:
            deployed['PredictionMarket'] = prediction_market
        
        # 2. Deploy ClockchainOracle (needs PredictionMarket address)
        if prediction_market:
            logger.info("\n2. Deploying ClockchainOracle...")
            oracle = await self.deploy_contract("ClockchainOracle", prediction_market)
            if oracle:
                deployed['ClockchainOracle'] = oracle
        else:
            logger.error("Cannot deploy ClockchainOracle: PredictionMarket deployment failed")
            oracle = None
        
        # 3. Deploy NodeRegistry (no constructor args)
        logger.info("\n3. Deploying NodeRegistry...")
        node_registry = await self.deploy_contract("NodeRegistry")
        if node_registry:
            deployed['NodeRegistry'] = node_registry
        
        # 4. Deploy PayoutManager (needs PredictionMarket and Oracle addresses)
        if prediction_market and oracle:
            logger.info("\n4. Deploying PayoutManager...")
            payout_manager = await self.deploy_contract(
                "PayoutManager",
                prediction_market,  # Market address
                oracle  # Oracle address
            )
        else:
            logger.error("Cannot deploy PayoutManager: Missing PredictionMarket or Oracle")
            payout_manager = None
        if payout_manager:
            deployed['PayoutManager'] = payout_manager
        
        # Save deployment addresses
        if deployed:
            deployment_file = "deployments/base-sepolia-test.json"
            os.makedirs("deployments", exist_ok=True)
            
            deployment_data = {
                "network": "base-sepolia",
                "chainId": self.chain_id,
                "contracts": deployed,
                "microAmounts": {
                    "stake": str(MICRO_STAKE),
                    "platformFee": str(MICRO_PLATFORM_FEE),
                    "stakeInBase": "0.001",
                    "feeInBase": "0.0001"
                }
            }
            
            with open(deployment_file, 'w') as f:
                json.dump(deployment_data, f, indent=2)
                
            logger.info(f"\n✓ Deployment addresses saved to {deployment_file}")
            
            # Create .env update instructions
            logger.info("\n📝 Add these to your .env or Replit Secrets:")
            logger.info(f"NODE_REGISTRY_ADDRESS={deployed.get('NodeRegistry', '')}")
            logger.info(f"ORACLE_CONTRACT_ADDRESS={deployed.get('ClockchainOracle', '')}")
            logger.info(f"PREDICTION_MARKET_ADDRESS={deployed.get('PredictionMarket', '')}")
            logger.info(f"PAYOUT_MANAGER_ADDRESS={deployed.get('PayoutManager', '')}")
            
            # Display Basescan links
            logger.info("\n🔍 View on Basescan:")
            for name, addr in deployed.items():
                logger.info(f"{name}: https://sepolia.basescan.org/address/{addr}")
        
        return deployed
    
    async def setup_test_environment(self, deployed):
        """Setup initial test environment with micro transactions"""
        if not deployed:
            return
            
        logger.info("\n🔧 Setting up test environment...")
        
        # Register oracle in ClockchainOracle contract
        if 'ClockchainOracle' in deployed:
            try:
                oracle_abi, _ = self.load_contract_artifact('ClockchainOracle')
                oracle_contract = self.w3.eth.contract(
                    address=deployed['ClockchainOracle'],
                    abi=oracle_abi
                )
                
                # Register deployer as oracle
                tx = oracle_contract.functions.registerOracle(
                    self.deployer_address
                ).build_transaction({
                    'from': self.deployer_address,
                    'nonce': self.w3.eth.get_transaction_count(self.deployer_address),
                    'gas': 100000,
                    'gasPrice': self.w3.eth.gas_price,
                    'chainId': self.chain_id
                })
                
                signed_tx = self.account.sign_transaction(tx)
                tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
                
                if receipt.status == 1:
                    logger.info("✓ Oracle registered successfully")
                    
            except Exception as e:
                logger.error(f"Error setting up oracle: {e}")
        
        logger.info("\n✅ Test environment ready!")
        logger.info("Micro transaction amounts configured:")
        logger.info(f"- Node stake: 0.001 BASE")
        logger.info(f"- Platform fee: 0.0001 BASE") 
        logger.info(f"- All test transactions use < 0.01 BASE total")


async def main():
    """Deploy test contracts with micro transactions"""
    logger.info("🚀 Clockchain Test Contract Deployment")
    logger.info("=====================================")
    logger.info("Using micro transactions (penny contracts)")
    logger.info("Network: BASE Sepolia (Chain ID: 84532)")
    
    deployer = TestContractDeployer()
    
    # Check if contracts need compilation
    if not os.path.exists("artifacts/contracts"):
        logger.error("No contract artifacts found!")
        logger.info("Run: npx hardhat compile")
        return
    
    # Deploy all contracts
    deployed = await deployer.deploy_all_contracts()
    
    # Setup test environment
    await deployer.setup_test_environment(deployed)
    
    if deployed:
        logger.info("\n🎉 Deployment complete!")
        logger.info("Total contracts deployed: " + str(len(deployed)))
        
        # Calculate total deployment cost
        # Rough estimate: 3M gas per contract * 4 contracts * 0.002 gwei
        estimated_cost = 3000000 * 4 * 0.002 * 10**9 / 10**18
        logger.info(f"Estimated total cost: ~{estimated_cost:.6f} ETH")
    else:
        logger.error("\n❌ Deployment failed")


if __name__ == "__main__":
    asyncio.run(main())