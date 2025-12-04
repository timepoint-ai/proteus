/**
 * Clockchain Wallet Integration for BASE Blockchain
 * Following Coinbase BASE platform best practices
 */

class ClockchainWallet {
    constructor() {
        // Session storage key
        this.SESSION_KEY = 'clockchain_wallet_session';
        this.SESSION_EXPIRY_HOURS = 24;

        // Wallet adapter pattern to support multiple wallet types
        this.walletType = localStorage.getItem('wallet_type') || 'coinbase'; // Default to Coinbase
        this.adapter = null;
        this.provider = null;
        this.signer = null;
        this.address = null;
        this.chainId = null;
        this.isConnected = false;

        // BASE network configurations
        this.networks = {
            base: {
                chainId: '0x2105', // 8453 in hex
                chainName: 'Base',
                nativeCurrency: {
                    name: 'Ethereum',
                    symbol: 'ETH',
                    decimals: 18
                },
                rpcUrls: ['https://mainnet.base.org'],
                blockExplorerUrls: ['https://basescan.org']
            },
            baseSepolia: {
                chainId: '0x14a34', // 84532 in hex
                chainName: 'Base Sepolia',
                nativeCurrency: {
                    name: 'Ethereum',
                    symbol: 'ETH',
                    decimals: 18
                },
                rpcUrls: ['https://sepolia.base.org'],
                blockExplorerUrls: ['https://sepolia.basescan.org']
            }
        };
        
        // Initialize UI elements
        this.initializeUI();
        
        // Check for existing connection based on wallet type
        this.checkExistingConnection();
    }
    
    initializeUI() {
        // Add event listeners to existing UI elements
        const connectBtn = document.getElementById('wallet-connect-btn');
        const disconnectBtn = document.getElementById('wallet-disconnect-btn');
        
        if (connectBtn) {
            connectBtn.addEventListener('click', () => {
                this.connect();
            });
        }
        
        if (disconnectBtn) {
            disconnectBtn.addEventListener('click', () => {
                this.disconnect();
            });
        }
        
        // Update network display
        this.updateNetworkDisplay();
    }
    
    async checkExistingConnection() {
        // First, try to restore from saved session
        const restored = await this.restoreSession();
        if (restored) {
            console.log('Wallet connection restored from session');
            this.updateConnectionStatus();
            this.updateNetworkDisplay();
            return;
        }

        // Fallback: Check based on wallet type without session
        if (this.walletType === 'metamask') {
            // Check if MetaMask is available and has authorized accounts
            if (typeof window.ethereum !== 'undefined') {
                try {
                    const accounts = await window.ethereum.request({ method: 'eth_accounts' });
                    if (accounts.length > 0) {
                        // MetaMask still authorized, do full connect
                        await this.connect();
                    }
                } catch (error) {
                    console.error('Error checking existing MetaMask connection:', error);
                }
            }
        } else if (this.walletType === 'coinbase') {
            // Check if user is authenticated with Firebase
            try {
                const response = await fetch('/api/embedded/auth/status');
                const data = await response.json();
                if (data.authenticated && data.wallet_address) {
                    // User is authenticated, do full connect
                    await this.connect();
                }
            } catch (error) {
                console.error('Error checking Coinbase wallet connection:', error);
            }
        }
    }
    
    async connect() {
        try {
            if (this.walletType === 'coinbase') {
                // Show email auth modal for Coinbase
                if (window.authModal) {
                    window.authModal.show();
                    return; // Auth modal will handle the connection
                } else {
                    // Fallback to direct Coinbase connection
                    await this.connectCoinbaseWallet();
                }
            } else if (this.walletType === 'metamask') {
                // Use MetaMask (legacy support)
                await this.connectMetaMask();
            } else {
                throw new Error('Unknown wallet type: ' + this.walletType);
            }
            
            // Update UI
            this.updateConnectionStatus();
            this.updateNetworkDisplay();
            this.showSuccess('Wallet connected successfully!');
            
        } catch (error) {
            console.error('Error connecting wallet:', error);
            this.showError('Failed to connect wallet: ' + error.message);
        }
    }
    
