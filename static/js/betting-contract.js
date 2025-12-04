/**
 * Betting Contract Integration for PredictionMarketV2
 * Handles blockchain transactions for markets, submissions, and payouts
 * Uses PredictionMarketV2 contract with full resolution mechanism
 */

class BettingContract {
    constructor() {
        this.web3 = null;
        this.contract = null;
        this.account = null;

        // PredictionMarketV2 contract address on BASE Sepolia
        this.contractAddress = '0x5174Da96BCA87c78591038DEe9DB1811288c9286';

        // Contract ABI for PredictionMarketV2
        this.contractABI = [
            // Market creation
            {
                "inputs": [
                    {"internalType": "string", "name": "_actorHandle", "type": "string"},
                    {"internalType": "uint256", "name": "_duration", "type": "uint256"}
                ],
                "name": "createMarket",
                "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            // Submission creation
            {
                "inputs": [
                    {"internalType": "uint256", "name": "_marketId", "type": "uint256"},
                    {"internalType": "string", "name": "_predictedText", "type": "string"}
                ],
                "name": "createSubmission",
                "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                "stateMutability": "payable",
                "type": "function"
            },
            // Claim payout (NEW in V2)
            {
                "inputs": [
                    {"internalType": "uint256", "name": "_submissionId", "type": "uint256"}
                ],
                "name": "claimPayout",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            // Refund single submission
            {
                "inputs": [
                    {"internalType": "uint256", "name": "_marketId", "type": "uint256"}
                ],
                "name": "refundSingleSubmission",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            // View functions
            {
                "inputs": [{"internalType": "uint256", "name": "marketId", "type": "uint256"}],
                "name": "getMarketSubmissions",
                "outputs": [{"internalType": "uint256[]", "name": "", "type": "uint256[]"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "marketCount",
                "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "submissionCount",
                "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            },
            // Get market details
            {
                "inputs": [{"internalType": "uint256", "name": "_marketId", "type": "uint256"}],
                "name": "getMarketDetails",
                "outputs": [
                    {"internalType": "string", "name": "actorHandle", "type": "string"},
                    {"internalType": "uint256", "name": "endTime", "type": "uint256"},
                    {"internalType": "uint256", "name": "totalPool", "type": "uint256"},
                    {"internalType": "bool", "name": "resolved", "type": "bool"},
                    {"internalType": "uint256", "name": "winningSubmissionId", "type": "uint256"},
                    {"internalType": "address", "name": "creator", "type": "address"},
                    {"internalType": "uint256[]", "name": "submissionIds", "type": "uint256[]"}
                ],
                "stateMutability": "view",
                "type": "function"
            },
            // Get submission details
            {
                "inputs": [{"internalType": "uint256", "name": "_submissionId", "type": "uint256"}],
                "name": "getSubmissionDetails",
                "outputs": [
                    {"internalType": "uint256", "name": "marketId", "type": "uint256"},
                    {"internalType": "address", "name": "submitter", "type": "address"},
                    {"internalType": "string", "name": "predictedText", "type": "string"},
                    {"internalType": "uint256", "name": "amount", "type": "uint256"},
                    {"internalType": "bool", "name": "claimed", "type": "bool"}
                ],
                "stateMutability": "view",
                "type": "function"
            },
            // Constants
            {
                "inputs": [],
                "name": "MIN_BET",
                "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "MAX_TEXT_LENGTH",
                "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "PLATFORM_FEE_BPS",
                "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "BETTING_CUTOFF",
                "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            },
            // Market resolution (owner only)
            {
                "inputs": [
                    {"internalType": "uint256", "name": "_marketId", "type": "uint256"},
                    {"internalType": "string", "name": "_actualText", "type": "string"}
                ],
                "name": "resolveMarket",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            // Contract owner
            {
                "inputs": [],
                "name": "owner",
                "outputs": [{"internalType": "address", "name": "", "type": "address"}],
                "stateMutability": "view",
                "type": "function"
            }
        ];
    }

    async init() {
        // Check if wallet is connected
        if (!window.clockchainWallet || !window.clockchainWallet.isConnected) {
            throw new Error('Please connect your wallet first');
        }

        // Get wallet adapter (works with both MetaMask and Coinbase)
        const wallet = window.clockchainWallet;
        const provider = wallet.adapter || wallet.provider || window.ethereum;

        if (!provider) {
            throw new Error('No wallet provider available');
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

        // Initialize Web3 with wallet adapter
        this.web3 = new Web3(provider);

        // Get account from connected wallet
        this.account = wallet.address;

        if (!this.account) {
            // Try to get accounts through provider
            const accounts = await provider.request({ method: 'eth_requestAccounts' });
            this.account = accounts[0];
        }

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
            // Use wallet adapter if available
            const wallet = window.clockchainWallet;
            const provider = wallet?.adapter || wallet?.provider || window.ethereum;

            await provider.request({
                method: 'wallet_switchEthereumChain',
                params: [{ chainId: '0x14a34' }] // 84532 in hex
            });
        } catch (error) {
            if (error.code === 4902 && window.ethereum) {
                // Chain not added, add it (MetaMask only)
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
            const submissionIds = await this.contract.methods.getMarketSubmissions(marketId).call();
            const submissions = [];

            for (const subId of submissionIds) {
                const submission = await this.contract.methods.getSubmissionDetails(subId).call();
                submissions.push({
                    id: parseInt(subId),
                    marketId: parseInt(submission.marketId),
                    submitter: submission.submitter,
                    predictedText: submission.predictedText,
                    amount: this.web3.utils.fromWei(submission.amount, 'ether'),
                    claimed: submission.claimed
                });
            }

            return submissions;
        } catch (error) {
            console.error('Error fetching submissions:', error);
            return [];
        }
    }

    async checkDuplicate(marketId, predictedText) {
        try {
            // Get existing submissions for this market
            const submissions = await this.getMarketSubmissions(marketId);

            // Check if any submission has the same predicted text
            return submissions.some(sub =>
                sub.predictedText.toLowerCase().trim() === predictedText.toLowerCase().trim()
            );
        } catch (error) {
            console.error('Error checking duplicate:', error);
            return false;
        }
    }

    async submitNewPrediction(marketId, predictedText, amountETH) {
        // Check max text length
        const maxLength = await this.contract.methods.MAX_TEXT_LENGTH().call();
        if (predictedText.length > parseInt(maxLength)) {
            throw new Error(`Prediction text exceeds maximum length of ${maxLength} characters`);
        }

        // Check for duplicate
        const isDuplicate = await this.checkDuplicate(marketId, predictedText);
        if (isDuplicate) {
            throw new Error('This exact prediction already exists for this market. Please modify your text.');
        }

        // Check minimum bet
        const minBet = await this.contract.methods.MIN_BET().call();
        const amountWei = this.web3.utils.toWei(amountETH.toString(), 'ether');
        if (BigInt(amountWei) < BigInt(minBet)) {
            throw new Error(`Minimum bet is ${this.web3.utils.fromWei(minBet, 'ether')} ETH`);
        }

        // Estimate gas
        const gasEstimate = await this.contract.methods
            .createSubmission(marketId, predictedText)
            .estimateGas({ from: this.account, value: amountWei })
            .catch(() => 300000); // Fallback gas limit

        // Send transaction with BASE Sepolia gas settings
        const tx = await this.contract.methods
            .createSubmission(marketId, predictedText)
            .send({
                from: this.account,
                value: amountWei,
                gas: Math.min(Math.floor(Number(gasEstimate) * 1.2), 400000),
                gasPrice: '1000000000' // 1 gwei for BASE Sepolia
            });

        return tx;
    }

    async createMarket(actorHandle, durationHours) {
        // V2 createMarket is NOT payable - just creates the market structure
        const durationSeconds = durationHours * 3600;

        // Estimate gas
        const gasEstimate = await this.contract.methods
            .createMarket(actorHandle, durationSeconds)
            .estimateGas({ from: this.account })
            .catch(() => 200000); // Fallback gas limit

        // Send transaction
        const tx = await this.contract.methods
            .createMarket(actorHandle, durationSeconds)
            .send({
                from: this.account,
                gas: Math.min(Math.floor(Number(gasEstimate) * 1.2), 300000),
                gasPrice: '1000000000' // 1 gwei for BASE Sepolia
            });

        return tx;
    }

    async claimPayout(submissionId) {
        // Estimate gas
        const gasEstimate = await this.contract.methods
            .claimPayout(submissionId)
            .estimateGas({ from: this.account })
            .catch(() => 150000); // Fallback gas limit

        // Send transaction
        const tx = await this.contract.methods
            .claimPayout(submissionId)
            .send({
                from: this.account,
                gas: Math.min(Math.floor(Number(gasEstimate) * 1.2), 200000),
                gasPrice: '1000000000'
            });

        return tx;
    }

    async refundSingleSubmission(marketId) {
        // For markets with only 1 submission after end time
        const gasEstimate = await this.contract.methods
            .refundSingleSubmission(marketId)
            .estimateGas({ from: this.account })
            .catch(() => 150000);

        const tx = await this.contract.methods
            .refundSingleSubmission(marketId)
            .send({
                from: this.account,
                gas: Math.min(Math.floor(Number(gasEstimate) * 1.2), 200000),
                gasPrice: '1000000000'
            });

        return tx;
    }

    async resolveMarket(marketId, actualText) {
        // Only contract owner can resolve
        const owner = await this.contract.methods.owner().call();
        if (this.account.toLowerCase() !== owner.toLowerCase()) {
            throw new Error('Only contract owner can resolve markets');
        }

        // Estimate gas - Levenshtein can be expensive
        const gasEstimate = await this.contract.methods
            .resolveMarket(marketId, actualText)
            .estimateGas({ from: this.account })
            .catch(() => 2000000); // Higher fallback for Levenshtein

        const tx = await this.contract.methods
            .resolveMarket(marketId, actualText)
            .send({
                from: this.account,
                gas: Math.min(Math.floor(Number(gasEstimate) * 1.3), 5000000), // Extra buffer
                gasPrice: '1000000000'
            });

        return tx;
    }

    async getContractConstants() {
        return {
            minBet: this.web3.utils.fromWei(
                await this.contract.methods.MIN_BET().call(), 'ether'
            ),
            maxTextLength: parseInt(await this.contract.methods.MAX_TEXT_LENGTH().call()),
            platformFeeBps: parseInt(await this.contract.methods.PLATFORM_FEE_BPS().call()),
            bettingCutoff: parseInt(await this.contract.methods.BETTING_CUTOFF().call())
        };
    }

    async isContractOwner() {
        const owner = await this.contract.methods.owner().call();
        return this.account.toLowerCase() === owner.toLowerCase();
    }

    // Helper to get contract address
    getContractAddress() {
        return this.contractAddress;
    }
}

// Export for use in other scripts
window.BettingContract = BettingContract;
