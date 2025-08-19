/**
 * Market Blockchain Integration for Clockchain
 * Handles direct blockchain queries for market data
 */

class MarketBlockchain {
    constructor() {
        this.contracts = {};
        this.abis = {};
        this.web3 = null;
        this.initialized = false;
        
        // Contract addresses from deployment-base-sepolia.json
        this.contractAddresses = {
            EnhancedPredictionMarket: '0x6B67Cb0DaAf78f63BD11195Df0FD9FFe4361b93C',
            ActorRegistry: '0xC71CC19C5573C5E1E144829800cD0005D0eDB723',
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
            
            if (typeof window.ethereum !== 'undefined') {
                this.web3 = new Web3(window.ethereum);
            } else {
                // Use read-only provider for BASE Sepolia
                this.web3 = new Web3('https://sepolia.base.org');
            }
            
            // Load contract ABIs
            await this.loadABIs();
            
            // Initialize contracts
            this.initializeContracts();
            
            this.initialized = true;
            console.log('MarketBlockchain initialized successfully');
            
        } catch (error) {
            console.error('Error initializing MarketBlockchain:', error);
        }
    }
    
    async loadABIs() {
        try {
            // Load EnhancedPredictionMarket ABI
            const response = await fetch('/api/contract-abi/EnhancedPredictionMarket');
            if (response.ok) {
                this.abis.EnhancedPredictionMarket = await response.json();
            }
        } catch (error) {
            console.error('Error loading ABIs:', error);
            // Fallback to minimal ABI
            this.abis.EnhancedPredictionMarket = [
                {
                    "inputs": [],
                    "name": "marketCount",
                    "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                    "stateMutability": "view",
                    "type": "function"
                },
                {
                    "inputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                    "name": "markets",
                    "outputs": [
                        {"internalType": "uint256", "name": "actorId", "type": "uint256"},
                        {"internalType": "uint256", "name": "startTime", "type": "uint256"},
                        {"internalType": "uint256", "name": "endTime", "type": "uint256"},
                        {"internalType": "uint256", "name": "submissionCount", "type": "uint256"},
                        {"internalType": "bool", "name": "resolved", "type": "bool"},
                        {"internalType": "uint256", "name": "totalPot", "type": "uint256"}
                    ],
                    "stateMutability": "view",
                    "type": "function"
                },
                {
                    "inputs": [
                        {"internalType": "uint256", "name": "", "type": "uint256"},
                        {"internalType": "uint256", "name": "", "type": "uint256"}
                    ],
                    "name": "submissions",
                    "outputs": [
                        {"internalType": "address", "name": "submitter", "type": "address"},
                        {"internalType": "string", "name": "predictedText", "type": "string"},
                        {"internalType": "uint256", "name": "submissionFee", "type": "uint256"},
                        {"internalType": "uint256", "name": "betAmount", "type": "uint256"},
                        {"internalType": "uint256", "name": "totalBetsOnThis", "type": "uint256"},
                        {"internalType": "bool", "name": "isWinner", "type": "bool"}
                    ],
                    "stateMutability": "view",
                    "type": "function"
                }
            ];
        }
    }
    
    initializeContracts() {
        // Initialize contract instances
        this.contracts.EnhancedPredictionMarket = new this.web3.eth.Contract(
            this.abis.EnhancedPredictionMarket,
            this.contractAddresses.EnhancedPredictionMarket
        );
    }
    
