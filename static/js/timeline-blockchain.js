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
        // Wait for Web3 to be loaded first
        if (typeof Web3 === 'undefined') {
            console.log('Waiting for Web3 to load before starting timeline updates...');
            setTimeout(() => this.startUpdates(), 1000);
            return;
        }
        
        // Initial update after a delay to ensure page is loaded
        setTimeout(() => {
            this.updateTimeline();
        }, 2000);
        
        // Update every 60 seconds (less frequent to avoid clearing data)
        this.updateInterval = setInterval(() => {
            this.updateTimeline();
        }, 60000);
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
            // Get ALL markets from blockchain (both active and resolved)
            const allMarkets = await window.marketBlockchain.getAllMarkets();
            
            // Also try to get resolved markets separately
            const resolvedMarkets = await window.marketBlockchain.getResolvedMarkets();
            
            // Combine and deduplicate markets
            const marketMap = new Map();
            [...allMarkets, ...resolvedMarkets].forEach(market => {
                if (market && market.id) {
                    marketMap.set(market.id, market);
                }
            });
            
            const markets = Array.from(marketMap.values());
            
            // Update the timeline display without clearing existing data
            this.renderMarkets(markets);
            
            // Update statistics
            this.updateStatistics(markets);
            
            this.lastUpdateTime = new Date();
            
        } catch (error) {
            console.error('Error updating timeline:', error);
            // Don't show error for normal update failures
        } finally {
            this.isUpdating = false;
        }
    }
    
    renderMarkets(markets) {
        const container = document.querySelector('.timeline-container');
        if (!container) return;
        
        // Check if this is initial load or update
        const existingMarkets = container.querySelectorAll('.timeline-segment');
        const existingIds = new Set();
        existingMarkets.forEach(segment => {
            existingIds.add(segment.dataset.marketId);
        });
        
        // Don't clear content, just update or add new markets
        if (markets.length === 0 && existingIds.size === 0) {
            container.innerHTML = `
                <div class="text-center py-5">
                    <i class="fas fa-info-circle fa-3x text-muted mb-3"></i>
                    <p class="text-muted">No markets found on blockchain yet</p>
                    <a href="/proteus/create" class="btn btn-primary mt-3">
                        <i class="fas fa-plus"></i> Create First Market
                    </a>
                </div>
            `;
            return;
        }
        
        // Update or add markets without clearing existing ones
        markets.forEach(market => {
            const existingSegment = container.querySelector(`[data-market-id="${market.id}"]`);
            
            if (existingSegment) {
                // Update existing segment
                this.updateMarketSegment(existingSegment, market);
            } else {
                // Add new segment
                const segment = this.createMarketSegment(market);
                
                // Insert in correct position based on time
                const segments = container.querySelectorAll('.timeline-segment');
                let inserted = false;
                
                for (let i = 0; i < segments.length; i++) {
                    const segmentTime = parseInt(segments[i].dataset.endMs || '0');
                    if (market.endTime && market.endTime.getTime() < segmentTime) {
                        segments[i].parentNode.insertBefore(segment, segments[i]);
                        inserted = true;
                        break;
                    }
                }
                
                if (!inserted) {
                    container.appendChild(segment);
                }
            }
        });
        
        // Update NOW marker position
        this.updateNowMarker(container);
    }
    
    createNowMarker() {
        const marker = document.createElement('div');
        marker.className = 'w-100 my-4 now-marker';
        marker.innerHTML = `
            <div class="d-flex align-items-center">
                <div class="bg-danger" style="height: 2px; flex: 1;"></div>
                <span class="badge bg-danger mx-2">NOW</span>
                <div class="bg-danger" style="height: 2px; flex: 1;"></div>
            </div>
        `;
        return marker;
    }
    
    updateNowMarker(container) {
        // Remove existing NOW marker
        const existingMarker = container.querySelector('.now-marker');
        if (existingMarker) {
            existingMarker.remove();
        }
        
        // Add NOW marker in correct position
        const currentTime = Date.now();
        const segments = container.querySelectorAll('.timeline-segment');
        let markerPlaced = false;
        
        for (let i = 0; i < segments.length; i++) {
            const segmentEndMs = parseInt(segments[i].dataset.endMs || '0');
            if (segmentEndMs > currentTime) {
                segments[i].parentNode.insertBefore(this.createNowMarker(), segments[i]);
                markerPlaced = true;
                break;
            }
        }
        
        if (!markerPlaced && segments.length > 0) {
            container.appendChild(this.createNowMarker());
        }
    }
    
    updateMarketSegment(segment, market) {
        // Update segment data attributes
        if (market.endTime) {
            segment.dataset.endMs = market.endTime.getTime();
        }
        if (market.startTime) {
            segment.dataset.startMs = market.startTime.getTime();
        }
        
        // Update volume display if it exists
        const volumeElement = segment.querySelector('.total-volume');
        if (volumeElement && market.totalPot) {
            volumeElement.textContent = market.totalPot + ' ETH';
        }
        
        // Update status badge if changed
        const statusBadge = segment.querySelector('.status-badge');
        if (statusBadge && market.status) {
            statusBadge.className = `badge status-badge bg-${market.status === 'resolved' ? 'success' : 'primary'}`;
            statusBadge.textContent = market.status === 'resolved' ? 'Resolved' : 'Active';
        }
    }
    
    createMarketSegment(market) {
        const segment = document.createElement('div');
        segment.className = 'timeline-segment mb-4';
        segment.dataset.marketId = market.id;
        
        // Set data attributes for filtering
        const startMs = market.startTime ? market.startTime.getTime() : 0;
        const endMs = market.endTime ? market.endTime.getTime() : 0;
        segment.dataset.start = startMs;
        segment.dataset.end = endMs;
        segment.dataset.startMs = startMs;
        segment.dataset.endMs = endMs;
        segment.dataset.betId = market.id;
        
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
                                    <a href="/proteus/market/${market.id}" class="btn btn-sm btn-outline-primary">
                                        <i class="fas fa-eye me-1"></i> View Details
                                    </a>
                                    ${status === 'active' ? `
                                        <button class="btn btn-sm btn-primary ms-2" onclick="window.location.href='/proteus/market/${market.id}#submit'">
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
    if (window.location.pathname.includes('/proteus')) {
        // Wait for marketBlockchain to initialize
        const checkInterval = setInterval(() => {
            if (window.marketBlockchain?.initialized) {
                clearInterval(checkInterval);
                window.timelineBlockchain = new TimelineBlockchain();
            }
        }, 100);
    }
});