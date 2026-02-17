# Coinbase Wallet Integration

Guide for integrating Coinbase Embedded Wallet with Proteus.

## Overview

Proteus uses Coinbase Embedded Wallet for seamless Web3 onboarding:
- Email/SMS authentication (no seed phrases)
- TEE-secured wallet creation
- Coinbase Onramp for easy funding

## Current Status

| Feature | Status |
|---------|--------|
| Firebase email OTP | Complete |
| Wallet session persistence | Complete |
| Multi-wallet support | Complete (MetaMask + Coinbase) |
| Mobile responsive UI | Complete |
| Coinbase SDK integration | In Progress |
| Wallet recovery flow | Not started |

## Prerequisites

1. [Coinbase Developer Platform](https://portal.cdp.coinbase.com/) account
2. Firebase project with email auth enabled

## Setup

### 1. Get Coinbase Credentials

1. Go to CDP Console > API Keys
2. Create new API key with permissions:
   - `wallet:create`
   - `wallet:read`
   - `wallet:transactions:send`
3. Download JSON credentials

### 2. Configure Environment

```bash
COINBASE_PROJECT_ID=your_project_id
COINBASE_API_KEY_NAME=organizations/your-org/apiKeys/your-key
COINBASE_API_KEY_PRIVATE_KEY=-----BEGIN EC PRIVATE KEY-----\n...\n-----END EC PRIVATE KEY-----
```

### 3. Install SDK

```bash
npm install @coinbase/waas-sdk-web
```

## Authentication Flow

```
User enters email
    │
    ▼
Firebase sends OTP
    │
    ▼
User verifies OTP
    │
    ▼
Coinbase creates wallet (TEE-secured)
    │
    ▼
JWT token issued
```

## Testing

Test the authentication flow:

```
/api/embedded/test
```

1. Enter email address
2. Check email for verification code
3. Enter code to create wallet

## Production Checklist

- [x] Firebase email authentication
- [x] Session persistence (localStorage)
- [x] Multi-wallet support
- [x] Mobile responsive CSS
- [ ] Coinbase Developer account created
- [ ] API credentials configured
- [ ] SDK installed
- [ ] Domain allowlisted in CDP Console
- [ ] Rate limiting enabled
- [ ] Wallet recovery flow

## Resources

- [Coinbase Embedded Wallets Docs](https://docs.cloud.coinbase.com/embedded-wallets)
- [CDP Console](https://portal.cdp.coinbase.com/)
- [Firebase Setup Guide](./FIREBASE-SETUP-GUIDE.md)
