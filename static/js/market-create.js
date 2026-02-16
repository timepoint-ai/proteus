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
            <!-- Live region for status announcements -->
            <div id="form-status" class="aria-live-region" aria-live="polite" aria-atomic="true"></div>

            <div class="card bg-dark text-white">
                <div class="card-header">
                    <h4 class="mb-0" id="form-title">Create New Prediction Market</h4>
                </div>
                <div class="card-body">
                    <form id="create-market-form" aria-labelledby="form-title">
                        <div class="mb-3">
                            <label for="actor-handle" class="form-label">X.com Handle <span class="text-danger" aria-hidden="true">*</span></label>
                            <div class="input-group">
                                <span class="input-group-text" aria-hidden="true">@</span>
                                <input type="text" class="form-control" id="actor-handle" required
                                       placeholder="elonmusk" pattern="[a-zA-Z0-9_]+"
                                       aria-required="true" aria-describedby="actor-handle-help actor-handle-error"
                                       autocomplete="off">
                            </div>
                            <div id="actor-handle-help" class="form-text">The X.com (Twitter) handle to track for next post prediction</div>
                            <div id="actor-handle-error" class="invalid-feedback" role="alert"></div>
                        </div>

                        <div class="mb-3">
                            <label for="duration-hours" class="form-label">Duration (Hours) <span class="text-danger" aria-hidden="true">*</span></label>
                            <input type="number" class="form-control" id="duration-hours"
                                   min="1" max="720" value="24" required
                                   aria-required="true" aria-describedby="duration-hours-help duration-hours-error">
                            <div id="duration-hours-help" class="form-text">How long until market closes for submissions (1-720 hours)</div>
                            <div id="duration-hours-error" class="invalid-feedback" role="alert"></div>
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

                        <button type="submit" class="btn btn-primary btn-lg w-100" id="submit-market-btn" aria-describedby="form-status">
                            <i class="fas fa-rocket" aria-hidden="true"></i> Create Market on BASE
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

        // Real-time validation feedback
        const actorHandle = document.getElementById('actor-handle');
        const durationHours = document.getElementById('duration-hours');

        actorHandle.addEventListener('blur', () => this.validateField(actorHandle, 'actor-handle-error'));
        durationHours.addEventListener('blur', () => this.validateField(durationHours, 'duration-hours-error'));
    }

    /**
     * Announce a message to screen readers via live region
     */
    announceStatus(message) {
        const statusRegion = document.getElementById('form-status');
        if (statusRegion) {
            statusRegion.textContent = message;
        }
    }

    /**
     * Validate a form field and show error feedback
     */
    validateField(field, errorId) {
        const errorEl = document.getElementById(errorId);
        if (!field.validity.valid) {
            field.classList.add('is-invalid');
            field.setAttribute('aria-invalid', 'true');
            if (field.validity.valueMissing) {
                errorEl.textContent = 'This field is required';
            } else if (field.validity.patternMismatch) {
                errorEl.textContent = 'Only letters, numbers, and underscores allowed';
            } else if (field.validity.rangeUnderflow || field.validity.rangeOverflow) {
                errorEl.textContent = 'Please enter a value between 1 and 720';
            }
        } else {
            field.classList.remove('is-invalid');
            field.setAttribute('aria-invalid', 'false');
            errorEl.textContent = '';
        }
    }

    async createMarket() {
        // Check wallet connection
        if (!window.proteusWallet || !window.proteusWallet.isConnected) {
            this.announceStatus('Please connect your wallet first');
            alert('Please connect your wallet first');
            return;
        }

        // Gather form data
        const actorHandleInput = document.getElementById('actor-handle');
        const durationHoursInput = document.getElementById('duration-hours');
        const actorHandle = actorHandleInput.value.trim();
        const durationHours = parseInt(durationHoursInput.value);

        // Validate with accessible feedback
        let hasErrors = false;

        if (!actorHandle) {
            this.validateField(actorHandleInput, 'actor-handle-error');
            hasErrors = true;
        }

        if (!durationHours || durationHours < 1 || durationHours > 720) {
            this.validateField(durationHoursInput, 'duration-hours-error');
            hasErrors = true;
        }

        if (hasErrors) {
            this.announceStatus('Please correct the errors in the form');
            // Focus first invalid field
            const firstInvalid = this.form.querySelector('.is-invalid');
            if (firstInvalid) firstInvalid.focus();
            return;
        }

        // Clean handle (remove @ if present)
        const cleanHandle = actorHandle.replace(/^@/, '');

        // Disable submit button and announce loading state
        const submitBtn = document.getElementById('submit-market-btn');
        submitBtn.disabled = true;
        submitBtn.setAttribute('aria-busy', 'true');
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin" aria-hidden="true"></i> <span>Creating Market...</span>';
        this.announceStatus('Creating market, please wait...');

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

            this.announceStatus(marketId ? `Market number ${marketId} created successfully` : 'Market created successfully');
            alert(successMsg);

            // Redirect to proteus view
            window.location.href = '/proteus';

        } catch (error) {
            console.error('Error creating market:', error);
            this.announceStatus(`Error creating market: ${error.message}`);
            alert(`Error creating market: ${error.message}`);

            // Re-enable button on error
            submitBtn.disabled = false;
            submitBtn.setAttribute('aria-busy', 'false');
            submitBtn.innerHTML = '<i class="fas fa-rocket" aria-hidden="true"></i> Create Market on BASE';
        }
    }
}

// Initialize market creator
let marketCreator;
document.addEventListener('DOMContentLoaded', () => {
    marketCreator = new MarketCreator();
});
