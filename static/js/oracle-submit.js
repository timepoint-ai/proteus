/**
 * Oracle Submission Interface for BASE Blockchain
 * Handles oracle data submission for expired markets
 */

class OracleSubmitter {
    constructor() {
        this.initializeButtons();
    }
    
    initializeButtons() {
        // Attach event listeners to oracle submit buttons
        document.querySelectorAll('.submit-oracle-data').forEach(button => {
            button.addEventListener('click', (e) => {
                const marketId = e.target.dataset.marketId;
                this.showOracleModal(marketId);
            });
        });
    }
    
    showOracleModal(marketId) {
        // Create modal HTML
        const modal = document.createElement('div');
        modal.innerHTML = `
            <div class="modal fade show d-block" tabindex="-1" style="background: rgba(0,0,0,0.5);">
                <div class="modal-dialog modal-dialog-centered modal-lg">
                    <div class="modal-content bg-dark text-white">
                        <div class="modal-header">
                            <h5 class="modal-title">Submit Oracle Data</h5>
                            <button type="button" class="btn-close btn-close-white" onclick="this.closest('.modal').remove()"></button>
                        </div>
                        <div class="modal-body">
                            <form id="oracle-form-${marketId}">
                                <div class="mb-3">
                                    <label for="tweet-id-${marketId}" class="form-label">X.com Tweet ID</label>
                                    <input type="text" class="form-control" id="tweet-id-${marketId}" 
                                           placeholder="1234567890123456789" required>
                                    <div class="form-text">The ID from the tweet URL</div>
                                </div>
                                
                                <div class="mb-3">
                                    <label for="actual-text-${marketId}" class="form-label">Actual Text</label>
                                    <textarea class="form-control" id="actual-text-${marketId}" rows="4" required
                                              placeholder="Enter the exact text from the tweet"></textarea>
                                    <div class="form-text">Copy the exact text from the X.com post</div>
                                </div>
                                
                                <div class="alert alert-info">
                                    <i class="fas fa-info-circle"></i> 
                                    <strong>Oracle Responsibilities:</strong>
                                    <ul class="mb-0 mt-2">
                                        <li>Verify the tweet is from the correct actor</li>
                                        <li>Ensure the tweet was posted within the market timeframe</li>
                                        <li>Copy the exact text (punctuation matters for Levenshtein distance)</li>
                                        <li>Your wallet address will be recorded with this submission</li>
                                    </ul>
                                </div>
                                
                                <div class="form-check mb-3">
                                    <input class="form-check-input" type="checkbox" id="verify-${marketId}" required>
                                    <label class="form-check-label" for="verify-${marketId}">
                                        I verify this data is accurate and from the correct source
                                    </label>
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" onclick="this.closest('.modal').remove()">Cancel</button>
                            <button type="button" class="btn btn-primary" id="submit-oracle-${marketId}">
                                <i class="fas fa-check-circle"></i> Submit Oracle Data
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Handle oracle submission
        document.getElementById(`submit-oracle-${marketId}`).addEventListener('click', async () => {
            const tweetId = document.getElementById(`tweet-id-${marketId}`).value;
            const actualText = document.getElementById(`actual-text-${marketId}`).value;
            const verified = document.getElementById(`verify-${marketId}`).checked;
            
            if (!tweetId || !actualText || !verified) {
                alert('Please fill all fields and verify the data');
                return;
            }
            
            // Disable button
            const submitBtn = document.getElementById(`submit-oracle-${marketId}`);
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Submitting...';
            
            try {
                await baseBlockchain.submitOracleData(marketId, {
                    tweetId: tweetId,
                    actualText: actualText
                });
                modal.remove();
            } catch (error) {
                // Re-enable button on error
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="fas fa-check-circle"></i> Submit Oracle Data';
            }
        });
    }
}

// Initialize oracle interface
document.addEventListener('DOMContentLoaded', () => {
    new OracleSubmitter();
});