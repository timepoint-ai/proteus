/**
 * Market Detail Blockchain Integration
 * Handles MetaMask transactions for submissions and bets
 */

class MarketDetailBlockchain {
    constructor(marketId) {
        this.marketId = marketId;
        this.marketData = null;
        this.initialized = false;
        
        this.init();
    }
    
    async init() {
        try {
            // Wait for wallet and blockchain to be ready
            await this.waitForDependencies();
            
            // Load market data from blockchain
            await this.loadMarketData();
            
            // Update UI with blockchain data
            this.updateUI();
            
            // Setup event listeners
            this.setupEventListeners();
            
            this.initialized = true;
            
        } catch (error) {
            console.error('Error initializing market detail:', error);
            this.showError('Failed to load market data from blockchain');
        }
    }
    
    async waitForDependencies() {
        const maxAttempts = 50;
        let attempts = 0;
        
        while (attempts < maxAttempts) {
            if (window.clockchainWallet && window.marketBlockchain?.initialized) {
                return;
            }
            await new Promise(resolve => setTimeout(resolve, 100));
            attempts++;
        }
        
        throw new Error('Dependencies not loaded');
    }
    
    async loadMarketData() {
        this.marketData = await window.marketBlockchain.getMarketDetails(this.marketId);
        
        if (!this.marketData) {
            throw new Error('Market not found on blockchain');
        }
    }
    
    updateUI() {
        // Update market statistics from blockchain
        const statsContainer = document.querySelector('.market-statistics');
        if (statsContainer) {
            statsContainer.innerHTML = `
                <p class="text-muted">
                    <strong>Total Pot:</strong> ${this.marketData.totalPot} ETH<br>
                    <strong>Submissions:</strong> ${this.marketData.submissionCount}<br>
                    <strong>Status:</strong> ${this.marketData.resolved ? 'Resolved' : 'Active'}
                </p>
            `;
        }
        
        // Add submission form if market is active
        if (!this.marketData.resolved && this.marketData.endTime > Date.now()) {
            this.addSubmissionForm();
        }
        
        // Update submissions display
        this.updateSubmissionsDisplay();
    }
    
    addSubmissionForm() {
        const submissionsCard = document.querySelector('.card-body');
        if (!submissionsCard) return;
        
        const formHtml = `
            <div class="submission-form mb-4 p-3 bg-dark rounded">
                <h6 class="text-primary mb-3">
                    <i class="fas fa-plus-circle me-2"></i>
                    Create New Submission
                </h6>
                <form id="blockchain-submission-form">
                    <div class="mb-3">
                        <label for="predicted-text" class="form-label">Predicted Text</label>
                        <textarea class="form-control" id="predicted-text" rows="3" 
                                  placeholder="Enter the exact text you predict will be said..." required></textarea>
                        <small class="text-muted">This should be the exact phrase you expect the actor to say</small>
                    </div>
                    <div class="mb-3">
                        <label for="submission-fee" class="form-label">Submission Fee (ETH)</label>
                        <input type="number" class="form-control" id="submission-fee" 
                               step="0.001" min="0.001" placeholder="0.01" required>
                        <small class="text-muted">Minimum: 0.001 ETH</small>
                    </div>
                    <div class="mb-3">
                        <label for="initial-bet" class="form-label">Initial Bet Amount (ETH)</label>
                        <input type="number" class="form-control" id="initial-bet" 
                               step="0.001" min="0.001" placeholder="0.05" required>
                        <small class="text-muted">Your initial stake on this prediction</small>
                    </div>
                    <button type="submit" class="btn btn-primary" id="submit-prediction-btn">
                        <i class="fas fa-rocket me-2"></i>
                        Submit Prediction
                    </button>
                </form>
            </div>
        `;
        
        // Insert before the submissions table
        const submissionsContainer = document.querySelector('.table-responsive')?.parentElement;
        if (submissionsContainer) {
            submissionsContainer.insertAdjacentHTML('afterbegin', formHtml);
        }
    }
    
