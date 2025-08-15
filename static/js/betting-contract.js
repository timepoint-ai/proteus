/**
 * Betting Contract Integration
 * Handles actual blockchain transactions for betting and submissions
 */

class BettingContract {
    constructor() {
        this.web3 = null;
        this.contract = null;
        this.account = null;
        
        // EnhancedPredictionMarket contract address on BASE Sepolia
        this.contractAddress = '0x6B67Cb0DaAf78f63BD11195Df0FD9FFe4361b93C';
        
        // Contract ABI (simplified for betting operations)
        this.contractABI = [
            {
                "inputs": [
                    {"internalType": "uint256", "name": "marketId", "type": "uint256"},
                    {"internalType": "string", "name": "predictedText", "type": "string"}
                ],
                "name": "submitPrediction",
                "outputs": [],
                "stateMutability": "payable",
                "type": "function"
            },
            {
                "inputs": [
                    {"internalType": "uint256", "name": "marketId", "type": "uint256"},
                    {"internalType": "uint256", "name": "submissionId", "type": "uint256"}
                ],
                "name": "placeBet",
                "outputs": [],
                "stateMutability": "payable",
                "type": "function"
            },
            {
                "inputs": [
                    {"internalType": "uint256", "name": "marketId", "type": "uint256"}
                ],
                "name": "getMarketSubmissions",
                "outputs": [
                    {
                        "components": [
                            {"internalType": "address", "name": "submitter", "type": "address"},
                            {"internalType": "string", "name": "predictedText", "type": "string"},
                            {"internalType": "uint256", "name": "totalStake", "type": "uint256"},
                            {"internalType": "uint256", "name": "timestamp", "type": "uint256"}
                        ],
                        "internalType": "struct Submission[]",
                        "name": "",
                        "type": "tuple[]"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [
                    {"internalType": "uint256", "name": "marketId", "type": "uint256"},
                    {"internalType": "string", "name": "predictedText", "type": "string"}
                ],
                "name": "isDuplicateSubmission",
                "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
                "stateMutability": "view",
                "type": "function"
            }
        ];
    }
    
    async init() {
        if (typeof window.ethereum === 'undefined') {
            throw new Error('MetaMask is not installed');
        }
        
        // Check if Web3 is already available, if not load it
        if (typeof Web3 === 'undefined') {
            // Load Web3 from CDN
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/web3@1.10.0/dist/web3.min.js';
            document.head.appendChild(script);
            
            // Wait for Web3 to load
            await new Promise((resolve) => {
                script.onload = resolve;
            });
        }
        
        // Initialize Web3
        this.web3 = new Web3(window.ethereum);
        
        // Request account access
        const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
        this.account = accounts[0];
        
        // Initialize contract
        this.contract = new this.web3.eth.Contract(this.contractABI, this.contractAddress);
        
        // Verify we're on BASE Sepolia
        const chainId = await this.web3.eth.getChainId();
        if (chainId !== 84532n) {
            await this.switchToBaseSepolia();
        }
        
        return this.account;
    }
    
    async switchToBaseSepolia() {
        try {
            await window.ethereum.request({
                method: 'wallet_switchEthereumChain',
                params: [{ chainId: '0x14a34' }] // 84532 in hex
            });
        } catch (error) {
            if (error.code === 4902) {
                // Chain not added, add it
                await window.ethereum.request({
                    method: 'wallet_addEthereumChain',
                    params: [{
                        chainId: '0x14a34',
                        chainName: 'Base Sepolia',
                        nativeCurrency: {
                            name: 'Ethereum',
                            symbol: 'ETH',
                            decimals: 18
                        },
                        rpcUrls: ['https://sepolia.base.org'],
                        blockExplorerUrls: ['https://sepolia.basescan.org/']
                    }]
                });
            } else {
                throw error;
            }
        }
    }
    
    async getMarketSubmissions(marketId) {
        try {
            const submissions = await this.contract.methods.getMarketSubmissions(marketId).call();
            return submissions;
        } catch (error) {
            console.error('Error fetching submissions:', error);
            return [];
        }
    }
    
    async checkDuplicate(marketId, predictedText) {
        try {
            const isDuplicate = await this.contract.methods.isDuplicateSubmission(marketId, predictedText).call();
            return isDuplicate;
        } catch (error) {
            console.error('Error checking duplicate:', error);
            // If the method doesn't exist, assume no duplicate
            return false;
        }
    }
    
    async submitNewPrediction(marketId, predictedText, amountETH) {
        // Check for duplicate
        const isDuplicate = await this.checkDuplicate(marketId, predictedText);
        if (isDuplicate) {
            throw new Error('This exact prediction already exists for this market. Please modify your text or bet on the existing submission.');
        }
        
        const amountWei = this.web3.utils.toWei(amountETH.toString(), 'ether');
        
        // Estimate gas
        const gasEstimate = await this.contract.methods
            .submitPrediction(marketId, predictedText)
            .estimateGas({ from: this.account, value: amountWei })
            .catch(() => 100000); // Fallback gas limit
        
        // Send transaction
        const tx = await this.contract.methods
            .submitPrediction(marketId, predictedText)
            .send({
                from: this.account,
                value: amountWei,
                gas: Math.floor(gasEstimate * 1.2) // Add 20% buffer
            });
        
        return tx;
    }
    
    async betOnExistingSubmission(marketId, submissionId, amountETH) {
        const amountWei = this.web3.utils.toWei(amountETH.toString(), 'ether');
        
        // Estimate gas
        const gasEstimate = await this.contract.methods
            .placeBet(marketId, submissionId)
            .estimateGas({ from: this.account, value: amountWei })
            .catch(() => 80000); // Fallback gas limit
        
        // Send transaction
        const tx = await this.contract.methods
            .placeBet(marketId, submissionId)
            .send({
                from: this.account,
                value: amountWei,
                gas: Math.floor(gasEstimate * 1.2) // Add 20% buffer
            });
        
        return tx;
    }
}

// Export for use in other scripts
window.BettingContract = BettingContract;