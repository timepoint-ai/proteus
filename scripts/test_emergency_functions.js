const { ethers } = require('ethers');
const fs = require('fs').promises;
const path = require('path');

async function testEmergencyFunctions() {
    console.log("🚨 Testing Emergency Functions on BASE Sepolia");
    console.log("==============================================\n");
    
    try {
        // Load deployment info
        const deploymentPath = path.join(__dirname, '../deployments/base-sepolia.json');
        const deployments = JSON.parse(await fs.readFile(deploymentPath, 'utf8'));
        
        // Set up provider and signer
        const provider = new ethers.JsonRpcProvider('https://sepolia.base.org');
        const privateKey = process.env.DEPLOYER_PRIVATE_KEY || process.env.PRIVATE_KEY;
        
        if (!privateKey) {
            throw new Error("No private key found. Set DEPLOYER_PRIVATE_KEY in .env");
        }
        
        const signer = new ethers.Wallet(privateKey, provider);
        console.log(`Testing with account: ${signer.address}\n`);
        
        // Load contract ABIs
        const getABI = async (contractName) => {
            const abiPath = `artifacts/contracts/src/${contractName}.sol/${contractName}.json`;
            const artifact = JSON.parse(await fs.readFile(abiPath, 'utf8'));
            return artifact.abi;
        };
        
        // Test results
        const results = [];
        
        // 1. Test SecurityAudit Emergency Functions
        console.log("1️⃣ Testing SecurityAudit Contract...");
        if (deployments.SecurityAudit) {
            const securityAuditABI = await getABI('SecurityAudit');
            const securityAudit = new ethers.Contract(
                deployments.SecurityAudit.address,
                securityAuditABI,
                signer
            );
            
            // Check emergency stop status
            try {
                const isEmergencyStopped = await securityAudit.emergencyStop();
                console.log(`   ✓ Emergency Stop Status: ${isEmergencyStopped ? 'ACTIVE' : 'INACTIVE'}`);
                results.push({ contract: 'SecurityAudit', function: 'emergencyStop', status: 'READABLE' });
            } catch (error) {
                console.log(`   ✗ Failed to read emergency stop: ${error.message}`);
                results.push({ contract: 'SecurityAudit', function: 'emergencyStop', status: 'FAILED', error: error.message });
            }
            
            // Check if we can toggle emergency (dry run)
            try {
                await securityAudit.toggleEmergencyStop.staticCall();
                console.log(`   ✓ Can toggle emergency stop (admin access confirmed)`);
                results.push({ contract: 'SecurityAudit', function: 'toggleEmergencyStop', status: 'AUTHORIZED' });
            } catch (error) {
                console.log(`   ⚠️  Cannot toggle emergency stop (expected if not admin)`);
                results.push({ contract: 'SecurityAudit', function: 'toggleEmergencyStop', status: 'UNAUTHORIZED' });
            }
            
            // Check blacklist functionality
            const testAddress = '0x0000000000000000000000000000000000000001';
            try {
                const isBlacklisted = await securityAudit.blacklist(testAddress);
                console.log(`   ✓ Blacklist check works: ${testAddress} is ${isBlacklisted ? 'BLACKLISTED' : 'NOT BLACKLISTED'}`);
                results.push({ contract: 'SecurityAudit', function: 'blacklist', status: 'READABLE' });
            } catch (error) {
                console.log(`   ✗ Failed to check blacklist: ${error.message}`);
                results.push({ contract: 'SecurityAudit', function: 'blacklist', status: 'FAILED', error: error.message });
            }
        }
        
        // 2. Test PredictionMarket Pause Functions
        console.log("\n2️⃣ Testing PredictionMarket Contract...");
        if (deployments.PredictionMarket) {
            const predictionMarketABI = await getABI('PredictionMarket');
            const predictionMarket = new ethers.Contract(
                deployments.PredictionMarket.address,
                predictionMarketABI,
                signer
            );
            
            // Check if contract has pause functionality
            try {
                if (predictionMarket.paused) {
                    const isPaused = await predictionMarket.paused();
                    console.log(`   ✓ Pause Status: ${isPaused ? 'PAUSED' : 'ACTIVE'}`);
                    results.push({ contract: 'PredictionMarket', function: 'paused', status: 'READABLE' });
                } else {
                    console.log(`   ℹ️  No pause function in PredictionMarket`);
                    results.push({ contract: 'PredictionMarket', function: 'paused', status: 'NOT_IMPLEMENTED' });
                }
            } catch (error) {
                console.log(`   ℹ️  No pause functionality detected`);
                results.push({ contract: 'PredictionMarket', function: 'paused', status: 'NOT_IMPLEMENTED' });
            }
        }
        
        // 3. Test AdvancedMarkets Admin Functions
        console.log("\n3️⃣ Testing AdvancedMarkets Contract...");
        if (deployments.AdvancedMarkets) {
            const advancedMarketsABI = await getABI('AdvancedMarkets');
            const advancedMarkets = new ethers.Contract(
                deployments.AdvancedMarkets.address,
                advancedMarketsABI,
                signer
            );
            
            // Check admin role
            try {
                const DEFAULT_ADMIN_ROLE = await advancedMarkets.DEFAULT_ADMIN_ROLE();
                const hasAdminRole = await advancedMarkets.hasRole(DEFAULT_ADMIN_ROLE, signer.address);
                console.log(`   ✓ Admin Role Check: ${hasAdminRole ? 'IS ADMIN' : 'NOT ADMIN'}`);
                results.push({ contract: 'AdvancedMarkets', function: 'hasRole', status: 'READABLE', isAdmin: hasAdminRole });
            } catch (error) {
                console.log(`   ✗ Failed to check admin role: ${error.message}`);
                results.push({ contract: 'AdvancedMarkets', function: 'hasRole', status: 'FAILED', error: error.message });
            }
            
            // Check market creator role
            try {
                const MARKET_CREATOR_ROLE = await advancedMarkets.MARKET_CREATOR_ROLE();
                const hasCreatorRole = await advancedMarkets.hasRole(MARKET_CREATOR_ROLE, signer.address);
                console.log(`   ✓ Market Creator Role: ${hasCreatorRole ? 'HAS ROLE' : 'NO ROLE'}`);
                results.push({ contract: 'AdvancedMarkets', function: 'MARKET_CREATOR_ROLE', status: 'READABLE', hasRole: hasCreatorRole });
            } catch (error) {
                console.log(`   ✗ Failed to check creator role: ${error.message}`);
                results.push({ contract: 'AdvancedMarkets', function: 'MARKET_CREATOR_ROLE', status: 'FAILED', error: error.message });
            }
        }
        
        // 4. Test EnhancedPredictionMarket Functions
        console.log("\n4️⃣ Testing EnhancedPredictionMarket Contract...");
        if (deployments.EnhancedPredictionMarket) {
            const enhancedPredictionMarketABI = await getABI('EnhancedPredictionMarket');
            const enhancedPredictionMarket = new ethers.Contract(
                deployments.EnhancedPredictionMarket.address,
                enhancedPredictionMarketABI,
                signer
            );
            
            // Check owner
            try {
                const owner = await enhancedPredictionMarket.owner();
                const isOwner = owner.toLowerCase() === signer.address.toLowerCase();
                console.log(`   ✓ Owner Check: ${isOwner ? 'IS OWNER' : `NOT OWNER (owner: ${owner})`}`);
                results.push({ contract: 'EnhancedPredictionMarket', function: 'owner', status: 'READABLE', isOwner });
            } catch (error) {
                console.log(`   ✗ Failed to check owner: ${error.message}`);
                results.push({ contract: 'EnhancedPredictionMarket', function: 'owner', status: 'FAILED', error: error.message });
            }
        }
        
        // Summary Report
        console.log("\n📊 Emergency Functions Test Summary");
        console.log("===================================");
        
        const authorizedCount = results.filter(r => r.status === 'AUTHORIZED' || r.isAdmin || r.isOwner).length;
        const readableCount = results.filter(r => r.status === 'READABLE').length;
        const failedCount = results.filter(r => r.status === 'FAILED').length;
        
        console.log(`✅ Authorized Functions: ${authorizedCount}`);
        console.log(`👁️  Readable Functions: ${readableCount}`);
        console.log(`❌ Failed Checks: ${failedCount}`);
        
        if (authorizedCount === 0) {
            console.log("\n⚠️  WARNING: No admin access detected!");
            console.log("Make sure to deploy with the correct admin account for mainnet.");
        }
        
        // Save test results
        const testResultsPath = path.join(__dirname, '../emergency-test-results.json');
        await fs.writeFile(testResultsPath, JSON.stringify({
            timestamp: new Date().toISOString(),
            tester: signer.address,
            network: 'base-sepolia',
            results: results,
            summary: {
                authorized: authorizedCount,
                readable: readableCount,
                failed: failedCount
            }
        }, null, 2));
        
        console.log(`\n💾 Test results saved to: emergency-test-results.json`);
        
        // Recommendations
        console.log("\n🔐 Production Recommendations:");
        console.log("1. Deploy with a multi-sig wallet for admin functions");
        console.log("2. Test emergency functions on testnet first");
        console.log("3. Document all admin addresses");
        console.log("4. Set up monitoring for emergency function calls");
        console.log("5. Have an incident response plan ready");
        
    } catch (error) {
        console.error("\n❌ Test failed:", error.message);
    }
}

// Run the test
testEmergencyFunctions().catch(console.error);