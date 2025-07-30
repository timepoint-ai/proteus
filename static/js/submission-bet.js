/**
 * Submission Betting Interface for BASE Blockchain
 * Handles betting on existing submissions
 */

class SubmissionBetting {
    constructor() {
        this.initializeButtons();
    }
    
    initializeButtons() {
        // Attach event listeners to all bet buttons
        document.querySelectorAll('.bet-on-submission').forEach(button => {
            button.addEventListener('click', (e) => {
                const submissionId = e.target.dataset.submissionId;
                const marketId = e.target.dataset.marketId;
                this.showBetModal(submissionId, marketId);
            });
        });
    }
    
    showBetModal(submissionId, marketId) {
        // Create modal HTML
        const modal = document.createElement('div');
        modal.innerHTML = `
            <div class="modal fade show d-block" tabindex="-1" style="background: rgba(0,0,0,0.5);">
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content bg-dark text-white">
                        <div class="modal-header">
                            <h5 class="modal-title">Place Bet on Submission</h5>
                            <button type="button" class="btn-close btn-close-white" onclick="this.closest('.modal').remove()"></button>
                        </div>
                        <div class="modal-body">
                            <form id="bet-form-${submissionId}">
                                <div class="mb-3">
                                    <label for="bet-amount-${submissionId}" class="form-label">Bet Amount (ETH)</label>
                                    <input type="number" class="form-control" id="bet-amount-${submissionId}" 
                                           min="0.01" step="0.01" value="0.1" required>
                                    <div class="form-text">Minimum bet: 0.01 ETH</div>
                                </div>
                                
                                <div class="alert alert-info">
                                    <i class="fas fa-info-circle"></i> 
                                    <strong>Platform Fee:</strong> 7% will be added to your bet
                                    <br>
                                    <span id="total-bet-${submissionId}">Total: 0.107 ETH</span>
                                </div>
                                
                                <div class="text-muted small">
                                    <p class="mb-1">By placing this bet, you're predicting this submission will have the lowest Levenshtein distance.</p>
                                    <p class="mb-0">Payouts are distributed proportionally among winning bettors.</p>
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" onclick="this.closest('.modal').remove()">Cancel</button>
                            <button type="button" class="btn btn-primary" id="submit-bet-${submissionId}">
                                <i class="fas fa-coins"></i> Place Bet
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Update total on input change
        const amountInput = document.getElementById(`bet-amount-${submissionId}`);
        const totalDisplay = document.getElementById(`total-bet-${submissionId}`);
        
        amountInput.addEventListener('input', () => {
            const amount = parseFloat(amountInput.value) || 0;
            const fee = amount * 0.07;
            const total = amount + fee;
            totalDisplay.textContent = `Total: ${total.toFixed(4)} ETH (includes ${fee.toFixed(4)} ETH fee)`;
        });
        
        // Handle bet submission
        document.getElementById(`submit-bet-${submissionId}`).addEventListener('click', async () => {
            const amount = amountInput.value;
            
            // Disable button
            const submitBtn = document.getElementById(`submit-bet-${submissionId}`);
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
            
            try {
                await baseBlockchain.placeBet(submissionId, amount);
                modal.remove();
            } catch (error) {
                // Re-enable button on error
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="fas fa-coins"></i> Place Bet';
            }
        });
    }
}

// Initialize betting interface
document.addEventListener('DOMContentLoaded', () => {
    new SubmissionBetting();
});