const { ethers } = require('ethers');
const fs = require('fs').promises;
const path = require('path');

// Configuration
const BASE_MAINNET_RPC = 'https://mainnet.base.org';
const BASE_SEPOLIA_RPC = 'https://sepolia.base.org';
const CHECK_INTERVAL = 60000; // Check every minute
const LOW_GAS_THRESHOLD = 0.1; // Alert when below 0.1 gwei

class GasPriceMonitor {
    constructor() {
        this.mainnetProvider = new ethers.JsonRpcProvider(BASE_MAINNET_RPC);
        this.testnetProvider = new ethers.JsonRpcProvider(BASE_SEPOLIA_RPC);
        this.priceHistory = [];
        this.alertThresholds = {
            veryLow: 0.05,  // < 0.05 gwei - Deploy immediately
            low: 0.1,       // < 0.1 gwei - Good time
            medium: 0.5,    // < 0.5 gwei - Acceptable
            high: 1.0       // > 1.0 gwei - Wait
        };
    }
    
    async getCurrentGasPrices() {
        try {
            const [mainnetGas, testnetGas] = await Promise.all([
                this.mainnetProvider.getFeeData(),
                this.testnetProvider.getFeeData()
            ]);
            
            return {
                mainnet: {
                    gasPrice: ethers.formatUnits(mainnetGas.gasPrice, 'gwei'),
                    maxFeePerGas: mainnetGas.maxFeePerGas ? 
                        ethers.formatUnits(mainnetGas.maxFeePerGas, 'gwei') : null,
                    maxPriorityFeePerGas: mainnetGas.maxPriorityFeePerGas ?
                        ethers.formatUnits(mainnetGas.maxPriorityFeePerGas, 'gwei') : null
                },
                testnet: {
                    gasPrice: ethers.formatUnits(testnetGas.gasPrice, 'gwei'),
                    maxFeePerGas: testnetGas.maxFeePerGas ?
                        ethers.formatUnits(testnetGas.maxFeePerGas, 'gwei') : null,
                    maxPriorityFeePerGas: testnetGas.maxPriorityFeePerGas ?
                        ethers.formatUnits(testnetGas.maxPriorityFeePerGas, 'gwei') : null
                }
            };
        } catch (error) {
            console.error('Error fetching gas prices:', error);
            return null;
        }
    }
    
    getRecommendation(gasPrice) {
        const price = parseFloat(gasPrice);
        if (price < this.alertThresholds.veryLow) {
            return { level: 'VERY LOW', action: '🟢 DEPLOY NOW! Excellent gas prices', color: '\x1b[32m' };
        } else if (price < this.alertThresholds.low) {
            return { level: 'LOW', action: '🟢 Good time to deploy', color: '\x1b[32m' };
        } else if (price < this.alertThresholds.medium) {
            return { level: 'MEDIUM', action: '🟡 Acceptable for deployment', color: '\x1b[33m' };
        } else {
            return { level: 'HIGH', action: '🔴 Consider waiting', color: '\x1b[31m' };
        }
    }
    
    calculateDeploymentCost(gasPrice) {
        // Estimated gas usage for all contracts
        const estimatedGasUnits = {
            PredictionMarket: 3000000,
            ClockchainOracle: 2500000,
            NodeRegistry: 2000000,
            PayoutManager: 2500000,
            ActorRegistry: 2000000,
            EnhancedPredictionMarket: 3500000,
            DecentralizedOracle: 3000000,
            AdvancedMarkets: 4000000,
            SecurityAudit: 2500000,
            Total: 25000000
        };
        
        const priceInGwei = parseFloat(gasPrice);
        const totalCostInETH = (estimatedGasUnits.Total * priceInGwei) / 1e9;
        const totalCostInUSD = totalCostInETH * 4000; // Approximate ETH price
        
        return {
            gasUnits: estimatedGasUnits.Total,
            costInETH: totalCostInETH.toFixed(6),
            costInUSD: totalCostInUSD.toFixed(2)
        };
    }
    
