/**
 * Timeline Blockchain Integration
 * Updates the timeline view with real-time blockchain data
 */

class TimelineBlockchain {
    constructor() {
        this.updateInterval = null;
        this.lastUpdateTime = null;
        this.isUpdating = false;
        
        // Start periodic updates
        this.startUpdates();
        
        // Subscribe to blockchain events
        this.subscribeToEvents();
    }
    
    async startUpdates() {
        // Initial update
        await this.updateTimeline();
        
        // Update every 30 seconds
        this.updateInterval = setInterval(() => {
            this.updateTimeline();
        }, 30000);
    }
    
    async updateTimeline() {
        // Check if Web3 is loaded
        if (typeof Web3 === 'undefined') {
            console.log('Waiting for Web3 to load...');
            return;
        }
        
        if (this.isUpdating || !window.marketBlockchain?.initialized) {
            return;
        }
        
        this.isUpdating = true;
        
        try {
            // Get active markets from blockchain
            const markets = await window.marketBlockchain.getActiveMarkets();
            
            // Update the timeline display
            this.renderMarkets(markets);
            
            // Update statistics
            this.updateStatistics(markets);
            
            this.lastUpdateTime = new Date();
            
        } catch (error) {
            console.error('Error updating timeline:', error);
            this.showError('Failed to update from blockchain');
        } finally {
            this.isUpdating = false;
        }
    }
    
    renderMarkets(markets) {
        const container = document.querySelector('.timeline-container');
        if (!container) return;
        
        // Clear existing content except the NOW marker
        const nowMarker = container.querySelector('.bg-danger');
        container.innerHTML = '';
        
        if (markets.length === 0) {
            container.innerHTML = `
                <div class="text-center py-5">
                    <i class="fas fa-info-circle fa-3x text-muted mb-3"></i>
                    <p class="text-muted">No active markets found on blockchain</p>
                    <a href="/clockchain/create" class="btn btn-primary mt-3">
                        <i class="fas fa-plus"></i> Create First Market
                    </a>
                </div>
            `;
            return;
        }
        
        // Sort markets by end time
        markets.sort((a, b) => a.endTime - b.endTime);
        
        // Current time for NOW marker placement
        const currentTime = Date.now();
        let nowMarkerPlaced = false;
        
        markets.forEach(market => {
            // Place NOW marker if appropriate
            if (!nowMarkerPlaced && market.endTime > currentTime) {
                container.appendChild(this.createNowMarker());
                nowMarkerPlaced = true;
            }
            
            // Create market segment
            const segment = this.createMarketSegment(market);
            container.appendChild(segment);
        });
        
        // Add NOW marker at end if not placed
        if (!nowMarkerPlaced) {
            container.appendChild(this.createNowMarker());
        }
    }
    
    createNowMarker() {
        const marker = document.createElement('div');
        marker.className = 'w-100 my-4';
        marker.innerHTML = `
            <div class="d-flex align-items-center">
                <div class="bg-danger" style="height: 2px; flex: 1;"></div>
                <span class="badge bg-danger mx-2">NOW</span>
                <div class="bg-danger" style="height: 2px; flex: 1;"></div>
            </div>
        `;
        return marker;
    }
    
