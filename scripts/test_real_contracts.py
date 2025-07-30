"""
Test real contract integration with micro transactions on BASE Sepolia
"""

import os
import sys
import asyncio
import logging
from web3 import Web3
from eth_account import Account

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from services.blockchain_base import BaseBlockchainService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealContractTester:
    def __init__(self):
        self.blockchain = BaseBlockchainService()
        self.deployer_key = os.getenv('DEPLOYER_PRIVATE_KEY')
        if not self.deployer_key:
            raise ValueError("DEPLOYER_PRIVATE_KEY not found")
        
        self.account = Account.from_key(self.deployer_key)
        self.deployer_address = self.account.address
        
    async def test_contract_connectivity(self):
        """Test basic contract connectivity"""
        logger.info("🔗 Testing Contract Connectivity")
        logger.info("=" * 50)
        
        results = {}
        
        # Test each contract with correct mappings
        contracts = {
            'PredictionMarket': os.getenv('PREDICTION_MARKET_ADDRESS'),
            'ClockchainOracle': os.getenv('ORACLE_CONTRACT_ADDRESS'),  
            'NodeRegistry': os.getenv('NODE_REGISTRY_ADDRESS'),
            'PayoutManager': os.getenv('PAYOUT_MANAGER_ADDRESS')
        }
        
        for name, address in contracts.items():
            if address:
                try:
                    contract = self.blockchain.get_contract(name, address)
                    if contract:
                        logger.info(f"✓ {name}: Connected at {address}")
                        results[name] = {'status': 'connected', 'address': address}
                    else:
                        logger.error(f"✗ {name}: Failed to load contract")
                        results[name] = {'status': 'failed', 'address': address}
                except Exception as e:
                    logger.error(f"✗ {name}: Error - {e}")
                    results[name] = {'status': 'error', 'address': address, 'error': str(e)}
            else:
                logger.warning(f"⚠ {name}: No address configured")
                results[name] = {'status': 'not_configured'}
                
        return results
    
    async def test_node_registry_read(self):
        """Test reading from NodeRegistry contract"""
        logger.info("\n📊 Testing NodeRegistry Read Operations")
        logger.info("=" * 50)
        
        try:
            address = os.getenv('NODE_REGISTRY_ADDRESS')
            if not address:
                logger.warning("NODE_REGISTRY_ADDRESS not configured")
                return {'status': 'not_configured'}
                
            contract = self.blockchain.get_contract('NodeRegistry', address)
            if not contract:
                logger.error("Failed to load NodeRegistry contract")
                return {'status': 'contract_load_failed'}
            
            # Read contract state
            node_count = contract.functions.nodeCount().call()
            active_node_count = contract.functions.activeNodeCount().call()
            total_staked = contract.functions.totalStaked().call()
            minimum_stake = contract.functions.MINIMUM_STAKE().call()
            
            logger.info(f"Node Count: {node_count}")
            logger.info(f"Active Nodes: {active_node_count}")
            logger.info(f"Total Staked: {Web3.from_wei(total_staked, 'ether')} BASE")
            logger.info(f"Minimum Stake: {Web3.from_wei(minimum_stake, 'ether')} BASE")
            
            return {
                'status': 'success',
                'node_count': node_count,
                'active_nodes': active_node_count,
                'total_staked': str(total_staked),
                'minimum_stake': str(minimum_stake)
            }
            
        except Exception as e:
            logger.error(f"Error reading NodeRegistry: {e}")
            return {'status': 'error', 'error': str(e)}
    
    async def test_prediction_market_read(self):
        """Test reading from PredictionMarket contract"""
        logger.info("\n🎯 Testing PredictionMarket Read Operations")
        logger.info("=" * 50)
        
        try:
            address = os.getenv('PREDICTION_MARKET_ADDRESS')
            if not address:
                logger.warning("PREDICTION_MARKET_ADDRESS not configured")
                return {'status': 'not_configured'}
                
            contract = self.blockchain.get_contract('PredictionMarket', address)
            if not contract:
                logger.error("Failed to load PredictionMarket contract")
                return {'status': 'contract_load_failed'}
            
            # Read contract state
            market_count = contract.functions.marketCount().call()
            submission_count = contract.functions.submissionCount().call()
            bet_count = contract.functions.betCount().call()
            platform_fee = contract.functions.PLATFORM_FEE().call()
            
            logger.info(f"Market Count: {market_count}")
            logger.info(f"Submission Count: {submission_count}")
            logger.info(f"Bet Count: {bet_count}")
            logger.info(f"Platform Fee: {platform_fee}%")
            
            return {
                'status': 'success',
                'market_count': market_count,
                'submission_count': submission_count,
                'bet_count': bet_count,
                'platform_fee': platform_fee
            }
            
        except Exception as e:
            logger.error(f"Error reading PredictionMarket: {e}")
            return {'status': 'error', 'error': str(e)}
    
    async def test_balance_check(self):
        """Check deployer balance for micro transactions"""
        logger.info("\n💰 Testing Balance & Gas Estimation")
        logger.info("=" * 50)
        
        try:
            balance = self.blockchain.w3.eth.get_balance(self.deployer_address)
            balance_eth = Web3.from_wei(balance, 'ether')
            
            gas_price = self.blockchain.w3.eth.gas_price
            gas_price_gwei = Web3.from_wei(gas_price, 'gwei')
            
            # Estimate costs for micro transactions
            estimated_gas = 200000  # Conservative estimate
            tx_cost = Web3.from_wei(estimated_gas * gas_price, 'ether')
            
            logger.info(f"Deployer Address: {self.deployer_address}")
            logger.info(f"Balance: {balance_eth} BASE")
            logger.info(f"Gas Price: {gas_price_gwei} gwei")
            logger.info(f"Estimated TX Cost: {tx_cost} BASE")
            
            sufficient = balance_eth > 0.001  # Need at least 0.001 BASE
            logger.info(f"Sufficient for micro TXs: {'✓' if sufficient else '✗'}")
            
            return {
                'status': 'success',
                'balance': str(balance),
                'balance_eth': float(balance_eth),
                'gas_price': str(gas_price),
                'estimated_tx_cost': str(estimated_gas * gas_price),
                'sufficient_balance': sufficient
            }
            
        except Exception as e:
            logger.error(f"Error checking balance: {e}")
            return {'status': 'error', 'error': str(e)}

