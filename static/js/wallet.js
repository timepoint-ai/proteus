/**
 * Clockchain Wallet Integration for BASE Blockchain
 * Following Coinbase BASE platform best practices
 */

class ClockchainWallet {
    constructor() {
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
        
        // Check for existing connection
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
        if (typeof window.ethereum !== 'undefined') {
            try {
                const accounts = await window.ethereum.request({ method: 'eth_accounts' });
                if (accounts.length > 0) {
                    await this.connect();
                }
            } catch (error) {
                console.error('Error checking existing connection:', error);
            }
        }
    }
    
    async connect() {
        if (typeof window.ethereum === 'undefined') {
            this.showError('Please install MetaMask or another Web3 wallet to continue.');
            return;
        }
        
        try {
            // Request account access
            const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
            
            if (accounts.length === 0) {
                throw new Error('No accounts found');
            }
            
            this.address = accounts[0];
            this.provider = window.ethereum;
            this.isConnected = true;
            
            // Get current chain
            const chainId = await window.ethereum.request({ method: 'eth_chainId' });
            this.chainId = chainId;
            
            // Switch to BASE Sepolia if not on correct network
            if (chainId !== this.networks.baseSepolia.chainId) {
                await this.switchToBaseSepolia();
            }
            
            // Update UI
            this.updateConnectionStatus();
            this.updateNetworkDisplay();
            
            // Listen for account changes
            window.ethereum.on('accountsChanged', (accounts) => {
                if (accounts.length === 0) {
                    this.disconnect();
                } else {
                    this.address = accounts[0];
                    this.updateConnectionStatus();
                }
            });
            
            // Listen for chain changes
            window.ethereum.on('chainChanged', (chainId) => {
                window.location.reload();
            });
            
            this.showSuccess('Wallet connected successfully!');
            
        } catch (error) {
            console.error('Error connecting wallet:', error);
            this.showError('Failed to connect wallet: ' + error.message);
        }
    }
    
    async switchToBaseSepolia() {
        try {
            await window.ethereum.request({
                method: 'wallet_switchEthereumChain',
                params: [{ chainId: this.networks.baseSepolia.chainId }],
            });
        } catch (switchError) {
            // This error code indicates that the chain has not been added to MetaMask
            if (switchError.code === 4902) {
                try {
                    await window.ethereum.request({
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
        if (!this.isConnected || !this.address) return;
        
        try {
            const balance = await window.ethereum.request({
                method: 'eth_getBalance',
                params: [this.address, 'latest']
            });
            
            // Convert from hex wei to ETH
            const ethBalance = parseInt(balance, 16) / 1e18;
            document.getElementById('wallet-balance').textContent = ethBalance.toFixed(4) + ' ETH';
        } catch (error) {
            console.error('Error fetching balance:', error);
        }
    }
    
    async disconnect() {
        this.provider = null;
        this.signer = null;
        this.address = null;
        this.isConnected = false;
        this.chainId = null;
        this.updateConnectionStatus();
        this.updateNetworkDisplay();
        this.showSuccess('Wallet disconnected');
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
        if (!this.isConnected) {
            throw new Error('Wallet not connected');
        }
        
        try {
            const signature = await window.ethereum.request({
                method: 'personal_sign',
                params: [message, this.address],
            });
            return signature;
        } catch (error) {
            throw new Error('Failed to sign message: ' + error.message);
        }
    }
    
    async sendTransaction(params) {
        if (!this.isConnected) {
            throw new Error('Wallet not connected');
        }
        
        try {
            const txHash = await window.ethereum.request({
                method: 'eth_sendTransaction',
                params: [params],
            });
            return txHash;
        } catch (error) {
            throw new Error('Failed to send transaction: ' + error.message);
        }
    }
    
    async estimateGas(params) {
        try {
            const gas = await window.ethereum.request({
                method: 'eth_estimateGas',
                params: [params],
            });
            return gas;
        } catch (error) {
            console.error('Gas estimation failed:', error);
            return '0x30d40'; // Default gas limit
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
}

// Initialize wallet on page load
let clockchainWallet;
document.addEventListener('DOMContentLoaded', () => {
    clockchainWallet = new ClockchainWallet();
});