    async connectCoinbaseWallet() {
        // Load Coinbase adapter if not already loaded
        if (!window.CoinbaseEmbeddedWallet) {
            throw new Error('Coinbase Embedded Wallet not loaded. Please refresh the page.');
        }
        
        // Create adapter instance
        this.adapter = new window.CoinbaseEmbeddedWallet();
        await this.adapter.init();
        
        // Get email from current auth session or prompt
        const email = await this.getCurrentUserEmail();
        if (!email) {
            throw new Error('Please sign in with your email first');
        }
        
        // Authenticate and get wallet address
        this.address = await this.adapter.authenticate(email);
        this.provider = this.adapter.provider;
        this.isConnected = true;
        this.chainId = this.networks.baseSepolia.chainId;
        
        // Save session after successful connection
        this.saveSession();

        // Attach event listeners
        this.attachProviderListeners();
    }
    
    async connectMetaMask() {
        if (typeof window.ethereum === 'undefined') {
            throw new Error('Please install MetaMask to use this option');
        }

        // Set provider and adapter to MetaMask
        this.provider = window.ethereum;
        this.adapter = window.ethereum; // For compatibility

        // Request account access
        const accounts = await this.provider.request({ method: 'eth_requestAccounts' });

        if (accounts.length === 0) {
            throw new Error('No accounts found');
        }

        this.address = accounts[0];
        this.isConnected = true;

        // Get current chain
        const chainId = await this.provider.request({ method: 'eth_chainId' });
        this.chainId = chainId;

        // Switch to BASE Sepolia if not on correct network
        if (chainId !== this.networks.baseSepolia.chainId) {
            await this.switchToBaseSepolia();
            this.chainId = this.networks.baseSepolia.chainId;
        }

        // Save session after successful connection
        this.saveSession();

        // Attach event listeners
        this.attachProviderListeners();
    }
    
    async getCurrentUserEmail() {
        try {
            // Check Firebase auth status
            const response = await fetch('/api/embedded/auth/status');
            const data = await response.json();
            
            if (data.authenticated && data.email) {
                return data.email;
            }
            
            // Prompt for email if not authenticated
            return prompt('Enter your email to connect wallet:');
        } catch (error) {
            console.error('Error getting user email:', error);
            return null;
        }
    }
    
    async switchToBaseSepolia() {
        try {
            // Use provider (already set during connection)
            if (!this.provider) {
                throw new Error('No wallet provider available');
            }

            await this.provider.request({
                method: 'wallet_switchEthereumChain',
                params: [{ chainId: this.networks.baseSepolia.chainId }],
            });
        } catch (switchError) {
            // This error code indicates that the chain has not been added
            // Only MetaMask supports adding new chains
            if (switchError.code === 4902 && this.walletType === 'metamask' && this.provider) {
                try {
                    await this.provider.request({
                        method: 'wallet_addEthereumChain',
                        params: [this.networks.baseSepolia],
                    });
                } catch (addError) {
                    throw new Error('Failed to add BASE Sepolia network');
                }
            } else {
                throw switchError;
            }
        }
    }
    
    updateConnectionStatus() {
        const connectBtn = document.getElementById('wallet-connect-btn');
        const statusDiv = document.getElementById('wallet-status');
        const addressSpan = document.getElementById('wallet-address');
        
        if (this.isConnected && this.address) {
            connectBtn.classList.add('d-none');
            statusDiv.classList.remove('d-none');
            statusDiv.classList.add('d-flex');
            addressSpan.textContent = this.formatAddress(this.address);
            
            // Update balance
            this.updateBalance();
        } else {
            connectBtn.classList.remove('d-none');
            statusDiv.classList.add('d-none');
            statusDiv.classList.remove('d-flex');
        }
    }
    
    async updateBalance() {
        if (!this.isConnected || !this.address || !this.provider) return;

        try {
            const balance = await this.provider.request({
                method: 'eth_getBalance',
                params: [this.address, 'latest']
            });

            // Convert from hex wei to ETH
            const ethBalance = parseInt(balance, 16) / 1e18;
            const balanceElement = document.getElementById('wallet-balance');
            if (balanceElement) {
                balanceElement.textContent = ethBalance.toFixed(4) + ' ETH';
            }
        } catch (error) {
            console.error('Error fetching balance:', error);
        }
    }
    
    async disconnect() {
        // Clear session
        this.clearSession();

        // Clear state
        this.provider = null;
        this.signer = null;
        this.adapter = null;
        this.address = null;
        this.isConnected = false;
        this.chainId = null;

        // Update UI
        this.updateConnectionStatus();
        this.updateNetworkDisplay();
        this.showSuccess('Wallet disconnected');
    }

