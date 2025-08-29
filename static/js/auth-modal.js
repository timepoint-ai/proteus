/**
 * Email Authentication Modal for Coinbase Embedded Wallet
 */

class AuthModal {
    constructor() {
        this.modal = null;
        this.isAuthenticating = false;
    }
    
    show() {
        // Create modal HTML
        this.modal = document.createElement('div');
        this.modal.className = 'email-auth-modal-wrapper';
        this.modal.innerHTML = `
            <div class="modal-backdrop"></div>
            <div class="email-auth-modal">
                <h3>Sign In to Clockchain</h3>
                <p class="auth-description">Enter your email to securely access your wallet</p>
                
                <form id="email-auth-form">
                    <input 
                        type="email" 
                        id="auth-email" 
                        placeholder="Enter your email address" 
                        required
                        autocomplete="email"
                    />
                    
                    <button type="submit" id="auth-submit-btn">
                        <span class="btn-text">Continue with Email</span>
                        <span class="btn-loading d-none">
                            <span class="coinbase-loading"></span>
                            Signing in...
                        </span>
                    </button>
                </form>
                
                <div class="auth-divider">
                    <span>or</span>
                </div>
                
                <button class="auth-option-btn" id="use-metamask-btn">
                    <i class="fas fa-wallet"></i>
                    Use MetaMask (Advanced)
                </button>
                
                <button class="close-modal-btn" aria-label="Close">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        document.body.appendChild(this.modal);
        
        // Add event listeners
        this.setupEventListeners();
        
        // Focus email input
        setTimeout(() => {
            const emailInput = document.getElementById('auth-email');
            if (emailInput) emailInput.focus();
        }, 100);
    }
    
    setupEventListeners() {
        // Form submission
        const form = document.getElementById('email-auth-form');
        if (form) {
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                await this.handleEmailAuth();
            });
        }
        
        // Close button
        const closeBtn = this.modal.querySelector('.close-modal-btn');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.close());
        }
        
        // Backdrop click
        const backdrop = this.modal.querySelector('.modal-backdrop');
        if (backdrop) {
            backdrop.addEventListener('click', () => this.close());
        }
        
        // MetaMask option
        const metamaskBtn = document.getElementById('use-metamask-btn');
        if (metamaskBtn) {
            metamaskBtn.addEventListener('click', () => {
                this.close();
                this.useMetaMask();
            });
        }
        
        // ESC key to close
        document.addEventListener('keydown', this.handleEscKey = (e) => {
            if (e.key === 'Escape') this.close();
        });
    }
    
    async handleEmailAuth() {
        if (this.isAuthenticating) return;
        
        const email = document.getElementById('auth-email').value;
        if (!email) return;
        
        this.isAuthenticating = true;
        this.showLoading(true);
        
        try {
            // Send OTP to email via Firebase
            const response = await fetch('/api/embedded/auth/send-otp', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to send verification code');
            }
            
            // Show OTP input
            this.showOTPInput(email);
            
        } catch (error) {
            console.error('Authentication error:', error);
            this.showError(error.message);
            this.showLoading(false);
        } finally {
            this.isAuthenticating = false;
        }
    }
    
    showOTPInput(email) {
        const modal = this.modal.querySelector('.email-auth-modal');
        modal.innerHTML = `
            <h3>Verify Your Email</h3>
            <p class="auth-description">We sent a verification code to<br><strong>${email}</strong></p>
            
            <form id="otp-verify-form">
                <input 
                    type="text" 
                    id="otp-code" 
                    placeholder="Enter 6-digit code" 
                    maxlength="6"
                    pattern="[0-9]{6}"
                    required
                    autocomplete="one-time-code"
                />
                
                <button type="submit" id="verify-otp-btn">
                    <span class="btn-text">Verify & Connect</span>
                    <span class="btn-loading d-none">
                        <span class="coinbase-loading"></span>
                        Verifying...
                    </span>
                </button>
            </form>
            
            <button class="auth-link-btn" id="resend-code-btn">
                Resend verification code
            </button>
            
            <button class="auth-link-btn" id="change-email-btn">
                Use different email
            </button>
            
            <button class="close-modal-btn" aria-label="Close">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        // Setup OTP form listeners
        const otpForm = document.getElementById('otp-verify-form');
        if (otpForm) {
            otpForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                await this.verifyOTP(email);
            });
        }
        
        // Resend code
        const resendBtn = document.getElementById('resend-code-btn');
        if (resendBtn) {
            resendBtn.addEventListener('click', () => this.handleEmailAuth());
        }
        
        // Change email
        const changeBtn = document.getElementById('change-email-btn');
        if (changeBtn) {
            changeBtn.addEventListener('click', () => {
                this.close();
                this.show();
            });
        }
        
        // Close button
        const closeBtn = modal.querySelector('.close-modal-btn');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.close());
        }
        
        // Focus OTP input
        const otpInput = document.getElementById('otp-code');
        if (otpInput) otpInput.focus();
    }
    
    async verifyOTP(email) {
        const otp = document.getElementById('otp-code').value;
        if (!otp || otp.length !== 6) return;
        
        this.showLoading(true, 'verify-otp-btn');
        
        try {
            // Verify OTP with Firebase
            const response = await fetch('/api/embedded/auth/verify-otp', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, otp })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Invalid verification code');
            }
            
            const data = await response.json();
            
            // Connect wallet with Coinbase adapter
            await this.connectCoinbaseWallet(email);
            
            // Close modal
            this.close();
            
            // Show success
            this.showSuccess('Successfully connected your wallet!');
            
        } catch (error) {
            console.error('OTP verification error:', error);
            this.showError(error.message);
            this.showLoading(false, 'verify-otp-btn');
        }
    }
    
    async connectCoinbaseWallet(email) {
        // Set wallet type to Coinbase
        localStorage.setItem('wallet_type', 'coinbase');
        
        // Connect wallet
        if (window.clockchainWallet) {
            window.clockchainWallet.walletType = 'coinbase';
            await window.clockchainWallet.connect();
        } else {
            // Create new wallet instance
            window.clockchainWallet = new ClockchainWallet();
            await window.clockchainWallet.connect();
        }
    }
    
    useMetaMask() {
        // Switch to MetaMask
        localStorage.setItem('wallet_type', 'metamask');
        
        if (window.clockchainWallet) {
            window.clockchainWallet.walletType = 'metamask';
            window.clockchainWallet.connect();
        } else {
            window.clockchainWallet = new ClockchainWallet();
            window.clockchainWallet.connect();
        }
    }
    
    showLoading(show, buttonId = 'auth-submit-btn') {
        const btn = document.getElementById(buttonId);
        if (!btn) return;
        
        const textSpan = btn.querySelector('.btn-text');
        const loadingSpan = btn.querySelector('.btn-loading');
        
        if (show) {
            textSpan?.classList.add('d-none');
            loadingSpan?.classList.remove('d-none');
            btn.disabled = true;
        } else {
            textSpan?.classList.remove('d-none');
            loadingSpan?.classList.add('d-none');
            btn.disabled = false;
        }
    }
    
    showError(message) {
        // Remove existing error
        const existing = document.querySelector('.coinbase-message');
        if (existing) existing.remove();
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'coinbase-message error';
        errorDiv.textContent = message;
        document.body.appendChild(errorDiv);
        
        setTimeout(() => errorDiv.remove(), 5000);
    }
    
    showSuccess(message) {
        // Remove existing message
        const existing = document.querySelector('.coinbase-message');
        if (existing) existing.remove();
        
        const successDiv = document.createElement('div');
        successDiv.className = 'coinbase-message success';
        successDiv.textContent = message;
        document.body.appendChild(successDiv);
        
        setTimeout(() => successDiv.remove(), 5000);
    }
    
    close() {
        if (this.modal) {
            this.modal.remove();
            this.modal = null;
        }
        
        // Remove ESC listener
        if (this.handleEscKey) {
            document.removeEventListener('keydown', this.handleEscKey);
        }
    }
}

// Initialize auth modal globally
window.authModal = new AuthModal();