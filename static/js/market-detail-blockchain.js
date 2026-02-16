/**
 * Market Detail Blockchain Integration for PredictionMarketV2
 * Handles wallet transactions for submissions and claim payouts
 * V2: Simplified submission model (predictedText + ETH stake)
 */

class MarketDetailBlockchain {
    constructor(marketId) {
        this.marketId = marketId;
        this.marketData = null;
        this.bettingContract = null;
        this.initialized = false;
        this.userAddress = null;

        this.init();
    }

    async init() {
        try {
            // Only initialize on market detail page
            if (!window.isMarketDetailPage) {
                return;
            }

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
            // Don't show error if dependencies not ready yet
            if (error.message !== 'Dependencies not loaded') {
                this.showError('Failed to load market data from blockchain');
            }
        }
    }

    async waitForDependencies() {
        const maxAttempts = 50;
        let attempts = 0;

        while (attempts < maxAttempts) {
            // Check if Web3 and marketBlockchain are loaded
            if (typeof Web3 !== 'undefined' && window.marketBlockchain?.initialized) {
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

        // Get user address if wallet connected
        if (window.proteusWallet?.isConnected) {
            this.userAddress = window.proteusWallet.address?.toLowerCase();
        }
    }

    updateUI() {
        // Update market statistics from blockchain
        const statsContainer = document.querySelector('.market-statistics');
        if (statsContainer) {
            const statusBadge = this.marketData.resolved
                ? '<span class="badge bg-success">Resolved</span>'
                : (this.marketData.endTime > new Date()
                    ? '<span class="badge bg-primary">Active</span>'
                    : '<span class="badge bg-warning">Pending Resolution</span>');

            statsContainer.innerHTML = `
                <p class="text-muted">
                    <strong>Total Pool:</strong> ${this.marketData.totalPool} ETH<br>
                    <strong>Submissions:</strong> ${this.marketData.submissions?.length || 0}<br>
                    <strong>Status:</strong> ${statusBadge}<br>
                    <strong>Ends:</strong> ${this.marketData.endTime.toLocaleString()}
                </p>
            `;
        }

        // Add submission form if market is active (not resolved and before end time)
        if (!this.marketData.resolved && this.marketData.endTime > new Date()) {
            this.addSubmissionForm();
        }

        // Show claim payout section if market is resolved
        if (this.marketData.resolved) {
            this.addResolutionInfo();
        }

        // Update submissions display
        this.updateSubmissionsDisplay();
    }

    addSubmissionForm() {
        const submissionsCard = document.querySelector('.card-body');
        if (!submissionsCard) return;

        // Check if form already exists
        if (document.getElementById('blockchain-submission-form')) return;

        const formHtml = `
            <div class="submission-form mb-4 p-3 bg-dark rounded">
                <h6 class="text-primary mb-3">
                    <i class="fas fa-plus-circle me-2"></i>
                    Submit Your Prediction
                </h6>
                <form id="blockchain-submission-form">
                    <div class="mb-3">
                        <label for="predicted-text" class="form-label">Predicted Text</label>
                        <textarea class="form-control" id="predicted-text" rows="3"
                                  placeholder="Enter the exact text you predict @${this.marketData.actorHandle} will post..."
                                  required maxlength="280"></textarea>
                        <small class="text-muted">
                            <span id="char-count">0</span>/280 characters - Match as closely as possible to win!
                        </small>
                    </div>
                    <div class="mb-3">
                        <label for="stake-amount" class="form-label">Stake Amount (ETH)</label>
                        <input type="number" class="form-control" id="stake-amount"
                               step="0.001" min="0.001" value="0.01" required>
                        <small class="text-muted">Minimum: 0.001 ETH - Winner takes the pool (minus 7% fee)</small>
                    </div>
                    <div class="alert alert-info py-2">
                        <i class="fas fa-info-circle"></i>
                        Your prediction will be compared to @${this.marketData.actorHandle}'s actual post using Levenshtein distance.
                        The closest match wins the entire pool!
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

            // Add character counter
            document.getElementById('predicted-text').addEventListener('input', (e) => {
                document.getElementById('char-count').textContent = e.target.value.length;
            });
        }
    }

    addResolutionInfo() {
        const container = document.querySelector('.card-body');
        if (!container) return;

        // Check if already added
        if (document.getElementById('resolution-info')) return;

        // Find winning submission
        const winningSubmission = this.marketData.submissions?.find(s => s.isWinner);

        const infoHtml = `
            <div id="resolution-info" class="alert alert-success mb-4">
                <h5 class="alert-heading">
                    <i class="fas fa-trophy me-2"></i>Market Resolved!
                </h5>
                ${winningSubmission ? `
                    <p class="mb-2"><strong>Winning Prediction:</strong></p>
                    <blockquote class="blockquote mb-3" style="font-size: 0.9rem;">
                        "${winningSubmission.predictedText}"
                    </blockquote>
                    <p class="mb-0">
                        <strong>Winner:</strong>
                        <code>${this.formatAddress(winningSubmission.submitter)}</code>
                        <br>
                        <strong>Pool Won:</strong> ${this.marketData.totalPool} ETH
                    </p>
                ` : `
                    <p class="mb-0">No winning submission found.</p>
                `}
            </div>
        `;

        container.insertAdjacentHTML('afterbegin', infoHtml);
    }

    updateSubmissionsDisplay() {
        if (!this.marketData.submissions || this.marketData.submissions.length === 0) {
            return;
        }

        const tbody = document.querySelector('.table tbody');
        if (!tbody) return;

        // Clear existing rows
        tbody.innerHTML = '';

        // Add submission rows
        this.marketData.submissions.forEach((submission) => {
            const isUserSubmission = this.userAddress &&
                submission.submitter.toLowerCase() === this.userAddress;
            const canClaim = submission.isWinner && !submission.claimed && isUserSubmission;

            const row = document.createElement('tr');
            row.className = submission.isWinner ? 'table-success' : '';
            row.innerHTML = `
                <td>
                    <span class="badge ${submission.isWinner ? 'bg-warning' : 'bg-primary'}">
                        ${submission.isWinner ? 'Winner' : `#${submission.id}`}
                    </span>
                </td>
                <td>
                    <div style="max-width: 300px; word-wrap: break-word;">
                        "${submission.predictedText}"
                    </div>
                </td>
                <td>
                    <small class="text-muted font-monospace">
                        ${this.formatAddress(submission.submitter)}
                        ${isUserSubmission ? '<span class="badge bg-info ms-1">You</span>' : ''}
                    </small>
                </td>
                <td>
                    <strong>${submission.amount} ETH</strong>
                </td>
                <td>
                    ${this.getSubmissionAction(submission, canClaim)}
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    getSubmissionAction(submission, canClaim) {
        if (this.marketData.resolved) {
            if (submission.isWinner) {
                if (submission.claimed) {
                    return '<span class="badge bg-secondary">Claimed</span>';
                } else if (canClaim) {
                    return `<button class="btn btn-sm btn-success claim-btn"
                            data-submission-id="${submission.id}">
                        <i class="fas fa-coins me-1"></i> Claim Payout
                    </button>`;
                } else {
                    return '<span class="badge bg-warning">Winner - Unclaimed</span>';
                }
            } else {
                return '<span class="badge bg-danger">Lost</span>';
            }
        }

        // Market not resolved yet
        if (this.marketData.endTime <= new Date()) {
            return '<span class="badge bg-secondary">Pending</span>';
        }

        return '<span class="badge bg-info">Active</span>';
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

        // Claim payout button handlers
        document.addEventListener('click', async (e) => {
            if (e.target.classList.contains('claim-btn') || e.target.parentElement?.classList.contains('claim-btn')) {
                const btn = e.target.classList.contains('claim-btn') ? e.target : e.target.parentElement;
                const submissionId = btn.dataset.submissionId;
                await this.handleClaimPayout(submissionId);
            }
        });

        // Refund button handler
        document.addEventListener('click', async (e) => {
            if (e.target.classList.contains('refund-btn') || e.target.parentElement?.classList.contains('refund-btn')) {
                await this.handleRefund();
            }
        });
    }

    async handleSubmissionCreate() {
        try {
            // Check wallet connection
            if (!window.proteusWallet?.isConnected) {
                alert('Please connect your wallet first');
                return;
            }

            const predictedText = document.getElementById('predicted-text').value.trim();
            const stakeAmount = document.getElementById('stake-amount').value;

            // Validate inputs
            if (!predictedText) {
                throw new Error('Please enter your predicted text');
            }

            if (!stakeAmount || parseFloat(stakeAmount) < 0.001) {
                throw new Error('Minimum stake is 0.001 ETH');
            }

            // Show loading
            const submitBtn = document.getElementById('submit-prediction-btn');
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Submitting...';

            // Initialize betting contract
            if (!this.bettingContract) {
                this.bettingContract = new BettingContract();
                await this.bettingContract.init();
            }

            // Create submission on blockchain
            const tx = await this.bettingContract.submitNewPrediction(
                this.marketId,
                predictedText,
                stakeAmount
            );

            console.log('Submission created:', tx);

            this.showSuccess(`Prediction submitted successfully!\n\nTx: ${tx.transactionHash}`);

            // Clear form
            document.getElementById('predicted-text').value = '';
            document.getElementById('char-count').textContent = '0';

            // Re-enable button
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-rocket me-2"></i>Submit Prediction';

            // Reload market data after delay
            setTimeout(async () => {
                await this.loadMarketData();
                this.updateUI();
            }, 3000);

        } catch (error) {
            console.error('Submission error:', error);
            this.showError(error.message);

            // Re-enable button
            const submitBtn = document.getElementById('submit-prediction-btn');
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="fas fa-rocket me-2"></i>Submit Prediction';
            }
        }
    }

    async handleClaimPayout(submissionId) {
        try {
            // Check wallet connection
            if (!window.proteusWallet?.isConnected) {
                alert('Please connect your wallet first');
                return;
            }

            // Confirm action
            if (!confirm(`Claim payout for submission #${submissionId}?\n\nYou will receive the pool minus 7% platform fee.`)) {
                return;
            }

            // Show loading on button
            const btn = document.querySelector(`.claim-btn[data-submission-id="${submissionId}"]`);
            if (btn) {
                btn.disabled = true;
                btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            }

            // Initialize betting contract
            if (!this.bettingContract) {
                this.bettingContract = new BettingContract();
                await this.bettingContract.init();
            }

            // Claim payout
            const tx = await this.bettingContract.claimPayout(submissionId);

            console.log('Payout claimed:', tx);

            this.showSuccess(`Payout claimed successfully!\n\nTx: ${tx.transactionHash}`);

            // Reload market data
            setTimeout(async () => {
                await this.loadMarketData();
                this.updateUI();
            }, 3000);

        } catch (error) {
            console.error('Claim payout error:', error);
            this.showError(error.message);

            // Re-enable button
            const btn = document.querySelector(`.claim-btn[data-submission-id="${submissionId}"]`);
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-coins me-1"></i> Claim Payout';
            }
        }
    }

    async handleRefund() {
        try {
            // Check wallet connection
            if (!window.proteusWallet?.isConnected) {
                alert('Please connect your wallet first');
                return;
            }

            // Confirm action
            if (!confirm('Request refund for this market?\n\nThis only works if you are the only submitter and the market has ended.')) {
                return;
            }

            // Initialize betting contract
            if (!this.bettingContract) {
                this.bettingContract = new BettingContract();
                await this.bettingContract.init();
            }

            // Request refund
            const tx = await this.bettingContract.refundSingleSubmission(this.marketId);

            console.log('Refund processed:', tx);

            this.showSuccess(`Refund processed successfully!\n\nTx: ${tx.transactionHash}`);

            // Reload market data
            setTimeout(async () => {
                await this.loadMarketData();
                this.updateUI();
            }, 3000);

        } catch (error) {
            console.error('Refund error:', error);
            this.showError(error.message);
        }
    }

    formatAddress(address) {
        if (!address) return 'Unknown';
        return address.substring(0, 6) + '...' + address.substring(38);
    }

    showSuccess(message) {
        alert(message);
    }

    showError(message) {
        alert('Error: ' + message);
    }
}

// Initialize on market detail pages
document.addEventListener('DOMContentLoaded', () => {
    const path = window.location.pathname;
    const marketMatch = path.match(/\/proteus\/market\/(\d+)/);

    if (marketMatch) {
        const marketId = parseInt(marketMatch[1]);
        window.isMarketDetailPage = true;
        window.marketDetailBlockchain = new MarketDetailBlockchain(marketId);
    }
});