async def main():
    """Run all real contract tests"""
    logger.info("🧪 Real Contract Integration Tests")
    logger.info("=" * 50)
    logger.info("Network: BASE Sepolia (Chain ID: 84532)")
    logger.info("Mode: Real contracts with micro transactions")
    
    try:
        tester = RealContractTester()
        
        # Run all tests
        results = {}
        results['connectivity'] = await tester.test_contract_connectivity()
        results['balance'] = await tester.test_balance_check()
        results['node_registry'] = await tester.test_node_registry_read()
        results['prediction_market'] = await tester.test_prediction_market_read()
        
        # Summary
        logger.info("\n" + "=" * 50)
        logger.info("REAL CONTRACT TEST SUMMARY")
        logger.info("=" * 50)
        
        total_tests = len(results)
        passed_tests = sum(1 for r in results.values() if r.get('status') == 'success')
        
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {total_tests - passed_tests}")
        
        if passed_tests == total_tests:
            logger.info("\n✅ All real contract tests PASSED!")
            logger.info("🚀 Ready for micro transaction testing")
        else:
            logger.warning(f"\n⚠ {total_tests - passed_tests} tests failed")
            
        return results
        
    except Exception as e:
        logger.error(f"Test setup failed: {e}")
        return {'error': str(e)}

if __name__ == "__main__":
    asyncio.run(main())