
# Clockchain Production Monitoring Setup Guide

## 1. Free Monitoring Options

### Option A: Uptime Robot (Recommended for Start)
1. Sign up at https://uptimerobot.com (free for 50 monitors)
2. Add monitors for:
   - Main application URL
   - API health endpoint (/api/health)
   - Contract interaction endpoints
3. Set up email/webhook alerts

### Option B: Better Uptime
1. Sign up at https://betteruptime.com (free tier available)
2. More advanced features than Uptime Robot
3. Includes status page

### Option C: Healthchecks.io
1. Sign up at https://healthchecks.io (free for 20 checks)
2. Great for cron job monitoring
3. Add checks for scheduled tasks

## 2. Blockchain Monitoring

### Basescan Alerts (Free)
1. Go to https://basescan.org
2. Add your contract addresses to watch list
3. Set up email alerts for:
   - Incoming/outgoing transactions
   - Contract events
   - Balance changes

### Tenderly (Free Tier)
1. Sign up at https://tenderly.co
2. Add your contracts
3. Set up alerts for:
   - Failed transactions
   - Specific function calls
   - Gas spikes

## 3. Setting Up Alerts

### Step 1: Create Webhook Endpoint
```python
# Add this to your Flask app
@app.route('/monitoring/webhook', methods=['POST'])
def monitoring_webhook():
    data = request.json
    logger.warning(f"ALERT: {data.get('type')} - {data.get('message')}")
    # Add your alert handling logic here
    return jsonify({'status': 'received'}), 200
```

### Step 2: Configure Environment Variables
```bash
# Add to .env
MONITORING_WEBHOOK_URL=https://your-app.replit.app/monitoring/webhook
ALERT_EMAIL=your-email@example.com
ALERT_PHONE=+1234567890  # For critical alerts only
```

### Step 3: Set Up Cron Jobs
```bash
# Add to crontab (every 5 minutes)
*/5 * * * * /path/to/monitoring_script.sh

# Daily summary report
0 9 * * * /path/to/daily_report.sh
```

## 4. Dashboard Setup

### Option 1: Built-in Dashboard
- Already available at /admin/monitoring
- Shows real-time metrics
- No additional setup needed

### Option 2: Grafana Cloud (Free Tier)
1. Sign up at https://grafana.com
2. Create new dashboard
3. Add BASE RPC as data source
4. Import provided dashboard template

## 5. Emergency Response Plan

### Critical Alerts Response
1. **Contract Low Balance**
   - Transfer ETH immediately
   - Check for unusual activity

2. **Failed Transactions**
   - Check gas price
   - Verify contract state
   - Review transaction logs

3. **Oracle Consensus Failure**
   - Check X.com API status
   - Verify oracle nodes online
   - Manual intervention if needed

4. **Security Alert**
   - Enable emergency stop if available
   - Review suspicious addresses
   - Contact team immediately

## 6. Testing Your Monitoring

Run these tests after setup:
```bash
# Test webhook
curl -X POST your-webhook-url -H "Content-Type: application/json" -d '{"type":"test","message":"Test alert"}'

# Test email alerts
python -c "from alerts import send_test_alert; send_test_alert()"

# Test contract monitoring
node scripts/test_monitoring.js
```

## 7. Recommended Alert Thresholds

- **Contract Balance**: < 0.01 ETH (warning), < 0.005 ETH (critical)
- **Gas Price**: > 5 gwei (info), > 10 gwei (warning)
- **Response Time**: > 2s (warning), > 5s (critical)
- **Error Rate**: > 1% (warning), > 5% (critical)
- **X.com API**: > 80% rate limit (warning), errors (critical)

## Next Steps
1. Choose monitoring services based on budget
2. Set up basic uptime monitoring first
3. Add blockchain monitoring
4. Configure alert channels
5. Test all alerts work correctly
6. Document escalation procedures
