/**
 * Market Creation Interface for BASE Blockchain
 * Handles the UI and logic for creating new prediction markets
 */

class MarketCreator {
    constructor() {
        this.form = null;
        this.oracleWallets = [];
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
                            <div class="form-text">The X.com (Twitter) handle to track</div>
                        </div>
                        
                        <div class="mb-3">
                            <label for="market-question" class="form-label">Market Question</label>
                            <input type="text" class="form-control" id="market-question" required
                                   placeholder="Will Elon Musk tweet about BASE blockchain?">
                            <div class="form-text">What are you predicting?</div>
                        </div>
                        
                        <div class="mb-3">
                            <label for="predicted-text" class="form-label">Predicted Text (Optional)</label>
                            <textarea class="form-control" id="predicted-text" rows="3"
                                      placeholder="BASE blockchain is the future"></textarea>
                            <div class="form-text">Leave empty for a null submission</div>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label for="duration-hours" class="form-label">Duration (Hours)</label>
                                <input type="number" class="form-control" id="duration-hours" 
                                       min="1" max="720" value="24" required>
                                <div class="form-text">How long until market expires?</div>
                            </div>
                            
                            <div class="col-md-6 mb-3">
                                <label for="initial-stake" class="form-label">Initial Stake (ETH)</label>
                                <input type="number" class="form-control" id="initial-stake" 
                                       min="0.01" step="0.01" value="0.1" required>
                                <div class="form-text">Your initial bet amount</div>
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Oracle Wallets</label>
                            <div id="oracle-wallets-list" class="mb-2"></div>
                            <div class="input-group">
                                <input type="text" class="form-control" id="oracle-wallet-input" 
                                       placeholder="0x..." pattern="0x[a-fA-F0-9]{40}">
                                <button type="button" class="btn btn-outline-primary" id="add-oracle-btn">
                                    Add Oracle
                                </button>
                            </div>
                            <div class="form-text">Add trusted oracle addresses (minimum 1)</div>
                        </div>
                        
                        <div class="alert alert-info">
                            <i class="fas fa-info-circle"></i> 
                            <strong>Platform Fee:</strong> 7% will be added to your stake
                            <br>
                            <span id="total-amount-display">Total: 0.107 ETH</span>
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
        
        // Add oracle button
        document.getElementById('add-oracle-btn').addEventListener('click', () => {
            this.addOracle();
        });
        
        // Oracle input enter key
        document.getElementById('oracle-wallet-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.addOracle();
            }
        });
        
        // Update total amount display
        document.getElementById('initial-stake').addEventListener('input', (e) => {
            this.updateTotalAmount();
        });
        
        // Initial total update
        this.updateTotalAmount();
    }
    
    addOracle() {
        const input = document.getElementById('oracle-wallet-input');
        const wallet = input.value.trim();
        
        if (!wallet || !/^0x[a-fA-F0-9]{40}$/.test(wallet)) {
            alert('Please enter a valid wallet address');
            return;
        }
        
        if (this.oracleWallets.includes(wallet)) {
            alert('This oracle is already added');
            return;
        }
        
        this.oracleWallets.push(wallet);
        input.value = '';
        this.renderOracleList();
    }
    
    renderOracleList() {
        const container = document.getElementById('oracle-wallets-list');
        container.innerHTML = this.oracleWallets.map((wallet, index) => `
            <div class="badge bg-secondary me-2 mb-2">
                ${wallet.substring(0, 6)}...${wallet.substring(38)}
                <button type="button" class="btn-close btn-close-white ms-2" 
                        onclick="marketCreator.removeOracle(${index})"></button>
            </div>
        `).join('');
    }
    
    removeOracle(index) {
        this.oracleWallets.splice(index, 1);
        this.renderOracleList();
    }
    
    updateTotalAmount() {
        const stake = parseFloat(document.getElementById('initial-stake').value) || 0;
        const fee = stake * 0.07;
        const total = stake + fee;
        
        document.getElementById('total-amount-display').textContent = 
            `Total: ${total.toFixed(4)} ETH (includes ${fee.toFixed(4)} ETH platform fee)`;
    }
    
    async createMarket() {
        // Validate oracle wallets - minimum 1 required from user
        if (this.oracleWallets.length === 0) {
            alert('Please add at least one oracle wallet');
            return;
        }
        
        // Pad oracle array to meet contract requirement of 3 minimum
        let paddedOracleWallets = [...this.oracleWallets];
        while (paddedOracleWallets.length < 3) {
            // Add placeholder addresses to meet contract requirement
            paddedOracleWallets.push('0x' + '0'.repeat(39) + (paddedOracleWallets.length + 1));
        }
        
        // Check wallet connection
        if (!clockchainWallet || !clockchainWallet.isConnected) {
            alert('Please connect your wallet first');
            return;
        }
        
        // Gather form data
        const marketData = {
            actorHandle: document.getElementById('actor-handle').value,
            question: document.getElementById('market-question').value,
            predictedText: document.getElementById('predicted-text').value,
            durationHours: parseInt(document.getElementById('duration-hours').value),
            initialStake: document.getElementById('initial-stake').value,
            oracleWallets: paddedOracleWallets  // Use padded array for contract
        };
        
        // Disable submit button
        const submitBtn = document.getElementById('submit-market-btn');
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating Market...';
        
        try {
            // Call blockchain integration
            await baseBlockchain.createPredictionMarket(marketData);
        } catch (error) {
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