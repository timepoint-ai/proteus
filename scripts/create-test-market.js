#!/usr/bin/env node
const { ethers } = require('ethers');
const fs = require('fs');
require('dotenv').config();

// Contract ABI (minimal - just what we need)
const CONTRACT_ABI = [
    {
        "inputs": [
            {"internalType": "string", "name": "_question", "type": "string"},
            {"internalType": "string", "name": "_actorUsername", "type": "string"},
            {"internalType": "uint256", "name": "_duration", "type": "uint256"},
            {"internalType": "address[]", "name": "_oracleWallets", "type": "address[]"},
            {"internalType": "string", "name": "_metadata", "type": "string"}
        ],
        "name": "createMarket",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "_marketId", "type": "uint256"},
            {"internalType": "string", "name": "_predictedText", "type": "string"},
            {"internalType": "string", "name": "_submissionType", "type": "string"}
        ],
        "name": "createSubmission",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "payable",
        "type": "function"
    }
];

// Contract address on BASE Sepolia
const CONTRACT_ADDRESS = '0x6b67cb0daaf78f63bd11195df0fd9ffe4361b93c';

async function main() {
    console.log('🚀 Creating Test Market on BASE Sepolia...\n');
    
    // Connect to BASE Sepolia
    const provider = new ethers.JsonRpcProvider('https://sepolia.base.org');
    
    // Use private key from environment or create a test wallet
    let wallet;
    if (process.env.PRIVATE_KEY) {
        wallet = new ethers.Wallet(process.env.PRIVATE_KEY, provider);
    } else {
        console.log('⚠️  No PRIVATE_KEY found in .env, creating a new test wallet...');
        wallet = ethers.Wallet.createRandom().connect(provider);
        console.log('📝 New test wallet created:', wallet.address);
        console.log('🔑 Private key (save this!):', wallet.privateKey);
        console.log('\n⚠️  Send some testnet ETH to this address before continuing!');
        console.log('🚰 Get testnet ETH from: https://www.alchemy.com/faucets/base-sepolia\n');
        
        // Check balance
        const balance = await provider.getBalance(wallet.address);
        console.log('💰 Current balance:', ethers.formatEther(balance), 'ETH');
        
        if (balance === 0n) {
            console.log('\n❌ No ETH in wallet. Please fund it and run again.');
            process.exit(1);
        }
    }
    
    // Connect to contract
    const contract = new ethers.Contract(CONTRACT_ADDRESS, CONTRACT_ABI, wallet);
    
    // Create market parameters
    const marketParams = {
        question: "I predict Elon will tweet about Mars",
        actorUsername: "@elonmusk",
        duration: 86400, // 24 hours in seconds
        oracleWallets: [
            wallet.address, // Use the creator as an oracle for testing
            "0x0000000000000000000000000000000000000001",
            "0x0000000000000000000000000000000000000002"
        ],
        metadata: JSON.stringify({
            created: new Date().toISOString(),
            test: true
        })
    };
    
    try {
        console.log('📋 Market Parameters:');
        console.log('  - Question:', marketParams.question);
        console.log('  - Actor:', marketParams.actorUsername);
        console.log('  - Duration:', marketParams.duration / 3600, 'hours');
        console.log('  - Creator:', wallet.address);
        console.log('\n🔄 Creating market on blockchain...');
        
        // Create the market (no value sent for market creation)
        const tx = await contract.createMarket(
            marketParams.question,
            marketParams.actorUsername,
            marketParams.duration,
            marketParams.oracleWallets,
            marketParams.metadata
        );
        
        console.log('📝 Transaction sent:', tx.hash);
        console.log('⏳ Waiting for confirmation...');
        
        const receipt = await tx.wait();
        console.log('✅ Market created successfully!');
        console.log('  - Block:', receipt.blockNumber);
        console.log('  - Gas used:', receipt.gasUsed.toString());
        
        // Try to get the market ID from events
        const marketId = 0; // First market will be ID 0
        console.log('  - Market ID:', marketId);
        
        // Now create the initial submission
        console.log('\n🔄 Creating initial submission...');
        const submissionTx = await contract.createSubmission(
            marketId,
            marketParams.question, // Use the question as the initial prediction
            "original",
            { value: ethers.parseEther("0.0001") } // Send 0.0001 ETH as stake
        );
        
        console.log('📝 Submission transaction sent:', submissionTx.hash);
        const submissionReceipt = await submissionTx.wait();
        console.log('✅ Initial submission created!');
        
        console.log('\n🎉 Success! Market and initial submission created.');
        console.log('📍 View your market at: http://localhost:5000/clockchain/market/0');
        console.log('🔗 View on Basescan: https://sepolia.basescan.org/tx/' + receipt.transactionHash);
        
    } catch (error) {
        console.error('\n❌ Error creating market:', error.message);
        if (error.reason) console.error('Reason:', error.reason);
        if (error.data) console.error('Data:', error.data);
        process.exit(1);
    }
}

// Run the script
main().catch(console.error);