    async getActiveMarkets() {
        if (!this.initialized) {
            await this.waitForInitialization();
        }
        
        try {
            const currentTime = Math.floor(Date.now() / 1000);
            const marketCount = await this.contracts.EnhancedPredictionMarket.methods.marketCount().call();
            const markets = [];
            
            // Get last 50 markets (or less if fewer exist)
            const startIndex = Math.max(0, marketCount - 50);
            
            for (let i = startIndex; i < marketCount; i++) {
                const market = await this.contracts.EnhancedPredictionMarket.methods.markets(i).call();
                
                // Check if market is active (not resolved and end time is in future)
                if (!market.resolved && market.endTime > currentTime) {
                    markets.push({
                        id: i,
                        actorId: market.actorId,
                        startTime: new Date(market.startTime * 1000),
                        endTime: new Date(market.endTime * 1000),
                        submissionCount: market.submissionCount,
                        totalPot: this.web3.utils.fromWei(market.totalPot, 'ether'),
                        status: 'active'
                    });
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
            const markets = [];
            
            // Try to fetch up to 100 markets
            for (let i = 0; i < 100; i++) {
                try {
                    const market = await this.contracts.EnhancedPredictionMarket.methods.markets(i).call();
                    if (market && market.creator !== '0x0000000000000000000000000000000000000000') {
                        markets.push({
                            id: i,
                            creator: market.creator,
                            actorId: market.actorId,
                            startTime: new Date(market.startTime * 1000),
                            endTime: new Date(market.endTime * 1000),
                            totalPot: this.web3.utils.fromWei(market.totalPot || '0', 'ether'),
                            isResolved: market.resolved,
                            submissionCount: market.submissionCount || 0,
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
            const markets = [];
            
            // Try to fetch up to 100 markets and filter resolved ones
            for (let i = 0; i < 100; i++) {
                try {
                    const market = await this.contracts.EnhancedPredictionMarket.methods.markets(i).call();
                    if (market && market.resolved) {
                        markets.push({
                            id: i,
                            creator: market.creator,
                            actorId: market.actorId,
                            startTime: new Date(market.startTime * 1000),
                            endTime: new Date(market.endTime * 1000),
                            totalPot: this.web3.utils.fromWei(market.totalPot || '0', 'ether'),
                            isResolved: true,
                            submissionCount: market.submissionCount || 0,
                            winningSubmission: market.winningSubmission,
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
            const market = await this.contracts.EnhancedPredictionMarket.methods.markets(marketId).call();
            const submissions = [];
            
            // Get all submissions for this market
            for (let i = 0; i < market.submissionCount; i++) {
                const submission = await this.contracts.EnhancedPredictionMarket.methods
                    .submissions(marketId, i).call();
                    
                submissions.push({
                    id: i,
                    submitter: submission.submitter,
                    predictedText: submission.predictedText,
                    submissionFee: this.web3.utils.fromWei(submission.submissionFee, 'ether'),
                    betAmount: this.web3.utils.fromWei(submission.betAmount, 'ether'),
                    totalBetsOnThis: this.web3.utils.fromWei(submission.totalBetsOnThis, 'ether'),
                    isWinner: submission.isWinner
                });
            }
            
            return {
                id: marketId,
                actorId: market.actorId,
                startTime: new Date(market.startTime * 1000),
                endTime: new Date(market.endTime * 1000),
                submissionCount: market.submissionCount,
                resolved: market.resolved,
                totalPot: this.web3.utils.fromWei(market.totalPot, 'ether'),
                submissions: submissions
            };
            
        } catch (error) {
            console.error('Error fetching market details:', error);
            return null;
        }
    }
    
    async subscribeToMarketEvents(callback) {
        if (!this.initialized) {
            await this.waitForInitialization();
        }
        
        try {
            // Subscribe to MarketCreated events
            this.contracts.EnhancedPredictionMarket.events.MarketCreated({
                fromBlock: 'latest'
            })
            .on('data', event => {
                callback({
                    type: 'MarketCreated',
                    marketId: event.returnValues.marketId,
                    actorId: event.returnValues.actorId,
                    creator: event.returnValues.creator,
                    endTime: new Date(event.returnValues.endTime * 1000)
                });
            })
            .on('error', console.error);
            
            // Subscribe to SubmissionCreated events
            this.contracts.EnhancedPredictionMarket.events.SubmissionCreated({
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
            
            // Subscribe to BetPlaced events
            this.contracts.EnhancedPredictionMarket.events.BetPlaced({
                fromBlock: 'latest'
            })
            .on('data', event => {
                callback({
                    type: 'BetPlaced',
                    betId: event.returnValues.betId,
                    submissionId: event.returnValues.submissionId,
                    bettor: event.returnValues.bettor,
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
}

// Initialize on page load
let marketBlockchain;
document.addEventListener('DOMContentLoaded', () => {
    marketBlockchain = new MarketBlockchain();
    
    // Make it globally available
    window.marketBlockchain = marketBlockchain;
});