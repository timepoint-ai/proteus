/**
 * Network Status Monitor for BASE Blockchain
 * Shows connection status and gas prices
 */

class NetworkStatus {
    constructor() {
        this.statusElement = null;
        this.updateInterval = null;
        this.initializeStatus();
    }
    
    initializeStatus() {
        // Create status element
        this.statusElement = document.createElement('div');
        this.statusElement.className = 'network-status';
        this.statusElement.innerHTML = `
            <div class="status-dot"></div>
            <div class="status-text">
                <div class="network-name">Disconnected</div>
                <div class="gas-price-display d-none">Gas: <span id="gas-price">--</span> gwei</div>
            </div>
        `;
        document.body.appendChild(this.statusElement);
        
        // Start monitoring
        this.startMonitoring();
    }
    
    startMonitoring() {
        // Update immediately
        this.updateStatus();
        
        // Update every 30 seconds
        this.updateInterval = setInterval(() => {
            this.updateStatus();
        }, 30000);
    }
    
    async updateStatus() {
        if (!proteusWallet || !proteusWallet.isConnected) {
            this.showDisconnected();
            return;
        }
        
        try {
            // Get network info
            const chainId = await window.proteusWallet.provider.request({ method: 'eth_chainId' });
            const networkName = this.getNetworkName(chainId);
            
            // Get gas price (optional)
            try {
                const gasPrice = await window.proteusWallet.provider.request({
                    method: 'eth_gasPrice',
                    params: []
                });
                const gasPriceGwei = (parseInt(gasPrice, 16) / 1e9).toFixed(4);
                this.showConnected(networkName, gasPriceGwei);
            } catch (error) {
                this.showConnected(networkName);
            }
            
        } catch (error) {
            console.error('Error updating network status:', error);
            this.showDisconnected();
        }
    }
    
    getNetworkName(chainId) {
        const networks = {
            '0x1': 'Ethereum Mainnet',
            '0x2105': 'BASE Mainnet',
            '0x14a34': 'BASE Sepolia',
            '0x5': 'Goerli',
            '0xaa36a7': 'Sepolia'
        };
        return networks[chainId] || `Chain ${parseInt(chainId, 16)}`;
    }
    
    showConnected(networkName, gasPrice = null) {
        this.statusElement.classList.add('connected');
        this.statusElement.querySelector('.network-name').textContent = networkName;
        
        if (gasPrice) {
            this.statusElement.querySelector('.gas-price-display').classList.remove('d-none');
            this.statusElement.querySelector('#gas-price').textContent = gasPrice;
        }
    }
    
    showDisconnected() {
        this.statusElement.classList.remove('connected');
        this.statusElement.querySelector('.network-name').textContent = 'Disconnected';
        this.statusElement.querySelector('.gas-price-display').classList.add('d-none');
    }
    
    destroy() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
        if (this.statusElement) {
            this.statusElement.remove();
        }
    }
}

// Initialize network status monitor
let networkStatus;
document.addEventListener('DOMContentLoaded', () => {
    // Wait for wallet to be available
    setTimeout(() => {
        networkStatus = new NetworkStatus();
        
        // Update when wallet connects/disconnects
        if (window.proteusWallet && window.proteusWallet.provider) {
            window.proteusWallet.provider.on('accountsChanged', () => {
                networkStatus.updateStatus();
            });
            window.proteusWallet.provider.on('chainChanged', () => {
                networkStatus.updateStatus();
            });
        }
    }, 500);
});