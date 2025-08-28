/**
 * Embedded Wallet Integration
 * Provides email/SMS authentication without seed phrases
 */

class EmbeddedWallet {
    constructor() {
        this.walletAddress = null;
        this.token = null;
        this.authMethod = 'email';
        this.balanceUSD = 0;
        this.isAuthenticated = false;
        
        // Check if MetaMask should be hidden
        this.hideMetaMask = localStorage.getItem('hideMetaMask') !== 'false';
        
        // Initialize
        this.init();
    }
    
    init() {
        // Check for existing session
        this.checkWalletSession();
        
        // Hide MetaMask button if configured
        if (this.hideMetaMask) {
            const metamaskElements = document.querySelectorAll('.metamask-button, .connect-metamask');
            metamaskElements.forEach(el => el.style.display = 'none');
        }
    }
    
    /**
     * Show authentication modal
     */
    showAuthModal() {
        // Remove existing modal if any
        const existingModal = document.getElementById('embeddedAuthModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        const modalHTML = `
            <div id="embeddedAuthModal" class="modal" style="display: block; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.4);">
                <div class="modal-content" style="background-color: #1a1a1a; margin: 10% auto; padding: 20px; border: 1px solid #888; width: 400px; border-radius: 10px;">
                    <span class="close" onclick="embeddedWallet.closeAuthModal()" style="color: #aaa; float: right; font-size: 28px; cursor: pointer;">&times;</span>
                    <h2 style="color: #fff; text-align: center;">Get Started</h2>
                    <p style="color: #ccc; text-align: center;">Enter your email or phone to continue</p>
                    
                    <div id="authStep1" style="display: block;">
                        <input type="text" id="authIdentifier" placeholder="Email or Phone" style="width: 100%; padding: 10px; margin: 10px 0; background: #2a2a2a; color: #fff; border: 1px solid #444; border-radius: 5px;">
                        <button onclick="embeddedWallet.requestOTP()" style="width: 100%; padding: 10px; background: #4CAF50; color: white; border: none; border-radius: 5px; cursor: pointer;">Continue</button>
                    </div>
                    
                    <div id="authStep2" style="display: none;">
                        <p style="color: #ccc;">Enter the 6-digit code sent to <span id="sentTo"></span></p>
                        <input type="text" id="otpCode" placeholder="000000" maxlength="6" style="width: 100%; padding: 10px; margin: 10px 0; background: #2a2a2a; color: #fff; border: 1px solid #444; border-radius: 5px; text-align: center; font-size: 20px;">
                        <button onclick="embeddedWallet.verifyOTP()" style="width: 100%; padding: 10px; background: #4CAF50; color: white; border: none; border-radius: 5px; cursor: pointer;">Verify</button>
                        <p style="color: #888; text-align: center; margin-top: 10px;">
                            <a href="#" onclick="embeddedWallet.requestOTP(); return false;" style="color: #4CAF50;">Resend Code</a>
                        </p>
                    </div>
                    
                    <div id="authError" style="display: none; color: #f44336; text-align: center; margin-top: 10px;"></div>
                    <div id="authSuccess" style="display: none; color: #4CAF50; text-align: center; margin-top: 10px;"></div>
                    
                    <div style="text-align: center; margin-top: 20px;">
                        <a href="#" onclick="embeddedWallet.toggleAdvancedMode(); return false;" style="color: #666; font-size: 12px;">Advanced Mode</a>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
    }
    
    /**
     * Close authentication modal
     */
    closeAuthModal() {
        const modal = document.getElementById('embeddedAuthModal');
        if (modal) {
            modal.remove();
        }
    }
    
    /**
     * Request OTP code
     */
    async requestOTP() {
        const identifier = document.getElementById('authIdentifier').value;
        if (!identifier) {
            this.showError('Please enter your email or phone number');
            return;
        }
        
        // Detect auth method
        const authMethod = identifier.includes('@') ? 'email' : 'sms';
        
        try {
            const response = await fetch('/api/embedded/request-otp', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    identifier: identifier,
                    auth_method: authMethod
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Move to OTP verification step
                document.getElementById('authStep1').style.display = 'none';
                document.getElementById('authStep2').style.display = 'block';
                document.getElementById('sentTo').textContent = identifier;
                
                // For testing, show OTP if provided
                if (data.test_otp) {
                    console.log('Test OTP:', data.test_otp);
                    // Show test OTP prominently in the UI
                    document.getElementById('otpCode').value = data.test_otp;
                    this.showSuccess(`TEST MODE: Auto-filled OTP: ${data.test_otp} (In production, this would be sent via email/SMS)`);
                }
            } else {
                this.showError(data.error || 'Failed to send OTP');
            }
        } catch (error) {
            this.showError('Network error: ' + error.message);
        }
    }
    
    /**
     * Verify OTP and authenticate
     */
    async verifyOTP() {
        const identifier = document.getElementById('authIdentifier').value;
        const otpCode = document.getElementById('otpCode').value;
        
        if (!otpCode || otpCode.length !== 6) {
            this.showError('Please enter the 6-digit code');
            return;
        }
        
        try {
            const response = await fetch('/api/embedded/verify-otp', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    identifier: identifier,
                    otp_code: otpCode
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.walletAddress = data.wallet_address;
                this.token = data.token;
                this.authMethod = data.auth_method;
                this.balanceUSD = data.balance_usd || 0;
                this.isAuthenticated = true;
                
                // Store token
                localStorage.setItem('embeddedWalletToken', this.token);
                
                this.showSuccess('Successfully authenticated!');
                
                // Update UI
                this.updateUI();
                
                // Close modal after delay
                setTimeout(() => {
                    this.closeAuthModal();
                }, 1500);
                
            } else {
                this.showError(data.error || 'Invalid OTP');
            }
        } catch (error) {
            this.showError('Network error: ' + error.message);
        }
    }
    
    /**
     * Check existing wallet session
     */
    async checkWalletSession() {
        try {
            const response = await fetch('/api/embedded/wallet-info');
            const data = await response.json();
            
            if (data.success && data.wallet_address) {
                this.walletAddress = data.wallet_address;
                this.isAuthenticated = true;
                this.balanceUSD = data.balance?.balance_usd || 0;
                this.updateUI();
            }
        } catch (error) {
            console.log('No existing session');
        }
    }
    
    /**
     * Update UI with wallet info
     */
    updateUI() {
        // Update wallet address display
        const addressElements = document.querySelectorAll('.wallet-address, #walletAddress');
        addressElements.forEach(el => {
            el.textContent = this.formatAddress(this.walletAddress);
        });
        
        // Update balance display
        const balanceElements = document.querySelectorAll('.wallet-balance, #walletBalance');
        balanceElements.forEach(el => {
            el.textContent = `$${this.balanceUSD.toFixed(2)}`;
        });
        
        // Update connect button
        const connectButtons = document.querySelectorAll('.connect-wallet, #connectWallet');
        connectButtons.forEach(btn => {
            if (this.isAuthenticated) {
                btn.textContent = this.formatAddress(this.walletAddress);
                btn.style.backgroundColor = '#4CAF50';
            } else {
                btn.textContent = 'Get Started';
                btn.onclick = () => this.showAuthModal();
            }
        });
        
        // Show/hide authenticated content
        const authContent = document.querySelectorAll('.auth-required');
        authContent.forEach(el => {
            el.style.display = this.isAuthenticated ? 'block' : 'none';
        });
        
        const noAuthContent = document.querySelectorAll('.no-auth');
        noAuthContent.forEach(el => {
            el.style.display = !this.isAuthenticated ? 'block' : 'none';
        });
    }
    
    /**
     * Format wallet address for display
     */
    formatAddress(address) {
        if (!address) return '';
        return `${address.slice(0, 6)}...${address.slice(-4)}`;
    }
    
    /**
     * Show error message
     */
    showError(message) {
        const errorDiv = document.getElementById('authError');
        if (errorDiv) {
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
            setTimeout(() => {
                errorDiv.style.display = 'none';
            }, 5000);
        } else {
            console.error(message);
        }
    }
    
    /**
     * Show success message
     */
    showSuccess(message) {
        const successDiv = document.getElementById('authSuccess');
        if (successDiv) {
            successDiv.textContent = message;
            successDiv.style.display = 'block';
            setTimeout(() => {
                successDiv.style.display = 'none';
            }, 5000);
        } else {
            console.log(message);
        }
    }
    
    /**
     * Toggle advanced mode (show MetaMask)
     */
    toggleAdvancedMode() {
        const confirmed = confirm('Enable advanced mode? This will show MetaMask and other Web3 wallet options.');
        if (confirmed) {
            localStorage.setItem('hideMetaMask', 'false');
            localStorage.setItem('advanced_user_confirmed', 'true');
            
            // Show MetaMask elements
            const metamaskElements = document.querySelectorAll('.metamask-button, .connect-metamask');
            metamaskElements.forEach(el => el.style.display = 'inline-block');
            
            this.showSuccess('Advanced mode enabled');
        }
    }
    
    /**
     * Logout
     */
    async logout() {
        try {
            await fetch('/api/embedded/logout', { method: 'POST' });
            
            this.walletAddress = null;
            this.token = null;
            this.isAuthenticated = false;
            localStorage.removeItem('embeddedWalletToken');
            
            this.updateUI();
            
            // Reload page
            window.location.reload();
        } catch (error) {
            console.error('Logout failed:', error);
        }
    }
    
    /**
     * Get transaction signer
     */
    async getTransactionSigner() {
        if (!this.isAuthenticated) {
            throw new Error('Not authenticated');
        }
        
        return {
            address: this.walletAddress,
            signTransaction: async (tx) => {
                const response = await fetch('/api/embedded/sign-transaction', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        transaction: tx
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    return data.signed_tx;
                } else {
                    throw new Error(data.error || 'Transaction signing failed');
                }
            }
        };
    }
}

// Initialize embedded wallet
const embeddedWallet = new EmbeddedWallet();

// Export for use in other scripts
window.embeddedWallet = embeddedWallet;