    /**
     * Explicit logout - clears all wallet data
     */
    async logout() {
        try {
            // Notify server if we have Coinbase wallet
            if (this.walletType === 'coinbase') {
                try {
                    await fetch('/auth/logout', { method: 'POST' });
                } catch (e) {
                    console.error('Server logout failed:', e);
                }
            }
        } catch (error) {
            console.error('Logout error:', error);
        }

        // Disconnect wallet
        await this.disconnect();
    }
    
    updateNetworkDisplay() {
        const networkSpan = document.getElementById('network-name');
        if (networkSpan) {
            if (this.chainId === this.networks.base.chainId) {
                networkSpan.textContent = 'BASE Mainnet';
            } else if (this.chainId === this.networks.baseSepolia.chainId) {
                networkSpan.textContent = 'BASE Sepolia';
            } else {
                networkSpan.textContent = 'Unknown Network';
            }
        }
    }
    
    formatAddress(address) {
        return address.substring(0, 6) + '...' + address.substring(38);
    }
    
    async signMessage(message) {
        if (!this.isConnected || !this.provider) {
            throw new Error('Wallet not connected');
        }

        try {
            const signature = await this.provider.request({
                method: 'personal_sign',
                params: [message, this.address],
            });
            return signature;
        } catch (error) {
            throw new Error('Failed to sign message: ' + error.message);
        }
    }
    
    async sendTransaction(params) {
        if (!this.isConnected || !this.provider) {
            throw new Error('Wallet not connected');
        }

        try {
            const txHash = await this.provider.request({
                method: 'eth_sendTransaction',
                params: [params],
            });
            return txHash;
        } catch (error) {
            throw new Error('Failed to send transaction: ' + error.message);
        }
    }
    
    async estimateGas(params) {
        if (!this.provider) {
            console.warn('No provider available for gas estimation');
            return '0x30d40'; // Default gas limit (200k)
        }

        try {
            const gas = await this.provider.request({
                method: 'eth_estimateGas',
                params: [params],
            });
            return gas;
        } catch (error) {
            console.error('Gas estimation failed:', error);
            return '0x30d40'; // Default gas limit (200k)
        }
    }
    
    showError(message) {
        this.showNotification(message, 'danger');
    }
    
