/**
 * Market Blockchain Integration for Proteus Markets
 * Handles direct blockchain queries for market data
 * Uses PredictionMarketV2 contract with full resolution mechanism
 */

class MarketBlockchain {
    constructor() {
        this.contracts = {};
        this.abis = {};
        this.web3 = null;
        this.initialized = false;

        // Contract addresses from deployment-base-sepolia.json
        // Using PredictionMarketV2 - full resolution mechanism
        this.contractAddresses = {
            PredictionMarketV2: '0x5174Da96BCA87c78591038DEe9DB1811288c9286',
            GenesisNFT: '0x1A5D4475881B93e876251303757E60E524286A24',
            DecentralizedOracle: '0x7EF22e27D44E3f4Cc2f133BB4ab2065D180be3C1',
            PayoutManager: '0x88d399C949Ff2f1aaa8eA5a859Ae4d97c74f6871'
        };

        this.init();
    }

    async init() {
        try {
            // Skip initialization on market detail page
            if (window.isMarketDetailPage) {
                console.log('Skipping MarketBlockchain init on market detail page');
                return;
            }

            // Initialize Web3 - check if it's loaded first
            if (typeof Web3 === 'undefined') {
                console.error('Web3 library not loaded. Please ensure Web3.js is included.');
                return;
            }

            // Use wallet provider if available, otherwise use read-only provider
            if (window.proteusWallet && window.proteusWallet.provider) {
                this.web3 = new Web3(window.proteusWallet.provider);
            } else {
                // Use read-only provider for BASE Sepolia (for querying without wallet)
                this.web3 = new Web3('https://sepolia.base.org');
                console.log('Using read-only RPC provider');
            }

            // Load contract ABIs
            await this.loadABIs();

            // Initialize contracts
            this.initializeContracts();

            this.initialized = true;
            console.log('MarketBlockchain initialized successfully with PredictionMarketV2');

        } catch (error) {
            console.error('Error initializing MarketBlockchain:', error);
        }
    }

