# Proteus Betting & Submission Guide

## Quick Start: Interact with Markets on BASE Sepolia

This guide shows you how to place bets or create competing predictions on Proteus using the BASE Sepolia testnet.

---

## Contract Selection

| Contract | Address | Use Case |
|----------|---------|----------|
| **PredictionMarketV2** | `0x5174Da96BCA87c78591038DEe9DB1811288c9286` | **Recommended** -- full lifecycle with Levenshtein resolution |
| PredictionMarket (V1) | `0x667121e8f22570F2c521454D93D6A87e44488d93` | Deprecated -- no resolution mechanism |
| EnhancedPredictionMarket | `0x6B67Cb0DaAf78f63BD11195Df0FD9FFe4361b93C` | Requires governance bootstrap (0 active actors) |

> **Use PredictionMarketV2 for everything.** V1 is deprecated. EnhancedPredictionMarket requires active node operators.

---

## Prerequisites

1. **Wallet** - One of the following:
   - [MetaMask](https://metamask.io/download/) browser extension
   - [Coinbase Wallet](https://www.coinbase.com/wallet) browser extension
   - Email sign-in (creates embedded wallet automatically)
2. **BASE Sepolia ETH** - Get free test ETH from [BASE Sepolia Faucet](https://www.coinbase.com/faucets/base-ethereum-sepolia-faucet)
3. **Market Contract ID** - Find this on any market detail page (e.g., Market #0, Market #1, etc.)

> **Session Persistence:** Your wallet connection is automatically saved. You won't need to reconnect on page reload.

---

## Contract Information

**PredictionMarketV2:** `0x5174Da96BCA87c78591038DEe9DB1811288c9286` (recommended)
**Network:** BASE Sepolia Testnet
**Chain ID:** 84532

---

## Option 1: Bet on Existing Submissions

### Step-by-Step Process:

1. **Navigate to Market**
   - Go to the market detail page (e.g., `/proteus/market/0`)
   - You'll see the market details and current submissions

2. **Connect Wallet**
   - Click "Bet on Existing Submission"
   - MetaMask will prompt you to connect if not already connected

3. **Select Submission**
   - Review available submissions
   - Click "Select" on the submission you believe will win
   - The button will change to "Selected ✓" 

4. **Enter Bet Amount**
   - Minimum bet: 0.001 ETH
   - Enter your desired bet amount

5. **Confirm Transaction**
   - Click "Place Bet"
   - MetaMask will open showing:
     - Gas fees (usually ~0.0001 ETH)
     - Total amount (bet + gas)
   - Click "Confirm" in MetaMask

6. **Transaction Complete**
   - You'll see a success message with transaction hash
   - Your bet is now recorded on the blockchain

---

## Option 2: Create Competing Prediction

### Step-by-Step Process:

1. **Navigate to Market**
   - Go to the market detail page
   - Click "Create New Prediction"

2. **Enter Your Prediction**
   - Type your predicted text (what you think the actor will say)
   - System automatically checks for duplicates
   - If you see "This prediction already exists", modify your text

3. **Set Initial Stake**
   - Minimum stake: 0.001 ETH
   - Higher stakes may attract more bettors to your submission

4. **Submit Prediction**
   - Click "Submit Prediction"
   - MetaMask will request transaction approval
   - Confirm the transaction

5. **Success**
   - Your prediction is now live
   - Others can bet on your submission
   - You earn rewards if your prediction wins

---

## Direct Contract Interaction (Advanced)

### Using Basescan:

1. **Go to Contract on Basescan**
   ```
   https://sepolia.basescan.org/address/0x5174Da96BCA87c78591038DEe9DB1811288c9286#writeContract
   ```

2. **Connect Wallet**
   - Click "Connect to Web3"
   - Select MetaMask

3. **Submit New Prediction**
   - Find `createSubmission` function
   - Enter:
     - `_marketId`: The market number (e.g., 0, 1, 2)
     - `_predictedText`: Your prediction text
     - `payableAmount`: Your stake in ETH (minimum 0.001 ETH)
   - Click "Write"

4. **Claim Payout (after resolution)**
   - Find `claimPayout` function
   - Enter:
     - `_submissionId`: Your winning submission ID
   - Click "Write"

---

## Contract Methods Reference (PredictionMarketV2)

### Key Functions:

```solidity
// Create a new prediction market
function createMarket(string calldata _actorHandle, uint256 _duration) external returns (uint256)

// Submit a prediction with ETH stake (min 0.001 ETH)
function createSubmission(uint256 _marketId, string calldata _predictedText) external payable returns (uint256)

// Resolve market with actual text (owner only)
function resolveMarket(uint256 _marketId, string calldata _actualText) external

// Winner claims payout
function claimPayout(uint256 _submissionId) external

// Get all submissions for a market
function getMarketSubmissions(uint256 _marketId) external view returns (uint256[] memory)

// Calculate Levenshtein distance between two strings
function levenshteinDistance(string memory a, string memory b) public pure returns (uint256)
```

---

## Important Notes

### Duplicate Prevention:
- The system prevents identical predictions for the same market
- Each prediction must be unique in text content
- This ensures fair competition between submissions

### Winning Conditions:
- The submission with text closest to actual outcome wins (lowest Levenshtein distance)
- Winner takes the entire pool minus the 7% platform fee (winner-take-all)
- Ties broken by submission order (first submitter wins)
- Minimum 2 submissions required for resolution; single submissions get a full refund

### Gas Costs:
- Typical submission: ~0.0002 ETH in gas
- Typical bet: ~0.0001 ETH in gas
- Always keep extra ETH for gas fees

---

## Troubleshooting

### "Please install MetaMask"
- Install MetaMask browser extension from [metamask.io](https://metamask.io)

### "Wrong Network"
- Switch to BASE Sepolia in MetaMask
- Network will auto-switch when you interact with the site

### "Insufficient Balance"
- Get free test ETH from [BASE Sepolia Faucet](https://www.coinbase.com/faucets/base-ethereum-sepolia-faucet)
- Ensure you have enough for bet + gas fees

### "Transaction Failed"
- Check you have enough ETH for gas
- Try increasing gas limit in MetaMask settings
- Ensure you're on BASE Sepolia network

### "Duplicate Submission"
- Your exact text already exists
- Modify your prediction slightly
- Or bet on the existing submission instead

---

## Support

For additional help:
- View live markets: [/proteus/timeline](/proteus/timeline)
- Check your transactions: [BASE Sepolia Explorer](https://sepolia.basescan.org)
- Contract verification: [PredictionMarketV2 on Basescan](https://sepolia.basescan.org/address/0x5174Da96BCA87c78591038DEe9DB1811288c9286#code)

---

## Example Scenarios

### Scenario 1: Simple Bet
```
Market: "Will Elon tweet about Mars today?"
Your Action: Bet 0.01 ETH on existing submission "Going to Mars soon"
Result: If this submission wins, you get proportional payout
```

### Scenario 2: Competing Prediction
```
Market: "What will Biden say about economy?"
Existing: "Economy is strong"
Your Submission: "We need to do more for working families" 
Your Stake: 0.005 ETH
Result: Others can now bet on your submission vs existing ones
```

---

*Last Updated: February 2026*
*Network: BASE Sepolia Testnet*
*Contract: PredictionMarketV2 (`0x5174Da96BCA87c78591038DEe9DB1811288c9286`)*