    showSuccess(message) {
        this.showNotification(message, 'success');
    }
    
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
        notification.style.zIndex = '9999';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.body.appendChild(notification);

        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }

    // ================================================================
    // SESSION PERSISTENCE METHODS
    // ================================================================

    /**
     * Save wallet session to localStorage
     */
    saveSession() {
        const session = {
            walletType: this.walletType,
            address: this.address,
            chainId: this.chainId,
            connectedAt: Date.now(),
            expiresAt: Date.now() + (this.SESSION_EXPIRY_HOURS * 60 * 60 * 1000)
        };
        localStorage.setItem(this.SESSION_KEY, JSON.stringify(session));
        localStorage.setItem('wallet_type', this.walletType);
        console.log('Wallet session saved:', session);
    }

    /**
     * Load wallet session from localStorage
     * @returns {Object|null} Session object or null if invalid/expired
     */
    loadSession() {
        try {
            const sessionStr = localStorage.getItem(this.SESSION_KEY);
            if (!sessionStr) return null;

            const session = JSON.parse(sessionStr);

            // Check if session is expired
            if (session.expiresAt && Date.now() > session.expiresAt) {
                console.log('Wallet session expired');
                this.clearSession();
                return null;
            }

            // Validate session has required fields
            if (!session.walletType || !session.address) {
                console.log('Invalid wallet session');
                this.clearSession();
                return null;
            }

            return session;
        } catch (error) {
            console.error('Error loading wallet session:', error);
            this.clearSession();
            return null;
        }
    }

    /**
     * Clear wallet session from localStorage
     */
    clearSession() {
        localStorage.removeItem(this.SESSION_KEY);
        localStorage.removeItem('wallet_type');
        localStorage.removeItem('auth_token');
        localStorage.removeItem('wallet_address');
        console.log('Wallet session cleared');
    }

    /**
     * Check if a valid session exists
     * @returns {boolean}
     */
    hasValidSession() {
        return this.loadSession() !== null;
    }

    /**
     * Restore wallet connection from saved session
     * @returns {boolean} True if successfully restored
     */
    async restoreSession() {
        const session = this.loadSession();
        if (!session) {
            return false;
        }

        console.log('Attempting to restore wallet session:', session);

        try {
            // Set wallet type from session
            this.walletType = session.walletType;

            if (this.walletType === 'metamask') {
                // For MetaMask, verify the connection is still valid
                if (typeof window.ethereum !== 'undefined') {
                    const accounts = await window.ethereum.request({ method: 'eth_accounts' });
                    if (accounts.length > 0 && accounts[0].toLowerCase() === session.address.toLowerCase()) {
                        // Connection is still valid, restore state
                        this.provider = window.ethereum;
                        this.adapter = window.ethereum;
                        this.address = accounts[0];
                        this.chainId = await window.ethereum.request({ method: 'eth_chainId' });
                        this.isConnected = true;

                        // Re-attach event listeners
                        this.attachProviderListeners();

                        console.log('MetaMask session restored successfully');
                        return true;
                    }
                }
            } else if (this.walletType === 'coinbase') {
                // For Coinbase, check if user is still authenticated
                const response = await fetch('/api/embedded/auth/status');
                const data = await response.json();

                if (data.authenticated && data.wallet_address &&
                    data.wallet_address.toLowerCase() === session.address.toLowerCase()) {
                    // Re-initialize Coinbase adapter
                    if (window.CoinbaseEmbeddedWallet) {
                        this.adapter = new window.CoinbaseEmbeddedWallet();
                        await this.adapter.init();

                        // Set state from session
                        this.adapter.address = session.address;
                        this.adapter.isConnected = true;
                        this.provider = this.adapter.provider;
                        this.address = session.address;
                        this.chainId = session.chainId || this.networks.baseSepolia.chainId;
                        this.isConnected = true;

                        // Re-attach event listeners
                        this.attachProviderListeners();

                        console.log('Coinbase session restored successfully');
                        return true;
                    }
                }
            }

            // Session could not be restored
            console.log('Session restoration failed, clearing session');
            this.clearSession();
            return false;

        } catch (error) {
            console.error('Error restoring session:', error);
            this.clearSession();
            return false;
        }
    }

    /**
     * Attach event listeners to the provider
     */
    attachProviderListeners() {
        if (!this.provider) return;

        // Remove existing listeners first (if any)
        try {
            this.provider.removeListener('accountsChanged', this.handleAccountsChanged);
            this.provider.removeListener('chainChanged', this.handleChainChanged);
            this.provider.removeListener('disconnect', this.handleDisconnect);
        } catch (e) {
            // Ignore errors from removing non-existent listeners
        }

        // Bind handlers to preserve 'this' context
        this.handleAccountsChanged = this.handleAccountsChanged.bind(this);
        this.handleChainChanged = this.handleChainChanged.bind(this);
        this.handleDisconnect = this.handleDisconnect.bind(this);

        // Add listeners
        this.provider.on('accountsChanged', this.handleAccountsChanged);
        this.provider.on('chainChanged', this.handleChainChanged);

        // Some providers emit 'disconnect' event
        if (typeof this.provider.on === 'function') {
            this.provider.on('disconnect', this.handleDisconnect);
        }
    }

    /**
     * Handle account changes
     */
    handleAccountsChanged(accounts) {
        console.log('Accounts changed:', accounts);
        if (accounts.length === 0) {
            // User disconnected wallet
            this.handleDisconnect();
        } else if (accounts[0].toLowerCase() !== this.address?.toLowerCase()) {
            // User switched accounts - update and save session
            this.address = accounts[0];
            this.saveSession();
            this.updateConnectionStatus();
        }
    }

    /**
     * Handle chain changes
     */
    handleChainChanged(chainId) {
        console.log('Chain changed:', chainId);
        this.chainId = chainId;
        this.saveSession();
        // Reload page on chain change to reset state
        window.location.reload();
    }

    /**
     * Handle disconnect
     */
    handleDisconnect() {
        console.log('Wallet disconnected');
        this.clearSession();
        this.provider = null;
        this.adapter = null;
        this.address = null;
        this.isConnected = false;
        this.chainId = null;
        this.updateConnectionStatus();
        this.updateNetworkDisplay();
    }
}

// Initialize wallet on page load
let clockchainWallet;
document.addEventListener('DOMContentLoaded', () => {
    clockchainWallet = new ClockchainWallet();
});