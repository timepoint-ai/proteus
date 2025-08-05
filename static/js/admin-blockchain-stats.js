/**
 * Admin Dashboard Blockchain Statistics
 * Fetches and displays real-time contract statistics
 */

class AdminBlockchainStats {
    constructor() {
        this.stats = {
            totalMarkets: 0,
            activeMarkets: 0,
            totalVolume: '0',
            totalSubmissions: 0,
            totalBets: 0,
            contractBalances: {},
            gasPrice: '0',
            blockNumber: 0
        };
        
        this.init();
    }
    
    async init() {
        try {
            // Wait for blockchain connection
            await this.waitForBlockchain();
            
            // Initial stats load
            await this.loadStatistics();
            
            // Display stats
            this.displayStatistics();
            
            // Start periodic updates
            this.startPeriodicUpdates();
            
            // Subscribe to events
            this.subscribeToEvents();
            
        } catch (error) {
            console.error('Failed to initialize admin blockchain stats:', error);
        }
    }
    
    async waitForBlockchain() {
        const maxAttempts = 50;
        let attempts = 0;
        
        while (attempts < maxAttempts) {
            if (window.marketBlockchain?.initialized) {
                return;
            }
            await new Promise(resolve => setTimeout(resolve, 100));
            attempts++;
        }
        
        throw new Error('Blockchain connection timeout');
    }
    
    async loadStatistics() {
        try {
            const web3 = window.marketBlockchain.web3;
            const contract = window.marketBlockchain.contracts.EnhancedPredictionMarket;
            
            // Get market count
            this.stats.totalMarkets = await contract.methods.marketCount().call();
            
            // Get current block and gas price
            this.stats.blockNumber = await web3.eth.getBlockNumber();
            this.stats.gasPrice = await web3.eth.getGasPrice();
            
            // Calculate active markets and total volume
            let activeCount = 0;
            let totalVolume = BigInt(0);
            let totalSubmissions = 0;
            
            const currentTime = Math.floor(Date.now() / 1000);
            
            for (let i = 0; i < this.stats.totalMarkets; i++) {
                const market = await contract.methods.markets(i).call();
                
                if (!market.resolved && market.endTime > currentTime) {
                    activeCount++;
                }
                
                totalVolume += BigInt(market.totalPot);
                totalSubmissions += parseInt(market.submissionCount);
            }
            
            this.stats.activeMarkets = activeCount;
            this.stats.totalVolume = web3.utils.fromWei(totalVolume.toString(), 'ether');
            this.stats.totalSubmissions = totalSubmissions;
            
            // Get contract balances
            const contracts = window.marketBlockchain.contractAddresses;
            for (const [name, address] of Object.entries(contracts)) {
                const balance = await web3.eth.getBalance(address);
                this.stats.contractBalances[name] = web3.utils.fromWei(balance, 'ether');
            }
            
        } catch (error) {
            console.error('Error loading blockchain statistics:', error);
        }
    }
    
    displayStatistics() {
        // Update blockchain stats card
        this.updateStatsCard();
        
        // Update contract balances
        this.updateContractBalances();
        
        // Update network info
        this.updateNetworkInfo();
    }
    
    updateStatsCard() {
        const statsHtml = `
            <div class="row">
                <div class="col-md-3">
                    <div class="stat-item">
                        <h6 class="text-muted">Total Markets</h6>
                        <h3 class="text-primary">${this.stats.totalMarkets}</h3>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-item">
                        <h6 class="text-muted">Active Markets</h6>
                        <h3 class="text-success">${this.stats.activeMarkets}</h3>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-item">
                        <h6 class="text-muted">Total Volume</h6>
                        <h3 class="text-info">${parseFloat(this.stats.totalVolume).toFixed(4)} ETH</h3>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-item">
                        <h6 class="text-muted">Total Submissions</h6>
                        <h3 class="text-warning">${this.stats.totalSubmissions}</h3>
                    </div>
                </div>
            </div>
        `;
        
        // Find or create blockchain stats card
        let statsCard = document.getElementById('blockchain-stats-card');
        if (!statsCard) {
            statsCard = document.createElement('div');
            statsCard.id = 'blockchain-stats-card';
            statsCard.className = 'card mb-4';
            statsCard.innerHTML = `
                <div class="card-header">
                    <h5 class="card-title mb-0">
                        <i class="fas fa-link me-2"></i>
                        Blockchain Statistics
                    </h5>
                </div>
                <div class="card-body" id="blockchain-stats-content">
                </div>
            `;
            
            // Insert after page header
            const dashboard = document.querySelector('.container-fluid');
            if (dashboard) {
                const firstCard = dashboard.querySelector('.card');
                dashboard.insertBefore(statsCard, firstCard);
            }
        }
        
        const content = document.getElementById('blockchain-stats-content');
        if (content) {
            content.innerHTML = statsHtml;
        }
    }
    
