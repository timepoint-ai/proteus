/**
 * BASE Blockchain Integration for Clockchain
 * Handles smart contract interactions and transaction management
 */

class BaseBlockchain {
    constructor(wallet) {
        this.wallet = wallet;
        this.platformFee = 0.07; // 7% platform fee
        
        // Contract ABIs (minimal for now, will be populated when contracts are compiled)
        this.abis = {
            PredictionMarket: [
                {
                    "inputs": [
                        {"name": "_actor", "type": "string"},
                        {"name": "_endTime", "type": "uint256"},
                        {"name": "_oracles", "type": "address[]"},
                        {"name": "_ipfsData", "type": "string"}
                    ],
                    "name": "createMarket",
                    "outputs": [{"name": "", "type": "uint256"}],
                    "stateMutability": "payable",
                    "type": "function"
                }
            ]
        };
        
        // Contract addresses (will be set from environment)
        this.contracts = {
            PredictionMarket: null,
            ClockchainOracle: null,
            NodeRegistry: null,
            PayoutManager: null
        };
    }
    
    async createPredictionMarket(marketData) {
        try {
            if (!this.wallet.isConnected) {
                throw new Error('Please connect your wallet first');
            }
            
            // Show loading state
            this.showLoading('Creating prediction market...');
            
            // Prepare API call to create market in database first
            const response = await fetch('/api/base/markets/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    question: marketData.question,
                    actor_handle: marketData.actorHandle,
                    duration_hours: marketData.durationHours,
                    initial_stake: marketData.initialStake,
                    creator_wallet: this.wallet.address,
                    xcom_only: true,
                    predicted_text: marketData.predictedText || '',
                    oracle_wallets: marketData.oracleWallets || []
                })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to create market');
            }
            
            const result = await response.json();
            
