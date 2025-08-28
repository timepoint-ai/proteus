# Coinbase Embedded Wallet Integration Guide

## Current Status: Mock Implementation

The current implementation is a **test/mock version** that simulates the Coinbase Embedded Wallet flow without actually connecting to Coinbase services.

### How to Test the Mock Implementation

1. **Navigate to**: `/api/embedded/test`
2. **Click "Get Started"**
3. **Enter any email or phone number** (e.g., your.email@example.com)
4. **Click "Continue"**
5. **The OTP code will be auto-filled** in the verification field
6. **Click "Verify"** to create your test wallet

**Note**: No actual emails or SMS messages are sent. The OTP is generated locally and displayed in the UI for testing purposes.

## Real Coinbase Integration Requirements

To connect to actual Coinbase services and send real OTP codes via email/SMS, you need:

### 1. Coinbase Developer Platform Account

1. **Sign up** at [Coinbase Developer Platform (CDP)](https://portal.cdp.coinbase.com/)
2. **Create a project** in the CDP console
3. **Get your Project ID** from the dashboard

### 2. API Credentials Setup

```bash
# Required credentials (add to .env file)
COINBASE_PROJECT_ID=your_project_id_here
COINBASE_API_KEY_NAME=organizations/your-org/apiKeys/your-key
COINBASE_API_KEY_PRIVATE_KEY=-----BEGIN EC PRIVATE KEY-----\n...\n-----END EC PRIVATE KEY-----
```

#### How to Get Credentials:
1. Go to **CDP Console → API Keys**
2. Click **"New API key"**
3. Select permissions:
   - `wallet:create` - Create wallets
   - `wallet:read` - Read wallet info
   - `wallet:transactions:send` - Send transactions
4. Download the JSON file containing your credentials
5. Extract the `projectId`, `name`, and `privateKey`

### 3. Install Real SDK Packages

```bash
# For production Coinbase integration
npm install @coinbase/waas-sdk-web @coinbase/waas-sdk-viem
```

### 4. Update Backend Service

Replace the mock `EmbeddedWalletService` with actual Coinbase SDK integration:

```python
# services/embedded_wallet.py - Production version
from coinbase_sdk import CoinbaseClient

class EmbeddedWalletService:
    def __init__(self):
        self.client = CoinbaseClient(
            api_key_name=os.environ['COINBASE_API_KEY_NAME'],
            api_key_private_key=os.environ['COINBASE_API_KEY_PRIVATE_KEY']
        )
        
    def send_otp(self, identifier: str):
        """Send real OTP via Coinbase"""
        return self.client.auth.send_otp(
            identifier=identifier,
            channel='email' if '@' in identifier else 'sms'
        )
```

### 5. Frontend SDK Integration

```javascript
// Initialize Coinbase SDK
import { InitializeWaas } from '@coinbase/waas-sdk-web';

const waas = await InitializeWaas({
    enableHostedBackups: true,
    projectId: "YOUR_PROJECT_ID",
    prod: false  // Set to true for mainnet
});

// Create wallet with email/SMS
const wallet = await waas.create({
    authMethod: 'email',
    identifier: 'user@example.com',
    passcode: '123456'  // OTP from email
});
```

## Key Differences: Mock vs Production

| Feature | Mock (Current) | Production (Coinbase) |
|---------|---------------|----------------------|
| **OTP Delivery** | Auto-filled in UI | Sent via email/SMS |
| **Wallet Creation** | Generates test address | Creates real wallet with MPC |
| **Security** | Basic key derivation | TEE + secure enclaves |
| **Backup** | Local only | Hosted by Coinbase |
| **Network** | BASE Sepolia only | Multiple networks |
| **USDC** | Mock balances | Real USDC tokens |
| **Gas Fees** | Not required | Required for transactions |

## Production Deployment Checklist

- [ ] **Coinbase Developer Account** created
- [ ] **Project ID** obtained from CDP console  
- [ ] **API credentials** configured in environment
- [ ] **SDK packages** installed (`@coinbase/waas-sdk-web`)
- [ ] **Email/SMS service** enabled in Coinbase settings
- [ ] **Allowlist domains** configured for production URL
- [ ] **Security policies** configured (transaction limits, 2FA)
- [ ] **Remove test mode** flags and mock OTP display
- [ ] **Test with real email/phone** numbers
- [ ] **Implement error handling** for failed OTP delivery

## Security Best Practices

1. **Never expose API keys** in frontend code
2. **Use environment variables** for all credentials
3. **Enable IP allowlisting** in CDP console
4. **Set transaction limits** via policy engine
5. **Require 2FA** for large transactions
6. **Implement rate limiting** on OTP requests
7. **Use HTTPS only** in production
8. **Monitor for suspicious activity**

## Testing Flow Comparison

### Mock Testing (Current)
```
User enters email → Mock OTP generated → Auto-filled → Test wallet created
```

### Production Flow (With Coinbase)
```
User enters email → Coinbase sends OTP → User enters code → Real wallet created with MPC
```

## Troubleshooting

### Common Issues

1. **"OTP not sent"** - Check Coinbase API credentials and email/SMS settings
2. **"Invalid project ID"** - Verify project ID matches CDP console
3. **"Unauthorized"** - Check API key permissions and IP allowlist
4. **"Network error"** - Ensure BASE RPC URL is accessible
5. **"Wallet creation failed"** - Check Coinbase service status

## Next Steps

1. **For Testing**: Use the current mock implementation at `/api/embedded/test`
2. **For Production**: 
   - Sign up for Coinbase Developer Platform
   - Get API credentials
   - Update environment variables
   - Install production SDK
   - Replace mock service with real integration

## Support Resources

- [Coinbase Embedded Wallets Docs](https://docs.cloud.coinbase.com/embedded-wallets)
- [SDK GitHub Repository](https://github.com/coinbase/waas-sdk-web)
- [CDP Console](https://portal.cdp.coinbase.com/)
- [API Reference](https://docs.cdp.coinbase.com/embedded-wallets/reference)