    updateContractBalances() {
        const balancesHtml = `
            <table class="table table-sm">
                <thead>
                    <tr>
                        <th>Contract</th>
                        <th>Balance (ETH)</th>
                    </tr>
                </thead>
                <tbody>
                    ${Object.entries(this.stats.contractBalances).map(([name, balance]) => `
                        <tr>
                            <td>${name}</td>
                            <td>${parseFloat(balance).toFixed(6)}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
        
        // Find or create contract balances card
        let balancesCard = document.getElementById('contract-balances-card');
        if (!balancesCard) {
            balancesCard = document.createElement('div');
            balancesCard.id = 'contract-balances-card';
            balancesCard.className = 'card mb-4';
            balancesCard.innerHTML = `
                <div class="card-header">
                    <h5 class="card-title mb-0">
                        <i class="fas fa-wallet me-2"></i>
                        Contract Balances
                    </h5>
                </div>
                <div class="card-body" id="contract-balances-content">
                </div>
            `;
            
            // Add after blockchain stats
            const statsCard = document.getElementById('blockchain-stats-card');
            if (statsCard) {
                statsCard.insertAdjacentElement('afterend', balancesCard);
            }
        }
        
        const content = document.getElementById('contract-balances-content');
        if (content) {
            content.innerHTML = balancesHtml;
        }
    }
    
    updateNetworkInfo() {
        const gasInGwei = (parseFloat(this.stats.gasPrice) / 1e9).toFixed(2);
        
        const networkHtml = `
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <i class="fas fa-cube me-2"></i>
                    Block: #${this.stats.blockNumber.toLocaleString()}
                </div>
                <div>
                    <i class="fas fa-gas-pump me-2"></i>
                    Gas: ${gasInGwei} gwei
                </div>
                <div>
                    <i class="fas fa-network-wired me-2"></i>
                    Network: BASE Sepolia
                </div>
                <div class="text-muted">
                    <i class="fas fa-sync-alt me-1"></i>
                    Last update: ${new Date().toLocaleTimeString()}
                </div>
            </div>
        `;
        
        // Update network info bar
        let networkBar = document.getElementById('network-info-bar');
        if (!networkBar) {
            networkBar = document.createElement('div');
            networkBar.id = 'network-info-bar';
            networkBar.className = 'alert alert-info mb-4';
            
            const dashboard = document.querySelector('.container-fluid');
            if (dashboard) {
                dashboard.insertBefore(networkBar, dashboard.firstChild);
            }
        }
        
        networkBar.innerHTML = networkHtml;
    }
    
    startPeriodicUpdates() {
        // Update every 30 seconds
        setInterval(async () => {
            await this.loadStatistics();
            this.displayStatistics();
        }, 30000);
    }
    
    subscribeToEvents() {
        if (!window.marketBlockchain) return;
        
        window.marketBlockchain.subscribeToMarketEvents((event) => {
            // Show real-time notification
            this.showEventNotification(event);
            
            // Update stats after event
            setTimeout(async () => {
                await this.loadStatistics();
                this.displayStatistics();
            }, 2000);
        });
    }
    
    showEventNotification(event) {
        let message = '';
        let icon = 'fas fa-bell';
        
        switch(event.type) {
            case 'MarketCreated':
                message = `New market created! ID: ${event.marketId}`;
                icon = 'fas fa-plus-circle';
                break;
            case 'SubmissionCreated':
                message = `New submission in market #${event.marketId}`;
                icon = 'fas fa-file-alt';
                break;
            case 'BetPlaced':
                message = `New bet placed: ${event.amount} ETH`;
                icon = 'fas fa-coins';
                break;
        }
        
        if (message) {
            const notification = document.createElement('div');
            notification.className = 'alert alert-success alert-dismissible fade show position-fixed';
            notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
            notification.innerHTML = `
                <i class="${icon} me-2"></i>
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            
            document.body.appendChild(notification);
            
            setTimeout(() => notification.remove(), 5000);
        }
    }
}

// Initialize on admin pages
document.addEventListener('DOMContentLoaded', () => {
    if (window.location.pathname.includes('/admin')) {
        window.adminBlockchainStats = new AdminBlockchainStats();
    }
});