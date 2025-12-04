/**
 * Market Creation Interface for PredictionMarketV2
 * Handles the UI and logic for creating new prediction markets
 * V2: Simplified market creation (actorHandle + duration only, NOT payable)
 */

class MarketCreator {
    constructor() {
        this.form = null;
        this.bettingContract = null;
        this.initializeForm();
    }

    initializeForm() {
        // Check if we're on a page with market creation form
        const formContainer = document.getElementById('market-create-form');
        if (!formContainer) return;

        formContainer.innerHTML = `
            <div class="card bg-dark text-white">
                <div class="card-header">
                    <h4 class="mb-0">Create New Prediction Market</h4>
                </div>
                <div class="card-body">
                    <form id="create-market-form">
                        <div class="mb-3">
                            <label for="actor-handle" class="form-label">X.com Handle</label>
                            <div class="input-group">
                                <span class="input-group-text">@</span>
                                <input type="text" class="form-control" id="actor-handle" required
                                       placeholder="elonmusk" pattern="[a-zA-Z0-9_]+">
                            </div>
                            <div class="form-text">The X.com (Twitter) handle to track for next post prediction</div>
                        </div>

                        <div class="mb-3">
                            <label for="duration-hours" class="form-label">Duration (Hours)</label>
                            <input type="number" class="form-control" id="duration-hours"
                                   min="1" max="720" value="24" required>
                            <div class="form-text">How long until market closes for submissions</div>
                        </div>

                        <div class="alert alert-success">
                            <i class="fas fa-check-circle"></i>
                            <strong>Free to Create!</strong> Market creation costs only gas fees.
                            <br>
                            <small>Participants bet ETH when submitting predictions. 7% platform fee on payouts.</small>
                        </div>

                        <div class="alert alert-info">
                            <i class="fas fa-info-circle"></i>
                            <strong>How it works:</strong>
                            <ul class="mb-0 mt-2">
                                <li>Create a market for any X.com handle</li>
                                <li>Players submit predictions with ETH stakes</li>
                                <li>After market ends, oracle resolves with actual tweet text</li>
                                <li>Closest prediction (Levenshtein distance) wins the pool</li>
                            </ul>
                        </div>

                        <div class="alert alert-secondary">
                            <strong>Contract:</strong>
                            <code id="contract-address">0x5174Da96BCA87c78591038DEe9DB1811288c9286</code>
                            <br>
                            <small>PredictionMarketV2 on BASE Sepolia</small>
                        </div>

                        <button type="submit" class="btn btn-primary btn-lg w-100" id="submit-market-btn">
                            <i class="fas fa-rocket"></i> Create Market on BASE
                        </button>
                    </form>
                </div>
            </div>
        `;

        this.form = document.getElementById('create-market-form');
        this.attachEventListeners();
    }

    attachEventListeners() {
        // Form submission
        this.form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.createMarket();
        });
    }

    async createMarket() {
        // Check wallet connection
        if (!window.clockchainWallet || !window.clockchainWallet.isConnected) {
            alert('Please connect your wallet first');
            return;
        }

        // Gather form data
        const actorHandle = document.getElementById('actor-handle').value.trim();
        const durationHours = parseInt(document.getElementById('duration-hours').value);

        // Validate
        if (!actorHandle) {
            alert('Please enter an X.com handle');
            return;
        }

        if (!durationHours || durationHours < 1 || durationHours > 720) {
            alert('Please enter a valid duration (1-720 hours)');
            return;
        }

        // Clean handle (remove @ if present)
        const cleanHandle = actorHandle.replace(/^@/, '');

        // Disable submit button
        const submitBtn = document.getElementById('submit-market-btn');
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating Market...';

        try {
            // Initialize betting contract if not already done
            if (!this.bettingContract) {
                this.bettingContract = new BettingContract();
                await this.bettingContract.init();
            }

            // Create market on blockchain (V2: NOT payable, just gas)
            const tx = await this.bettingContract.createMarket(cleanHandle, durationHours);

            console.log('Market created successfully:', tx);

            // Extract market ID from event logs if available
            let marketId = null;
            if (tx.events && tx.events.MarketCreated) {
                marketId = tx.events.MarketCreated.returnValues.marketId;
            }

            // Show success message
            const successMsg = marketId
                ? `Market #${marketId} created successfully!\n\nTransaction: ${tx.transactionHash}\n\nView on Basescan: https://sepolia.basescan.org/tx/${tx.transactionHash}`
                : `Market created successfully!\n\nTransaction: ${tx.transactionHash}\n\nView on Basescan: https://sepolia.basescan.org/tx/${tx.transactionHash}`;

            alert(successMsg);

            // Redirect to clockchain view
            window.location.href = '/clockchain';

        } catch (error) {
            console.error('Error creating market:', error);
            alert(`Error creating market: ${error.message}`);

            // Re-enable button on error
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-rocket"></i> Create Market on BASE';
        }
    }
}

// Initialize market creator
let marketCreator;
document.addEventListener('DOMContentLoaded', () => {
    marketCreator = new MarketCreator();
});