    async startMonitoring() {
        console.log("🔍 Starting BASE Gas Price Monitor");
        console.log("==================================\n");
        
        const monitor = async () => {
            const prices = await this.getCurrentGasPrices();
            if (!prices) return;
            
            const mainnetRec = this.getRecommendation(prices.mainnet.gasPrice);
            const testnetRec = this.getRecommendation(prices.testnet.gasPrice);
            
            // Clear console for clean display
            console.clear();
            
            console.log("⛽ BASE Gas Price Monitor");
            console.log("========================");
            console.log(`Last Updated: ${new Date().toLocaleString()}\n`);
            
            // Mainnet prices
            console.log("📊 BASE MAINNET:");
            console.log(`Gas Price: ${mainnetRec.color}${prices.mainnet.gasPrice} gwei\x1b[0m`);
            console.log(`Status: ${mainnetRec.action}`);
            
            const mainnetCost = this.calculateDeploymentCost(prices.mainnet.gasPrice);
            console.log(`\nDeployment Cost Estimate:`);
            console.log(`- ETH: ${mainnetCost.costInETH}`);
            console.log(`- USD: $${mainnetCost.costInUSD}`);
            
            // Testnet prices  
            console.log("\n📊 BASE SEPOLIA (Testnet):");
            console.log(`Gas Price: ${testnetRec.color}${prices.testnet.gasPrice} gwei\x1b[0m`);
            console.log(`Status: ${testnetRec.action}`);
            
            // Historical data
            this.priceHistory.push({
                timestamp: new Date(),
                mainnet: parseFloat(prices.mainnet.gasPrice),
                testnet: parseFloat(prices.testnet.gasPrice)
            });
            
            // Keep only last hour of data
            const oneHourAgo = new Date(Date.now() - 3600000);
            this.priceHistory = this.priceHistory.filter(p => p.timestamp > oneHourAgo);
            
            if (this.priceHistory.length > 1) {
                const mainnetPrices = this.priceHistory.map(p => p.mainnet);
                const avgMainnet = mainnetPrices.reduce((a, b) => a + b) / mainnetPrices.length;
                const minMainnet = Math.min(...mainnetPrices);
                const maxMainnet = Math.max(...mainnetPrices);
                
                console.log("\n📈 Last Hour Statistics (Mainnet):");
                console.log(`Average: ${avgMainnet.toFixed(4)} gwei`);
                console.log(`Minimum: ${minMainnet.toFixed(4)} gwei`);
                console.log(`Maximum: ${maxMainnet.toFixed(4)} gwei`);
            }
            
            // Alert for very low prices
            if (mainnetRec.level === 'VERY LOW') {
                console.log("\n🚨 ALERT: VERY LOW GAS PRICES!");
                console.log("Perfect time for deployment!");
                
                // Save alert to file
                const alertPath = path.join(__dirname, '../.gas-alerts.log');
                const alertMessage = `${new Date().toISOString()} - VERY LOW GAS: ${prices.mainnet.gasPrice} gwei\n`;
                await fs.appendFile(alertPath, alertMessage).catch(() => {});
            }
            
            console.log("\n💡 Tips:");
            console.log("- Gas is typically lowest during weekends");
            console.log("- Early morning UTC often has lower prices");
            console.log("- Monitor for at least 24h for patterns");
            console.log("\nPress Ctrl+C to stop monitoring");
        };
        
        // Initial check
        await monitor();
        
        // Set up interval
        setInterval(monitor, CHECK_INTERVAL);
    }
}

// Run the monitor
const gasMonitor = new GasPriceMonitor();
gasMonitor.startMonitoring().catch(console.error);

// Handle graceful shutdown
process.on('SIGINT', () => {
    console.log('\n\n👋 Gas monitor stopped');
    process.exit(0);
});