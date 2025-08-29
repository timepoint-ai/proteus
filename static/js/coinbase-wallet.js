/**
 * Coinbase Embedded Wallet Adapter
 * Provides MetaMask-compatible interface for Coinbase Embedded Wallet
 */

class CoinbaseEmbeddedWallet {
    constructor() {
        this.wallet = null;
        this.address = null;
        this.provider = null;
        this.isConnected = false;
        this.chainId = '0x14a34'; // BASE Sepolia
        this.projectId = window.COINBASE_PROJECT_ID || null;
    }
    
    /**
     * Initialize the Coinbase Embedded Wallet SDK
     */
    async init() {
        try {
            // Check if we have required credentials
            if (!this.projectId) {
                // Get project ID from backend
                const response = await fetch('/api/embedded/config');
                const config = await response.json();
                this.projectId = config.project_id;
                window.COINBASE_PROJECT_ID = this.projectId;
            }
            
            // For now, create a provider interface that matches MetaMask
            // This will be replaced with actual Coinbase SDK when available
            this.provider = {
                request: this.request.bind(this),
                on: this.on.bind(this),
                removeListener: this.removeListener.bind(this),
                // Additional MetaMask-compatible methods
                isMetaMask: false,
                isCoinbaseWallet: true,
                selectedAddress: null,
                chainId: this.chainId
            };
            
            return this;
        } catch (error) {
            console.error('Failed to initialize Coinbase Embedded Wallet:', error);
            throw error;
        }
    }
    
    /**
     * Authenticate user with email (already done via Firebase)
     * Link wallet to authenticated user
     */
    async authenticate(email) {
        try {
            // Check if user is already authenticated
            const authResponse = await fetch('/api/embedded/auth/status');
            const authData = await authResponse.json();
            
            if (!authData.authenticated) {
                throw new Error('User not authenticated. Please sign in first.');
            }
            
            // Link wallet to authenticated user
            const response = await fetch('/api/embedded/link-wallet', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    email: email || authData.email,
                    create_if_not_exists: true
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to link wallet');
            }
            
            const data = await response.json();
            this.address = data.wallet_address;
            this.isConnected = true;
            this.provider.selectedAddress = this.address;
            
            // Emit connect event for compatibility
            this.emit('connect', { chainId: this.chainId });
            this.emit('accountsChanged', [this.address]);
            
            return this.address;
        } catch (error) {
            console.error('Failed to authenticate wallet:', error);
            throw error;
        }
    }
    
    /**
     * Connect wallet (combines init and authenticate)
     */
    async connect(email) {
        await this.init();
        return await this.authenticate(email);
    }
    
    /**
     * MetaMask-compatible request method
     */
    async request(args) {
        const { method, params } = args;
        
        switch (method) {
            case 'eth_requestAccounts':
            case 'eth_accounts':
                if (!this.isConnected) {
                    // Trigger authentication flow
                    const email = await this.promptForEmail();
                    await this.authenticate(email);
                }
                return [this.address];
                
            case 'eth_chainId':
                return this.chainId;
                
            case 'wallet_switchEthereumChain':
                // BASE Sepolia only for now
                if (params[0].chainId !== this.chainId) {
                    throw new Error('Only BASE Sepolia is supported');
                }
                return null;
                
            case 'eth_sendTransaction':
                return await this.sendTransaction(params[0]);
                
            case 'personal_sign':
            case 'eth_signTypedData':
            case 'eth_signTypedData_v4':
                return await this.signMessage(method, params);
                
            case 'eth_getBalance':
                return await this.getBalance(params[0]);
                
            case 'eth_call':
                return await this.ethCall(params[0]);
                
            case 'eth_estimateGas':
                return await this.estimateGas(params[0]);
                
            case 'eth_gasPrice':
                // Return 1 gwei for BASE Sepolia
                return '0xf4240'; // 1 gwei in hex
                
            default:
                // Forward to backend for processing
                return await this.forwardToBackend(method, params);
        }
    }
    
    /**
     * Send transaction with policy checks
     */
    async sendTransaction(tx) {
        try {
            // Apply transaction policies
            const validatedTx = await this.validateTransaction(tx);
            
            // Show custom confirmation UI (not MetaMask popup)
            const confirmed = await this.showTransactionConfirmation(validatedTx);
            if (!confirmed) {
                throw new Error('Transaction cancelled by user');
            }
            
            // Send transaction via backend
            const response = await fetch('/api/embedded/transaction/send', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    transaction: validatedTx,
                    wallet_address: this.address
                })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Transaction failed');
            }
            
