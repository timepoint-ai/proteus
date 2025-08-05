#!/usr/bin/env python3
"""
Production Monitoring Alert Setup for Clockchain
Sets up comprehensive monitoring for BASE mainnet deployment
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List

logger = logging.getLogger(__name__)

class MonitoringSetup:
    """Configure monitoring alerts for production"""
    
    def __init__(self):
        self.alert_configs = []
        self.webhook_url = os.environ.get('MONITORING_WEBHOOK_URL', '')
        
    def create_alert_configuration(self) -> Dict:
        """Create comprehensive monitoring configuration"""
        
        config = {
            "name": "Clockchain Production Monitoring",
            "created": datetime.utcnow().isoformat(),
            "network": "base-mainnet",
            "alerts": []
        }
        
        # 1. Contract Monitoring
        config["alerts"].extend([
            {
                "type": "contract_balance",
                "name": "Low Contract Balance Alert",
                "description": "Alert when any contract balance falls below threshold",
                "threshold": "0.01 ETH",
                "contracts": [
                    "PredictionMarket",
                    "PayoutManager",
                    "EnhancedPredictionMarket"
                ],
                "severity": "high",
                "channels": ["webhook", "email", "logs"]
            },
            {
                "type": "transaction_failed",
                "name": "Failed Transaction Alert",
                "description": "Alert on any failed contract transactions",
                "severity": "critical",
                "channels": ["webhook", "email", "logs", "sms"]
            },
            {
                "type": "emergency_function_called",
                "name": "Emergency Function Usage",
                "description": "Alert when emergency functions are called",
                "functions": [
                    "toggleEmergencyStop",
                    "pause",
                    "unpause",
                    "addToBlacklist"
                ],
                "severity": "critical",
                "channels": ["webhook", "email", "logs", "sms"]
            }
        ])
        
        # 2. Gas Price Monitoring
        config["alerts"].extend([
            {
                "type": "gas_price_spike",
                "name": "Gas Price Spike Alert",
                "description": "Alert when gas prices spike above threshold",
                "threshold": "5 gwei",
                "severity": "medium",
                "channels": ["webhook", "logs"]
            },
            {
                "type": "gas_price_low",
                "name": "Low Gas Price Opportunity",
                "description": "Alert when gas prices are very low",
                "threshold": "0.1 gwei",
                "severity": "info",
                "channels": ["webhook", "email"]
            }
        ])
        
        # 3. Oracle Monitoring
        config["alerts"].extend([
            {
                "type": "oracle_consensus_failure",
                "name": "Oracle Consensus Failure",
                "description": "Alert when oracle consensus cannot be reached",
                "threshold": "3 consecutive failures",
                "severity": "high",
                "channels": ["webhook", "email", "logs"]
            },
            {
                "type": "oracle_submission_delay",
                "name": "Oracle Submission Delay",
                "description": "Alert when oracle submissions are delayed",
                "threshold": "30 minutes",
                "severity": "medium",
                "channels": ["webhook", "logs"]
            }
        ])
        
        # 4. X.com API Monitoring
        config["alerts"].extend([
            {
                "type": "xcom_api_error",
                "name": "X.com API Error",
                "description": "Alert on X.com API failures",
                "threshold": "5 errors in 10 minutes",
                "severity": "high",
                "channels": ["webhook", "email", "logs"]
            },
            {
                "type": "xcom_rate_limit",
                "name": "X.com Rate Limit Warning",
                "description": "Alert when approaching X.com rate limits",
                "threshold": "80% of limit",
                "severity": "medium",
                "channels": ["webhook", "logs"]
            }
        ])
        
        # 5. Security Monitoring
        config["alerts"].extend([
            {
                "type": "suspicious_activity",
                "name": "Suspicious Activity Detection",
                "description": "Alert on unusual transaction patterns",
                "patterns": [
                    "Multiple failed transactions from same address",
                    "Unusually large bets",
                    "Rapid successive transactions"
                ],
                "severity": "high",
                "channels": ["webhook", "email", "logs"]
            },
            {
                "type": "blacklist_activity",
                "name": "Blacklisted Address Activity",
                "description": "Alert when blacklisted addresses attempt transactions",
                "severity": "high",
                "channels": ["webhook", "email", "logs"]
            }
        ])
        
        # 6. Performance Monitoring
        config["alerts"].extend([
            {
                "type": "high_response_time",
                "name": "High Response Time",
                "description": "Alert when API response times are high",
                "threshold": "2000ms",
                "severity": "medium",
                "channels": ["webhook", "logs"]
            },
            {
                "type": "database_connection_failure",
                "name": "Database Connection Issues",
                "description": "Alert on database connection failures",
                "severity": "critical",
                "channels": ["webhook", "email", "logs", "sms"]
            }
        ])
        
        # 7. Market Activity Monitoring
        config["alerts"].extend([
            {
                "type": "market_resolution_pending",
                "name": "Pending Market Resolution",
                "description": "Alert when markets need resolution",
                "threshold": "30 minutes after end time",
                "severity": "medium",
                "channels": ["webhook", "logs"]
            },
            {
                "type": "high_volume_activity",
                "name": "High Volume Activity",
                "description": "Alert on unusually high betting volume",
                "threshold": "10x average volume",
                "severity": "info",
                "channels": ["webhook", "logs"]
            }
        ])
        
        return config
    
    def generate_monitoring_script(self) -> str:
        """Generate monitoring script for cron job"""
        
        script = """#!/bin/bash
