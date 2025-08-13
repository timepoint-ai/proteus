# Fix: MetaMask Import Issue

## The Problem
You're entering the **wallet address** instead of the **private key**.

## What You're Entering (WRONG)
```
0x2b5fBAC3CAAf8937767b458ac6Ed38Cf0DF6b6EF
```
This is the ADDRESS (public) - like your bank account number

## What You Should Enter (CORRECT)
```
0x495e16f009afe913a0fd7cd49ccc89d22ad4c81ea6fed210998bdfb7cde39438
```
This is the PRIVATE KEY (secret) - like your password

## Quick Fix Steps

1. **Get the Private Key from Replit Secrets**
   - Go to your Replit secrets
   - Find `DEPLOYER_PRIVATE_KEY`
   - Copy the value (starts with 0x495e...)

2. **Import to MetaMask**
   - In MetaMask, select "Private Key" 
   - Paste: `0x495e16f009afe913a0fd7cd49ccc89d22ad4c81ea6fed210998bdfb7cde39438`
   - Click Import

## Understanding the Difference

| Type | Value | Purpose |
|------|-------|---------|
| **Address** | 0x2b5fBAC3CAAf8937767b458ac6Ed38Cf0DF6b6EF | Share this publicly, receive funds |
| **Private Key** | 0x495e16f009afe913a0fd7cd49ccc89d22ad4c81ea6fed210998bdfb7cde39438 | Keep SECRET, signs transactions |

## Security Note
- **Address**: Safe to share anywhere
- **Private Key**: NEVER share (except importing to your own wallet)

This is a TEST wallet for BASE Sepolia only, so it's safe for testing.