    createMarketSegment(market) {
        const segment = document.createElement('div');
        segment.className = 'timeline-segment mb-4';
        segment.dataset.marketId = market.id;
        
        const status = market.resolved ? 'resolved' : 
                      market.endTime > Date.now() ? 'active' : 'expired';
        
        segment.innerHTML = `
            <div class="row">
                <div class="col-2 text-end">
                    <small class="text-muted">
                        ${this.formatDate(market.startTime)}<br>
                        to<br>
                        ${this.formatDate(market.endTime)}
                    </small>
                </div>
                <div class="col-1 text-center">
                    <div class="timeline-marker bg-${status === 'resolved' ? 'success' : status === 'active' ? 'primary' : 'secondary'}" 
                         style="width: 16px; height: 16px; border-radius: 50%; margin: 0 auto; position: relative; z-index: 2;">
                    </div>
                </div>
                <div class="col-9">
                    <div class="card mb-3 ${status === 'resolved' ? 'border-success' : status === 'active' ? 'border-primary' : ''}">
                        <div class="card-body">
                            <div class="d-flex justify-content-between align-items-start mb-2">
                                <div>
                                    <h5 class="card-title mb-1">
                                        <i class="fas fa-dice me-2"></i>
                                        Market #${market.id}
                                        <span class="badge bg-${status === 'active' ? 'success' : 'secondary'} ms-2">
                                            ${status.toUpperCase()}
                                        </span>
                                    </h5>
                                    <p class="text-muted mb-2">
                                        <i class="fas fa-user me-1"></i> Actor ID: ${market.actorId}
                                    </p>
                                </div>
                                <div class="text-end">
                                    <small class="text-muted d-block">Total Pot</small>
                                    <strong class="text-primary">${market.totalPot} ETH</strong>
                                </div>
                            </div>
                            
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <span class="badge bg-info">
                                        <i class="fas fa-file-alt me-1"></i>
                                        ${market.submissionCount} submissions
                                    </span>
                                </div>
                                <div>
                                    <a href="/clockchain/market/${market.id}" class="btn btn-sm btn-outline-primary">
                                        <i class="fas fa-eye me-1"></i> View Details
                                    </a>
                                    ${status === 'active' ? `
                                        <button class="btn btn-sm btn-primary ms-2" onclick="window.location.href='/clockchain/market/${market.id}#submit'">
                                            <i class="fas fa-plus me-1"></i> Submit Prediction
                                        </button>
                                    ` : ''}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        return segment;
    }
    
    updateStatistics(markets) {
        // Update active count
        const activeCount = markets.filter(m => !m.resolved && m.endTime > Date.now()).length;
        const activeCountEl = document.querySelector('.text-muted i.fa-chart-line')?.parentElement;
        if (activeCountEl) {
            activeCountEl.innerHTML = `<i class="fas fa-chart-line"></i> Active: ${activeCount}`;
        }
        
        // Update total volume
        const totalVolume = markets.reduce((sum, m) => sum + parseFloat(m.totalPot || 0), 0);
        const volumeEl = activeCountEl?.nextSibling;
        if (volumeEl) {
            volumeEl.textContent = ` | Volume: ${totalVolume.toFixed(4)} ETH`;
        }
        
        // Update last sync time
        this.updateSyncStatus();
    }
    
    subscribeToEvents() {
        if (!window.marketBlockchain) return;
        
        window.marketBlockchain.subscribeToMarketEvents((event) => {
            console.log('Blockchain event:', event);
            
            // Show notification
            this.showNotification(event);
            
            // Update timeline after a short delay
            setTimeout(() => {
                this.updateTimeline();
            }, 2000);
        });
    }
    
    showNotification(event) {
        let message = '';
        let type = 'info';
        
        switch(event.type) {
            case 'MarketCreated':
                message = `New market created! ID: ${event.marketId}`;
                type = 'success';
                break;
            case 'SubmissionCreated':
                message = `New submission in market #${event.marketId}`;
                type = 'info';
                break;
            case 'BetPlaced':
                message = `New bet placed: ${event.amount} ETH`;
                type = 'info';
                break;
        }
        
        if (message) {
            this.showAlert(message, type);
        }
    }
    
    showAlert(message, type = 'info') {
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-5`;
        alert.style.zIndex = '9999';
        alert.style.minWidth = '300px';
        alert.innerHTML = `
            <i class="fas fa-link me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.body.appendChild(alert);
        
        setTimeout(() => {
            alert.remove();
        }, 5000);
    }
    
    showError(message) {
        console.error(message);
        // Optionally show user-friendly error
        const container = document.querySelector('.timeline-container');
        if (container && !container.querySelector('.alert-warning')) {
            const warning = document.createElement('div');
            warning.className = 'alert alert-warning alert-dismissible';
            warning.innerHTML = `
                <i class="fas fa-exclamation-triangle me-2"></i>
                Unable to fetch latest blockchain data. Showing cached results.
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            container.prepend(warning);
        }
    }
    
    updateSyncStatus() {
        const statusEl = document.createElement('div');
        statusEl.className = 'position-fixed bottom-0 end-0 m-3 text-muted small';
        statusEl.innerHTML = `
            <i class="fas fa-sync fa-spin me-1"></i>
            Last sync: ${new Date().toLocaleTimeString()}
        `;
        
        // Remove old status
        document.querySelector('.sync-status')?.remove();
        statusEl.classList.add('sync-status');
        document.body.appendChild(statusEl);
        
        // Remove after 3 seconds
        setTimeout(() => statusEl.remove(), 3000);
    }
    
    formatDate(date) {
        return new Date(date).toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }
    
    destroy() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
    }
}

// Initialize on timeline pages
document.addEventListener('DOMContentLoaded', () => {
    if (window.location.pathname.includes('/clockchain')) {
        // Wait for marketBlockchain to initialize
        const checkInterval = setInterval(() => {
            if (window.marketBlockchain?.initialized) {
                clearInterval(checkInterval);
                window.timelineBlockchain = new TimelineBlockchain();
            }
        }, 100);
    }
});