# Clockchain Production Monitoring Script
# Run this every 5 minutes via cron

# Configuration
WEBHOOK_URL="${MONITORING_WEBHOOK_URL}"
LOG_FILE="/var/log/clockchain/monitoring.log"
ALERT_FILE="/var/log/clockchain/alerts.json"

# Function to send alert
send_alert() {
    local alert_type=$1
    local message=$2
    local severity=$3
    
    # Log the alert
    echo "[$(date)] [$severity] $alert_type: $message" >> "$LOG_FILE"
    
    # Send webhook if configured
    if [ ! -z "$WEBHOOK_URL" ]; then
        curl -X POST "$WEBHOOK_URL" \\
            -H "Content-Type: application/json" \\
            -d '{
                "type": "'$alert_type'",
                "message": "'$message'",
                "severity": "'$severity'",
                "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
            }'
    fi
}

# Check contract balances
check_contract_balances() {
    # Add contract balance checking logic here
    echo "Checking contract balances..."
}

# Check gas prices
check_gas_prices() {
    # Add gas price checking logic here
    echo "Checking gas prices..."
}

# Check oracle status
check_oracle_status() {
    # Add oracle status checking logic here
    echo "Checking oracle status..."
}

# Main monitoring loop
main() {
    check_contract_balances
    check_gas_prices
    check_oracle_status
}

# Run main function
main
"""
        return script
    
    def create_alerting_rules(self) -> Dict:
        """Create Prometheus-style alerting rules"""
        
        rules = {
            "groups": [
                {
                    "name": "clockchain_alerts",
                    "interval": "30s",
                    "rules": [
                        {
                            "alert": "ContractLowBalance",
                            "expr": 'contract_balance_eth < 0.01',
                            "for": "5m",
                            "labels": {
                                "severity": "warning"
                            },
                            "annotations": {
                                "summary": "Contract balance is low",
                                "description": "Contract {{ $labels.contract }} balance is {{ $value }} ETH"
                            }
                        },
                        {
                            "alert": "HighGasPrice",
                            "expr": 'gas_price_gwei > 5',
                            "for": "10m",
                            "labels": {
                                "severity": "info"
                            },
                            "annotations": {
                                "summary": "Gas prices are high",
                                "description": "Current gas price is {{ $value }} gwei"
                            }
                        },
                        {
                            "alert": "OracleConsensusFailure",
                            "expr": 'oracle_consensus_failures > 3',
                            "for": "5m",
                            "labels": {
                                "severity": "critical"
                            },
                            "annotations": {
                                "summary": "Oracle consensus is failing",
                                "description": "Oracle consensus has failed {{ $value }} times"
                            }
                        },
                        {
                            "alert": "XComAPIErrors",
                            "expr": 'rate(xcom_api_errors[5m]) > 1',
                            "for": "5m",
                            "labels": {
                                "severity": "warning"
                            },
                            "annotations": {
                                "summary": "X.com API errors detected",
                                "description": "X.com API error rate is {{ $value }} per minute"
                            }
                        }
                    ]
                }
            ]
        }
        
        return rules
    
    def generate_setup_instructions(self) -> str:
        """Generate setup instructions for monitoring"""
        
        instructions = """
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
"""
        return instructions
    
    def save_configurations(self):
        """Save all monitoring configurations"""
        
        # Create monitoring directory
        os.makedirs('monitoring', exist_ok=True)
        
        # Save alert configuration
        with open('monitoring/alert_config.json', 'w') as f:
            json.dump(self.create_alert_configuration(), f, indent=2)
        
        # Save monitoring script
        with open('monitoring/monitor.sh', 'w') as f:
            f.write(self.generate_monitoring_script())
        os.chmod('monitoring/monitor.sh', 0o755)
        
        # Save Prometheus rules
        with open('monitoring/alert_rules.yml', 'w') as f:
            json.dump(self.create_alerting_rules(), f, indent=2)
        
        # Save setup instructions
        with open('monitoring/SETUP_GUIDE.md', 'w') as f:
            f.write(self.generate_setup_instructions())
        
        print("✅ Monitoring configuration files created in ./monitoring/")
        print("\n📁 Files created:")
        print("- alert_config.json - Alert definitions")
        print("- monitor.sh - Monitoring script")
        print("- alert_rules.yml - Prometheus-style rules")  
        print("- SETUP_GUIDE.md - Complete setup instructions")
        
        print("\n🚀 Quick Start:")
        print("1. Read monitoring/SETUP_GUIDE.md")
        print("2. Choose your monitoring services")
        print("3. Configure webhooks and alerts")
        print("4. Test everything works")

if __name__ == "__main__":
    setup = MonitoringSetup()
    setup.save_configurations()