            const result = await response.json();
            return result.transaction_hash;
            
        } catch (error) {
            console.error('Transaction failed:', error);
            throw error;
        }
    }
    
    /**
     * Sign message
     */
    async signMessage(method, params) {
        try {
            const response = await fetch('/api/embedded/sign', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    method: method,
                    params: params,
                    wallet_address: this.address
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to sign message');
            }
            
            const result = await response.json();
            return result.signature;
            
        } catch (error) {
            console.error('Failed to sign message:', error);
            throw error;
        }
    }
    
    /**
     * Validate transaction against policies
     */
    async validateTransaction(tx) {
        // Get daily spending
        const dailySpent = await this.getDailySpending();
        const txValue = parseInt(tx.value || '0', 16);
        
        // Check daily limit ($1000 default)
        const dailyLimit = 1000 * 1e18; // Convert to wei
        if (dailySpent + txValue > dailyLimit) {
            throw new Error('Daily spending limit exceeded');
        }
        
        // Check if 2FA required (>$500)
        const twoFAThreshold = 500 * 1e18;
        if (txValue > twoFAThreshold) {
            await this.request2FA();
        }
        
        // Set reasonable gas limits
        if (!tx.gas) {
            tx.gas = '0x7a120'; // 500000 gas default
        }
        if (!tx.gasPrice) {
            tx.gasPrice = '0xf4240'; // 1 gwei for BASE Sepolia
        }
        
        return tx;
    }
    
    /**
     * Get daily spending for this wallet
     */
    async getDailySpending() {
        try {
            const response = await fetch(`/api/embedded/spending/daily?wallet=${this.address}`);
            const data = await response.json();
            return data.total_spent || 0;
        } catch (error) {
            console.error('Failed to get daily spending:', error);
            return 0;
        }
    }
    
    /**
     * Request 2FA verification
     */
    async request2FA() {
        // Show 2FA modal
        const code = await this.prompt2FACode();
        
        // Verify with backend
        const response = await fetch('/api/embedded/auth/verify-2fa', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code: code })
        });
        
        if (!response.ok) {
            throw new Error('2FA verification failed');
        }
        
        return true;
    }
    
    /**
     * Show transaction confirmation UI
     */
    async showTransactionConfirmation(tx) {
        return new Promise((resolve) => {
            // Create custom confirmation modal
            const modal = document.createElement('div');
            modal.className = 'coinbase-tx-modal';
            modal.innerHTML = `
                <div class="modal-backdrop"></div>
                <div class="modal-content">
                    <h3>Confirm Transaction</h3>
                    <div class="tx-details">
                        <p><strong>To:</strong> ${tx.to}</p>
                        <p><strong>Amount:</strong> ${this.formatAmount(tx.value)} ETH</p>
                        <p><strong>Gas:</strong> ${parseInt(tx.gas, 16)} units</p>
                        <p><strong>Network:</strong> BASE Sepolia</p>
                    </div>
                    <div class="modal-actions">
                        <button class="btn-cancel">Cancel</button>
                        <button class="btn-confirm">Confirm</button>
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            
            // Handle button clicks
            modal.querySelector('.btn-confirm').onclick = () => {
                document.body.removeChild(modal);
                resolve(true);
            };
            
            modal.querySelector('.btn-cancel').onclick = () => {
                document.body.removeChild(modal);
                resolve(false);
            };
            
            modal.querySelector('.modal-backdrop').onclick = () => {
                document.body.removeChild(modal);
                resolve(false);
            };
        });
    }
    
    /**
     * Prompt for email (for initial connection)
     */
    async promptForEmail() {
        // Check if we already have email from Firebase auth
        const response = await fetch('/api/embedded/auth/status');
        const data = await response.json();
        
        if (data.authenticated && data.email) {
            return data.email;
        }
        
        // Otherwise prompt user
        return new Promise((resolve) => {
            const email = prompt('Enter your email to connect wallet:');
            resolve(email);
        });
    }
    
    /**
     * Prompt for 2FA code
     */
    async prompt2FACode() {
        return new Promise((resolve) => {
            const code = prompt('Enter 2FA verification code:');
            resolve(code);
        });
    }
    
    /**
     * Format amount for display
     */
    formatAmount(hexValue) {
        if (!hexValue) return '0';
        const wei = parseInt(hexValue, 16);
        return (wei / 1e18).toFixed(6);
    }
    
    /**
     * Get balance
     */
    async getBalance(address) {
        const response = await fetch(`/api/chain/balance/${address || this.address}`);
        const data = await response.json();
        return '0x' + data.balance.toString(16);
    }
    
    /**
     * Estimate gas
     */
    async estimateGas(tx) {
        // Return reasonable defaults for BASE Sepolia
        if (tx.to && tx.data) {
            // Contract interaction
            return '0x493e0'; // 300000 gas
        }
        // Simple transfer
        return '0x5208'; // 21000 gas
    }
    
    /**
     * Make eth_call
     */
    async ethCall(params) {
        const response = await fetch('/api/chain/call', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params)
        });
        
        const data = await response.json();
        return data.result;
    }
    
    /**
     * Forward unknown methods to backend
     */
    async forwardToBackend(method, params) {
        const response = await fetch('/api/embedded/rpc', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                method: method,
                params: params,
                wallet_address: this.address
            })
        });
        
        const data = await response.json();
        return data.result;
    }
    
    /**
     * Event emitter methods for compatibility
     */
    on(event, callback) {
        if (!this._events) this._events = {};
        if (!this._events[event]) this._events[event] = [];
        this._events[event].push(callback);
    }
    
    removeListener(event, callback) {
        if (!this._events || !this._events[event]) return;
        const index = this._events[event].indexOf(callback);
        if (index > -1) {
            this._events[event].splice(index, 1);
        }
    }
    
    emit(event, data) {
        if (!this._events || !this._events[event]) return;
        this._events[event].forEach(callback => callback(data));
    }
    
    /**
     * Disconnect wallet
     */
    async disconnect() {
        this.address = null;
        this.isConnected = false;
        this.provider.selectedAddress = null;
        this.emit('disconnect');
        this.emit('accountsChanged', []);
    }
}

// Export for use in other modules
window.CoinbaseEmbeddedWallet = CoinbaseEmbeddedWallet;