    async loadABIs() {
        try {
            // Try to load from API endpoint
            const response = await fetch('/api/contract-abi/PredictionMarketV2');
            if (response.ok) {
                this.abis.PredictionMarketV2 = await response.json();
            }
        } catch (error) {
            console.error('Error loading ABIs from API:', error);
        }

        // Fallback to minimal ABI for PredictionMarketV2
        if (!this.abis.PredictionMarketV2) {
            this.abis.PredictionMarketV2 = [
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
                {
                    "inputs": [{"internalType": "uint256", "name": "marketId", "type": "uint256"}],
                    "name": "getMarketSubmissions",
                    "outputs": [{"internalType": "uint256[]", "name": "", "type": "uint256[]"}],
                    "stateMutability": "view",
                    "type": "function"
                },
                {
                    "inputs": [],
                    "name": "MIN_BET",
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
                {
                    "inputs": [],
                    "name": "owner",
                    "outputs": [{"internalType": "address", "name": "", "type": "address"}],
                    "stateMutability": "view",
                    "type": "function"
                }
            ];
        }
    }

    initializeContracts() {
        // Initialize PredictionMarketV2 contract instance
        this.contracts.PredictionMarketV2 = new this.web3.eth.Contract(
            this.abis.PredictionMarketV2,
            this.contractAddresses.PredictionMarketV2
        );
    }

    async getMarketCount() {
        if (!this.initialized) {
            await this.waitForInitialization();
        }

        try {
            return await this.contracts.PredictionMarketV2.methods.marketCount().call();
        } catch (error) {
            console.error('Error getting market count:', error);
            return 0;
        }
    }

    async getActiveMarkets() {
        if (!this.initialized) {
            await this.waitForInitialization();
        }

        try {
            const currentTime = Math.floor(Date.now() / 1000);
            const marketCount = await this.contracts.PredictionMarketV2.methods.marketCount().call();
            const markets = [];

            // Get last 20 markets (or less if fewer exist)
            const startIndex = Math.max(0, parseInt(marketCount) - 20);

            for (let i = startIndex; i < parseInt(marketCount); i++) {
                try {
                    const market = await this.contracts.PredictionMarketV2.methods.getMarketDetails(i).call();

                    // Check if market is active (not resolved and end time is in future)
                    if (!market.resolved && parseInt(market.endTime) > currentTime) {
                        markets.push({
                            id: i,
                            actorHandle: market.actorHandle,
                            creator: market.creator,
                            endTime: new Date(parseInt(market.endTime) * 1000),
                            submissionCount: market.submissionIds.length,
                            totalPool: this.web3.utils.fromWei(market.totalPool, 'ether'),
                            resolved: false,
                            status: 'active'
                        });
                    }
                } catch (e) {
                    console.debug(`Market ${i} not found or invalid`);
                }
            }

            return markets.reverse(); // Show newest first

        } catch (error) {
            console.error('Error fetching active markets:', error);
            return [];
        }
    }

    async getAllMarkets() {
        if (!this.initialized) {
            await this.waitForInitialization();
        }

        try {
            const marketCount = await this.contracts.PredictionMarketV2.methods.marketCount().call();
            const markets = [];

            // Limit to 20 markets to avoid excessive blockchain calls
            const limit = Math.min(parseInt(marketCount), 20);

            for (let i = 0; i < limit; i++) {
                try {
                    const market = await this.contracts.PredictionMarketV2.methods.getMarketDetails(i).call();

                    if (market && market.creator !== '0x0000000000000000000000000000000000000000') {
                        markets.push({
                            id: i,
                            actorHandle: market.actorHandle,
                            creator: market.creator,
                            endTime: new Date(parseInt(market.endTime) * 1000),
                            totalPool: this.web3.utils.fromWei(market.totalPool || '0', 'ether'),
                            resolved: market.resolved,
                            winningSubmissionId: parseInt(market.winningSubmissionId),
                            submissionCount: market.submissionIds.length,
                            status: market.resolved ? 'resolved' : 'active'
                        });
                    }
                } catch (error) {
                    // Market doesn't exist, stop trying
                    if (error.message && error.message.includes('revert')) {
                        break;
                    }
                }
            }

            return markets;
        } catch (error) {
            console.error('Error fetching all markets:', error);
            return [];
        }
    }

    async getResolvedMarkets() {
        if (!this.initialized) {
            await this.waitForInitialization();
        }

        try {
            const marketCount = await this.contracts.PredictionMarketV2.methods.marketCount().call();
            const markets = [];

            // Limit to 20 markets to avoid excessive blockchain calls
            const limit = Math.min(parseInt(marketCount), 20);

            for (let i = 0; i < limit; i++) {
                try {
                    const market = await this.contracts.PredictionMarketV2.methods.getMarketDetails(i).call();

                    if (market && market.resolved) {
                        markets.push({
                            id: i,
                            actorHandle: market.actorHandle,
                            creator: market.creator,
                            endTime: new Date(parseInt(market.endTime) * 1000),
                            totalPool: this.web3.utils.fromWei(market.totalPool || '0', 'ether'),
                            resolved: true,
                            winningSubmissionId: parseInt(market.winningSubmissionId),
                            submissionCount: market.submissionIds.length,
                            status: 'resolved'
                        });
                    }
                } catch (error) {
                    // Market doesn't exist, stop trying
                    if (error.message && error.message.includes('revert')) {
                        break;
                    }
                }
            }

            return markets;
        } catch (error) {
            console.error('Error fetching resolved markets:', error);
            return [];
        }
    }

    async getMarketDetails(marketId) {
        if (!this.initialized) {
            await this.waitForInitialization();
        }

        try {
            const market = await this.contracts.PredictionMarketV2.methods.getMarketDetails(marketId).call();
            const submissions = [];

            // Get all submissions for this market
            for (const subId of market.submissionIds) {
                try {
                    const submission = await this.contracts.PredictionMarketV2.methods.getSubmissionDetails(subId).call();

                    submissions.push({
                        id: parseInt(subId),
                        marketId: parseInt(submission.marketId),
                        submitter: submission.submitter,
                        predictedText: submission.predictedText,
                        amount: this.web3.utils.fromWei(submission.amount, 'ether'),
                        claimed: submission.claimed,
                        isWinner: market.resolved && parseInt(market.winningSubmissionId) === parseInt(subId)
                    });
                } catch (e) {
                    console.debug(`Submission ${subId} not found`);
                }
            }

            return {
                id: marketId,
                actorHandle: market.actorHandle,
                creator: market.creator,
                endTime: new Date(parseInt(market.endTime) * 1000),
                submissionCount: submissions.length,
                resolved: market.resolved,
                winningSubmissionId: parseInt(market.winningSubmissionId),
                totalPool: this.web3.utils.fromWei(market.totalPool, 'ether'),
                submissions: submissions
            };

        } catch (error) {
            console.error('Error fetching market details:', error);
            return null;
        }
    }

    async getSubmission(submissionId) {
        if (!this.initialized) {
            await this.waitForInitialization();
        }

        try {
            const submission = await this.contracts.PredictionMarketV2.methods.getSubmissionDetails(submissionId).call();

            return {
                id: submissionId,
                marketId: parseInt(submission.marketId),
                submitter: submission.submitter,
                predictedText: submission.predictedText,
                amount: this.web3.utils.fromWei(submission.amount, 'ether'),
                claimed: submission.claimed
            };
        } catch (error) {
            console.error('Error fetching submission:', error);
            return null;
        }
    }

    async subscribeToMarketEvents(callback) {
        if (!this.initialized) {
            await this.waitForInitialization();
        }

        try {
            // Subscribe to MarketCreated events
            this.contracts.PredictionMarketV2.events.MarketCreated({
                fromBlock: 'latest'
            })
            .on('data', event => {
                callback({
                    type: 'MarketCreated',
                    marketId: event.returnValues.marketId,
                    creator: event.returnValues.creator,
                    actorHandle: event.returnValues.actorHandle,
                    endTime: new Date(parseInt(event.returnValues.endTime) * 1000)
                });
            })
            .on('error', console.error);

            // Subscribe to SubmissionCreated events
            this.contracts.PredictionMarketV2.events.SubmissionCreated({
                fromBlock: 'latest'
            })
            .on('data', event => {
                callback({
                    type: 'SubmissionCreated',
                    marketId: event.returnValues.marketId,
                    submissionId: event.returnValues.submissionId,
                    submitter: event.returnValues.submitter,
                    predictedText: event.returnValues.predictedText
                });
            })
            .on('error', console.error);

            // Subscribe to MarketResolved events
            this.contracts.PredictionMarketV2.events.MarketResolved({
                fromBlock: 'latest'
            })
            .on('data', event => {
                callback({
                    type: 'MarketResolved',
                    marketId: event.returnValues.marketId,
                    winningSubmissionId: event.returnValues.winningSubmissionId,
                    actualText: event.returnValues.actualText
                });
            })
            .on('error', console.error);

            // Subscribe to PayoutClaimed events
            this.contracts.PredictionMarketV2.events.PayoutClaimed({
                fromBlock: 'latest'
            })
            .on('data', event => {
                callback({
                    type: 'PayoutClaimed',
                    submissionId: event.returnValues.submissionId,
                    claimer: event.returnValues.claimer,
                    amount: this.web3.utils.fromWei(event.returnValues.amount, 'ether')
                });
            })
            .on('error', console.error);

        } catch (error) {
            console.error('Error subscribing to events:', error);
        }
    }

    async waitForInitialization() {
        const maxAttempts = 50; // 5 seconds
        let attempts = 0;

        while (!this.initialized && attempts < maxAttempts) {
            await new Promise(resolve => setTimeout(resolve, 100));
            attempts++;
        }

        if (!this.initialized) {
            throw new Error('MarketBlockchain initialization timeout');
        }
    }

    formatAddress(address) {
        return address.substring(0, 6) + '...' + address.substring(38);
    }

    // Helper to get contract address
    getContractAddress() {
        return this.contractAddresses.PredictionMarketV2;
    }
}

// Initialize on page load
let marketBlockchain;
document.addEventListener('DOMContentLoaded', () => {
    marketBlockchain = new MarketBlockchain();

    // Make it globally available
    window.marketBlockchain = marketBlockchain;
});