    updateSubmissionsDisplay() {
        if (!this.marketData.submissions || this.marketData.submissions.length === 0) {
            return;
        }
        
        const tbody = document.querySelector('.table tbody');
        if (!tbody) return;
        
        // Clear existing rows
        tbody.innerHTML = '';
        
        // Add submission rows with bet buttons
        this.marketData.submissions.forEach((submission, index) => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>
                    <span class="badge bg-primary">On-Chain</span>
                </td>
                <td>
                    <div style="max-width: 300px; word-wrap: break-word;">
                        "${submission.predictedText}"
                    </div>
                </td>
                <td>
                    <small class="text-muted font-monospace">
                        ${window.marketBlockchain.formatAddress(submission.submitter)}
                    </small>
                </td>
                <td>
                    <strong>${submission.submissionFee} ETH</strong>
                </td>
                <td>
                    <strong>${submission.totalBetsOnThis} ETH</strong>
                </td>
                <td>
                    ${submission.betAmount} ETH
                </td>
                <td>
                    ${this.marketData.resolved ? 
                        (submission.isWinner ? 
                            '<span class="badge bg-success">Winner</span>' : 
                            '<span class="badge bg-danger">Lost</span>') :
                        `<button class="btn btn-sm btn-outline-primary bet-btn" 
                                data-submission-id="${index}">
                            <i class="fas fa-coins me-1"></i> Bet
                        </button>`
                    }
                </td>
            `;
            tbody.appendChild(row);
        });
    }
    
    setupEventListeners() {
        // Submission form handler
        const submissionForm = document.getElementById('blockchain-submission-form');
        if (submissionForm) {
            submissionForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                await this.handleSubmissionCreate();
            });
        }
        
        // Bet button handlers
        document.addEventListener('click', async (e) => {
            if (e.target.classList.contains('bet-btn') || e.target.parentElement?.classList.contains('bet-btn')) {
                const btn = e.target.classList.contains('bet-btn') ? e.target : e.target.parentElement;
                const submissionId = btn.dataset.submissionId;
                await this.handleBetPlace(submissionId);
            }
        });
    }
    
    async handleSubmissionCreate() {
        try {
            // Check wallet connection
            if (!window.clockchainWallet?.isConnected) {
                await window.clockchainWallet.connect();
            }
            
            const predictedText = document.getElementById('predicted-text').value;
            const submissionFee = document.getElementById('submission-fee').value;
            const initialBet = document.getElementById('initial-bet').value;
            
            // Validate inputs
            if (!predictedText || !submissionFee || !initialBet) {
                throw new Error('Please fill all fields');
            }
            
            // Show loading
            this.showLoading('Creating submission on blockchain...');
            
            // Prepare transaction
            const totalAmount = parseFloat(submissionFee) + parseFloat(initialBet);
            const txParams = {
                from: window.clockchainWallet.address,
                to: window.marketBlockchain.contractAddresses.EnhancedPredictionMarket,
                value: '0x' + (totalAmount * 1e18).toString(16),
                data: this.encodeSubmissionData(predictedText, submissionFee, initialBet)
            };
            
            // Send transaction
            const txHash = await window.clockchainWallet.sendTransaction(txParams);
            
            // Show pending notification
            this.showTransactionPending(txHash);
            
            // Wait for confirmation
            await this.waitForTransaction(txHash);
            
            this.hideLoading();
            this.showSuccess('Submission created successfully!');
            
            // Reload market data
            setTimeout(() => {
                this.loadMarketData().then(() => this.updateUI());
            }, 2000);
            
        } catch (error) {
            this.hideLoading();
            this.showError(error.message);
        }
    }
    
    async handleBetPlace(submissionId) {
        try {
            // Check wallet connection
            if (!window.clockchainWallet?.isConnected) {
                await window.clockchainWallet.connect();
            }
            
            // Show bet amount modal
            const betAmount = await this.showBetModal();
            if (!betAmount) return;
            
            // Show loading
            this.showLoading('Placing bet on blockchain...');
            
            // Calculate fees (7% platform fee)
            const platformFee = betAmount * 0.07;
            const totalAmount = betAmount + platformFee;
            
            // Send transaction
            const txParams = {
                from: window.clockchainWallet.address,
                to: window.marketBlockchain.contractAddresses.EnhancedPredictionMarket,
                value: '0x' + (totalAmount * 1e18).toString(16),
                data: this.encodeBetData(this.marketId, submissionId)
            };
            
            const txHash = await window.clockchainWallet.sendTransaction(txParams);
            
            // Show pending notification
            this.showTransactionPending(txHash);
            
            // Wait for confirmation
            await this.waitForTransaction(txHash);
            
            this.hideLoading();
            this.showSuccess('Bet placed successfully!');
            
            // Reload market data
            setTimeout(() => {
                this.loadMarketData().then(() => this.updateUI());
            }, 2000);
            
        } catch (error) {
            this.hideLoading();
            this.showError(error.message);
        }
    }
    
    async showBetModal() {
        return new Promise((resolve) => {
            const modal = document.createElement('div');
            modal.innerHTML = `
                <div class="modal fade show d-block" tabindex="-1" style="background: rgba(0,0,0,0.5);">
                    <div class="modal-dialog modal-dialog-centered">
                        <div class="modal-content bg-dark text-white">
                            <div class="modal-header">
                                <h5 class="modal-title">Place Bet</h5>
                                <button type="button" class="btn-close btn-close-white" onclick="this.closest('.modal').remove()"></button>
                            </div>
                            <div class="modal-body">
                                <div class="mb-3">
                                    <label for="bet-amount" class="form-label">Bet Amount (ETH)</label>
                                    <input type="number" class="form-control" id="bet-amount" 
                                           step="0.001" min="0.001" placeholder="0.01" required>
                                    <small class="text-muted">Plus 7% platform fee</small>
                                </div>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" onclick="this.closest('.modal').remove()">Cancel</button>
                                <button type="button" class="btn btn-primary" id="confirm-bet-btn">Place Bet</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            
            document.getElementById('confirm-bet-btn').addEventListener('click', () => {
                const amount = parseFloat(document.getElementById('bet-amount').value);
                modal.remove();
                resolve(amount);
            });
            
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.remove();
                    resolve(null);
                }
            });
        });
    }
    
    // Placeholder for encoding functions - would need actual ABI encoding
    encodeSubmissionData(predictedText, submissionFee, initialBet) {
        // This would use Web3.js to encode the function call
        return '0x';
    }
    
    encodeBetData(marketId, submissionId) {
        // This would use Web3.js to encode the function call
        return '0x';
    }
    
    async waitForTransaction(txHash) {
        // Reuse from base-blockchain.js
        if (window.baseBlockchain) {
            return window.baseBlockchain.waitForTransaction(txHash);
        }
    }
    
    showLoading(message) {
        if (window.baseBlockchain) {
            window.baseBlockchain.showLoading(message);
        }
    }
    
    hideLoading() {
        if (window.baseBlockchain) {
            window.baseBlockchain.hideLoading();
        }
    }
    
    showTransactionPending(txHash) {
        if (window.baseBlockchain) {
            window.baseBlockchain.showTransactionPending(txHash);
        }
    }
    
    showSuccess(message) {
        if (window.clockchainWallet) {
            window.clockchainWallet.showSuccess(message);
        }
    }
    
    showError(message) {
        if (window.clockchainWallet) {
            window.clockchainWallet.showError(message);
        }
    }
}

// Initialize on market detail pages
document.addEventListener('DOMContentLoaded', () => {
    const path = window.location.pathname;
    const marketMatch = path.match(/\/clockchain\/market\/(\d+)/);
    
    if (marketMatch) {
        const marketId = parseInt(marketMatch[1]);
        window.marketDetailBlockchain = new MarketDetailBlockchain(marketId);
    }
});