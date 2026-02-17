/**
 * Email Authentication Modal for Coinbase Embedded Wallet
 */

class AuthModal {
    constructor() {
        this.modal = null;
        this.isAuthenticating = false;
        this.previouslyFocused = null;
    }

    show() {
        // Store previously focused element for focus restoration
        this.previouslyFocused = document.activeElement;

        // Create modal HTML
        this.modal = document.createElement('div');
        this.modal.className = 'email-auth-modal-wrapper';
        this.modal.innerHTML = `
            <div class="modal-backdrop"></div>
            <div class="email-auth-modal" role="dialog" aria-modal="true" aria-labelledby="auth-modal-title" aria-describedby="auth-modal-desc">
                <h3 id="auth-modal-title">Sign In to Proteus</h3>
                <p id="auth-modal-desc" class="auth-description">Enter your email to securely access your wallet</p>

                <!-- Live region for status announcements -->
                <div id="auth-status" class="sr-only" aria-live="polite" aria-atomic="true"></div>

                <form id="email-auth-form">
                    <label for="auth-email" class="sr-only">Email address</label>
                    <input
                        type="email"
                        id="auth-email"
                        placeholder="Enter your email address"
                        required
                        autocomplete="email"
                        aria-required="true"
                        aria-describedby="auth-modal-desc"
                    />

                    <button type="submit" id="auth-submit-btn" aria-describedby="auth-status">
                        <span class="btn-text">Continue with Email</span>
                        <span class="btn-loading d-none" aria-hidden="true">
                            <span class="coinbase-loading"></span>
                            Signing in...
                        </span>
                    </button>
                </form>

                <div class="auth-divider" aria-hidden="true">
                    <span>or</span>
                </div>

                <button class="auth-option-btn" id="use-metamask-btn">
                    <i class="fas fa-wallet" aria-hidden="true"></i>
                    Use External Wallet (Advanced)
                </button>

                <button class="close-modal-btn" aria-label="Close sign in dialog">
                    <i class="fas fa-times" aria-hidden="true"></i>
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

    /**
     * Announce a message to screen readers
     */
    announceStatus(message) {
        const statusRegion = document.getElementById('auth-status');
        if (statusRegion) {
            statusRegion.textContent = message;
        }
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
            const response = await fetch('/api/embedded/request-otp', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ identifier: email, auth_method: 'email' })
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
            <h3 id="otp-modal-title">Verify Your Email</h3>
            <p id="otp-modal-desc" class="auth-description">We sent a verification code to<br><strong>${email}</strong></p>

            <!-- Live region for status announcements -->
            <div id="auth-status" class="sr-only" aria-live="polite" aria-atomic="true"></div>

            <form id="otp-verify-form" aria-labelledby="otp-modal-title">
                <label for="otp-code" class="sr-only">6-digit verification code</label>
                <input
                    type="text"
                    id="otp-code"
                    placeholder="Enter 6-digit code"
                    maxlength="6"
                    pattern="[0-9]{6}"
                    required
                    autocomplete="one-time-code"
                    aria-required="true"
                    aria-describedby="otp-modal-desc"
                    inputmode="numeric"
                />

                <button type="submit" id="verify-otp-btn" aria-describedby="auth-status">
                    <span class="btn-text">Verify & Connect</span>
                    <span class="btn-loading d-none" aria-hidden="true">
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

            <button class="close-modal-btn" aria-label="Close verification dialog">
                <i class="fas fa-times" aria-hidden="true"></i>
            </button>
        `;

        // Announce for screen readers
        this.announceStatus(`Verification code sent to ${email}. Please enter the 6-digit code.`);
        
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
            const response = await fetch('/api/embedded/verify-otp', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ identifier: email, otp_code: otp })
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
        if (window.proteusWallet) {
            window.proteusWallet.walletType = 'coinbase';
            await window.proteusWallet.connect();
        } else {
            // Create new wallet instance
            window.proteusWallet = new ProteusWallet();
            await window.proteusWallet.connect();
        }
    }
    
    useMetaMask() {
        // Switch to MetaMask
        localStorage.setItem('wallet_type', 'metamask');
        
        if (window.proteusWallet) {
            window.proteusWallet.walletType = 'metamask';
            window.proteusWallet.connect();
        } else {
            window.proteusWallet = new ProteusWallet();
            window.proteusWallet.connect();
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
            loadingSpan?.setAttribute('aria-hidden', 'false');
            btn.disabled = true;
            btn.setAttribute('aria-busy', 'true');
            this.announceStatus('Loading, please wait...');
        } else {
            textSpan?.classList.remove('d-none');
            loadingSpan?.classList.add('d-none');
            loadingSpan?.setAttribute('aria-hidden', 'true');
            btn.disabled = false;
            btn.setAttribute('aria-busy', 'false');
        }
    }

    showError(message) {
        // Remove existing error
        const existing = document.querySelector('.coinbase-message');
        if (existing) existing.remove();

        const errorDiv = document.createElement('div');
        errorDiv.className = 'coinbase-message error';
        errorDiv.setAttribute('role', 'alert');
        errorDiv.setAttribute('aria-live', 'assertive');
        errorDiv.textContent = message;
        document.body.appendChild(errorDiv);

        // Also announce via live region
        this.announceStatus(`Error: ${message}`);

        setTimeout(() => errorDiv.remove(), 5000);
    }

    showSuccess(message) {
        // Remove existing message
        const existing = document.querySelector('.coinbase-message');
        if (existing) existing.remove();

        const successDiv = document.createElement('div');
        successDiv.className = 'coinbase-message success';
        successDiv.setAttribute('role', 'status');
        successDiv.setAttribute('aria-live', 'polite');
        successDiv.textContent = message;
        document.body.appendChild(successDiv);

        // Also announce via live region
        this.announceStatus(message);

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

        // Restore focus to previously focused element
        if (this.previouslyFocused && typeof this.previouslyFocused.focus === 'function') {
            this.previouslyFocused.focus();
            this.previouslyFocused = null;
        }
    }
}

// Initialize auth modal globally
window.authModal = new AuthModal();