            // If we have contract deployment info, send the transaction
            if (result.blockchain_tx) {
                const txParams = {
                    from: this.wallet.address,
                    to: result.blockchain_tx.to,
                    value: '0x' + BigInt(result.blockchain_tx.value).toString(16),
                    data: result.blockchain_tx.data || '0x',
                    gas: result.blockchain_tx.gas_estimate
                };
                
                // Send transaction
                const txHash = await this.wallet.sendTransaction(txParams);
                
                // Show transaction pending
                this.showTransactionPending(txHash);
                
                // Wait for confirmation
                await this.waitForTransaction(txHash);
                
                this.hideLoading();
                this.wallet.showSuccess('Market created successfully!');
                
                // Redirect to market detail page
                window.location.href = `/clockchain/market/${result.market_id}`;
                
            } else {
                // Manual transaction required (no contract)
                this.hideLoading();
                this.showManualTransactionRequired(result);
            }
            
        } catch (error) {
            this.hideLoading();
            this.wallet.showError(error.message);
            console.error('Error creating market:', error);
        }
    }
    
    async placeBet(submissionId, amount) {
        try {
            if (!this.wallet.isConnected) {
                throw new Error('Please connect your wallet first');
            }
            
            this.showLoading('Placing bet...');
            
            // Calculate total amount including platform fee
            const betAmount = parseFloat(amount);
            const platformFee = betAmount * this.platformFee;
            const totalAmount = betAmount + platformFee;
            
            // Prepare transaction
            const txParams = {
                from: this.wallet.address,
                to: this.contracts.PredictionMarket || '0x0000000000000000000000000000000000000000',
                value: '0x' + BigInt(Math.floor(totalAmount * 1e18)).toString(16)
            };
            
            // Send transaction
            const txHash = await this.wallet.sendTransaction(txParams);
            
            // Record bet in database
            await fetch('/api/base/bets/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    submission_id: submissionId,
                    amount: amount,
                    bettor_wallet: this.wallet.address,
                    transaction_hash: txHash
                })
            });
            
            this.hideLoading();
            this.wallet.showSuccess('Bet placed successfully!');
            
            // Reload page to show updated data
            setTimeout(() => window.location.reload(), 2000);
            
        } catch (error) {
            this.hideLoading();
            this.wallet.showError(error.message);
        }
    }
    
    async submitOracleData(marketId, oracleData) {
        try {
            if (!this.wallet.isConnected) {
                throw new Error('Please connect your wallet first');
            }
            
            this.showLoading('Submitting oracle data...');
            
            // Sign the oracle data
            const message = JSON.stringify({
                market_id: marketId,
                actual_text: oracleData.actualText,
                tweet_id: oracleData.tweetId,
                timestamp: Date.now()
            });
            
            const signature = await this.wallet.signMessage(message);
            
            // Submit to API
            const response = await fetch(`/api/base/markets/${marketId}/oracle/submit`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    oracle_wallet: this.wallet.address,
                    actual_text: oracleData.actualText,
                    tweet_id: oracleData.tweetId,
                    signature: signature
                })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to submit oracle data');
            }
            
            this.hideLoading();
            this.wallet.showSuccess('Oracle data submitted successfully!');
            
            // Reload page
            setTimeout(() => window.location.reload(), 2000);
            
        } catch (error) {
            this.hideLoading();
            this.wallet.showError(error.message);
        }
    }
    
    async waitForTransaction(txHash) {
        // Poll for transaction receipt
        const checkInterval = 3000; // 3 seconds
        const maxAttempts = 40; // 2 minutes max
        let attempts = 0;
        
        while (attempts < maxAttempts) {
            try {
                const receipt = await window.ethereum.request({
                    method: 'eth_getTransactionReceipt',
                    params: [txHash],
                });
                
                if (receipt) {
                    if (receipt.status === '0x1') {
                        return receipt;
                    } else {
                        throw new Error('Transaction failed');
                    }
                }
            } catch (error) {
                console.error('Error checking transaction:', error);
            }
            
            await new Promise(resolve => setTimeout(resolve, checkInterval));
            attempts++;
        }
        
        throw new Error('Transaction timeout');
    }
    
    showLoading(message) {
        const loader = document.createElement('div');
        loader.id = 'blockchain-loader';
        loader.className = 'position-fixed top-50 start-50 translate-middle text-center';
        loader.style.zIndex = '9998';
        loader.innerHTML = `
            <div class="bg-dark p-4 rounded shadow">
                <div class="spinner-border text-primary mb-3" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="text-white mb-0">${message}</p>
            </div>
        `;
        document.body.appendChild(loader);
    }
    
    hideLoading() {
        const loader = document.getElementById('blockchain-loader');
        if (loader) {
            loader.remove();
        }
    }
    
    showTransactionPending(txHash) {
        const shortHash = txHash.substring(0, 10) + '...' + txHash.substring(56);
        const notification = document.createElement('div');
        notification.className = 'alert alert-info alert-dismissible fade show position-fixed bottom-0 end-0 m-3';
        notification.style.zIndex = '9997';
        notification.innerHTML = `
            <strong>Transaction Pending</strong><br>
            <a href="https://sepolia.basescan.org/tx/${txHash}" target="_blank" class="text-decoration-none">
                ${shortHash} <i class="fas fa-external-link-alt"></i>
            </a>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.body.appendChild(notification);
    }
    
    showManualTransactionRequired(result) {
        const modal = document.createElement('div');
        modal.innerHTML = `
            <div class="modal fade show d-block" tabindex="-1" style="background: rgba(0,0,0,0.5);">
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content bg-dark text-white">
                        <div class="modal-header">
                            <h5 class="modal-title">Manual Transaction Required</h5>
                            <button type="button" class="btn-close btn-close-white" onclick="this.closest('.modal').remove()"></button>
                        </div>
                        <div class="modal-body">
                            <p>Smart contracts are not yet deployed. Please send a manual transaction:</p>
                            <div class="bg-black p-3 rounded mb-3">
                                <p class="mb-2"><strong>To:</strong><br><code>${result.manual_tx.platform_wallet}</code></p>
                                <p class="mb-2"><strong>Amount:</strong> ${result.manual_tx.amount} ETH</p>
                                <p class="mb-0"><strong>Market ID:</strong> ${result.market_id}</p>
                            </div>
                            <p class="text-warning small mb-0">
                                <i class="fas fa-exclamation-triangle"></i> 
                                Include the Market ID in the transaction memo
                            </p>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" onclick="this.closest('.modal').remove()">Close</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }
}

// Initialize blockchain interface when wallet is ready
document.addEventListener('DOMContentLoaded', () => {
    // Wait for wallet to be initialized
    setTimeout(() => {
        if (typeof clockchainWallet !== 'undefined') {
            window.baseBlockchain = new BaseBlockchain(clockchainWallet);
        }
    }, 100);
});