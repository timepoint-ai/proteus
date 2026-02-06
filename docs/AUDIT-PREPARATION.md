# Security Audit Preparation

**v0 Alpha** -- This document is pre-prepared for a future audit engagement. No auditor has been engaged yet.

**Prepared for:** External Security Auditors
**Last Updated:** February 2026
**Contact:** [Project maintainer contact]

---

## Executive Summary

Clockchain is a v0 alpha prediction market protocol where users stake ETH on predicting the exact text of social media posts. Winner determination uses **on-chain Levenshtein distance** -- a continuous scoring metric, not binary yes/no. The protocol currently uses an **owner-based resolution model** (centralized prototype) with a designed upgrade path to decentralized oracle consensus.

**Audit Focus:** The MVP contracts that would handle real user funds on BASE mainnet. No audit has been engaged yet -- this document is prepared for when that happens.

---

## Contract Inventory

### In Scope (Priority Order)

| Contract | Address (Sepolia) | Lines | Priority | Funds at Risk |
|----------|-------------------|-------|----------|---------------|
| **PredictionMarketV2** | `0x5174Da96BCA87c78591038DEe9DB1811288c9286` | 513 | CRITICAL | All user stakes |
| **GenesisNFT** | `0x1A5D4475881B93e876251303757E60E524286A24` | 288 | HIGH | NFT ownership |
| **ImprovedDistributedPayoutManager** | (not deployed) | 224 | HIGH | Fee distribution |

**Total Lines in Scope:** ~1,025 lines of Solidity

### Explicitly Out of Scope

These contracts are for future decentralization and are NOT being deployed to mainnet in the MVP:

| Contract | Reason |
|----------|--------|
| EnhancedPredictionMarket.sol | Requires governance (future) |
| DecentralizedOracle.sol | Future upgrade |
| NodeRegistry.sol | Future upgrade |
| ActorRegistry.sol | Future upgrade |
| AdvancedMarkets.sol | Experimental |
| BittensorRewardPool.sol | Future integration |
| BuilderRewardPool.sol | Future integration |

---

## PredictionMarketV2 - Detailed Analysis

**File:** `contracts/src/PredictionMarketV2.sol`
**Deployed:** BASE Sepolia at `0x5174Da96BCA87c78591038DEe9DB1811288c9286`

### Trust Model

| Role | Trust Level | Capabilities |
|------|-------------|--------------|
| **Owner** | HIGH | Resolve markets, pause contract, emergency withdraw |
| **Fee Recipient** | MEDIUM | Withdraw accumulated fees |
| **Users** | UNTRUSTED | Create markets, submit predictions, claim payouts |

**Key Trust Assumption:** Owner is trusted to honestly resolve markets with accurate text. This is acceptable for MVP but documented as centralization risk.

### State Variables

```solidity
uint256 public marketCount;           // Counter for market IDs
uint256 public submissionCount;       // Counter for submission IDs
mapping(uint256 => Market) public markets;
mapping(uint256 => Submission) public submissions;
mapping(uint256 => uint256[]) public marketSubmissions;  // marketId => submissionIds
mapping(address => uint256[]) public userSubmissions;    // user => submissionIds
mapping(address => uint256) public pendingFees;          // Pull-based fee collection
```

### Fund Flow Diagram

```
User ETH ──────────────────────────────────────────┐
                                                    │
                                                    ▼
┌──────────────────────────────────────────────────────────────────┐
│                       PredictionMarketV2                          │
│                                                                   │
│  createSubmission() ───────► market.totalPool += msg.value       │
│                                                                   │
│  resolveMarket() ──────────► winningSubmissionId set             │
│       (owner only)                                                │
│                                                                   │
│  claimPayout() ────────────► winner gets (totalPool * 93%)       │
│                               pendingFees[feeRecipient] += 7%    │
│                                                                   │
│  withdrawFees() ───────────► feeRecipient gets accumulated fees  │
│                                                                   │
│  refundSingleSubmission() ─► 100% refund (no fee) if only 1 bet  │
│                                                                   │
│  emergencyWithdraw() ──────► all submitters get refund after 7d  │
│       (owner only)                                                │
└──────────────────────────────────────────────────────────────────┘
```

### Critical Functions

#### 1. `createSubmission()` - User stakes ETH

```solidity
function createSubmission(
    uint256 _marketId,
    string calldata _predictedText
) external payable whenNotPaused nonReentrant returns (uint256)
```

**Security Properties:**
- Requires `msg.value >= MIN_BET` (0.001 ETH)
- Validates market exists and is not ended/resolved
- Enforces 1-hour betting cutoff before market end
- Text length capped at 280 chars (gas DoS prevention)
- Uses `nonReentrant` modifier

**Attack Vectors to Consider:**
- Gas griefing via long text strings
- Front-running with better prediction
- Market manipulation via large stakes

#### 2. `resolveMarket()` - Owner determines winner

```solidity
function resolveMarket(
    uint256 _marketId,
    string calldata _actualText
) external onlyOwner
```

**Security Properties:**
- Owner-only access control
- Requires minimum 2 submissions
- Requires market end time passed
- Levenshtein distance calculated on-chain
- First submitter wins ties (deterministic)

**Attack Vectors to Consider:**
- Owner collusion (accepted risk in MVP)
- Gas cost manipulation via long `_actualText`
- Tie-breaking manipulation

#### 3. `claimPayout()` - Winner withdraws funds

```solidity
function claimPayout(uint256 _submissionId) external nonReentrant
```

**Security Properties:**
- Uses `nonReentrant` modifier
- Validates submission is winning
- Validates not already claimed
- Uses pull pattern for fees (no external calls during claim)
- Low-level `call` for ETH transfer

**Attack Vectors to Consider:**
- Reentrancy (mitigated by `nonReentrant`)
- Claim racing
- Fee recipient griefing

#### 4. `levenshteinDistance()` - On-chain string comparison

```solidity
function levenshteinDistance(string memory a, string memory b) public pure returns (uint256)
```

**Security Properties:**
- Pure function, no state changes
- O(m*n) time and space complexity
- Space-optimized with two-row approach

**Gas Considerations:**
| String Length | Approximate Gas |
|---------------|-----------------|
| 50 chars each | ~400,000 |
| 100 chars each | ~1,500,000 |
| 280 chars each | ~9,000,000 |

**Attack Vectors to Consider:**
- Block gas limit DoS (mitigated by 280 char cap)
- Predictable tie resolution

### Constants

```solidity
uint256 public constant PLATFORM_FEE_BPS = 700;   // 7% fee
uint256 public constant MIN_BET = 0.001 ether;    // Minimum stake
uint256 public constant BETTING_CUTOFF = 1 hours; // No bets within 1hr of end
uint256 public constant MIN_SUBMISSIONS = 2;      // Minimum for resolution
uint256 public constant MAX_TEXT_LENGTH = 280;    // Tweet-length limit
```

### OpenZeppelin Dependencies

```solidity
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
```

**Version:** OpenZeppelin Contracts v5.0.0+

---

## GenesisNFT - Detailed Analysis

**File:** `contracts/src/GenesisNFT.sol`
**Deployed:** BASE Sepolia at `0x1A5D4475881B93e876251303757E60E524286A24`
**Status:** 60/100 minted, minting finalized

### Trust Model

| Role | Trust Level | Capabilities |
|------|-------------|--------------|
| **Contract** | IMMUTABLE | No admin functions post-deploy |
| **NFT Holders** | UNTRUSTED | Transfer, receive fee shares |

### Key Properties

- Fixed supply: 100 NFTs maximum
- 24-hour minting window
- On-chain SVG art generation
- Auto-finalization after max supply
- ERC721Enumerable for efficient holder iteration

### Security Considerations

- No owner/admin functions after deployment
- Minting window has closed (finalized)
- NFT art generated deterministically from token ID
- No external dependencies beyond OpenZeppelin

---

## ImprovedDistributedPayoutManager - Detailed Analysis

**File:** `contracts/src/ImprovedDistributedPayoutManager.sol`
**Status:** Not yet deployed

### Fee Distribution (7% Platform Fee Split)

| Recipient | Share of Fees | Share of Volume |
|-----------|--------------|-----------------|
| Genesis NFT Holders | 20% | 1.4% |
| Oracles | 20% | 1.4% |
| Node Operators | 10% | 0.7% |
| Market Creators | 20% | 1.4% |
| Builder Pool | 20% | 1.4% |
| Bittensor Pool | 10% | 0.7% |

### Critical Function: `_distributeToGenesisHolders()`

```solidity
function _distributeToGenesisHolders(uint256 totalReward, uint256 marketId) internal {
    uint256 totalMinted = genesisNFT.totalMinted();
    if (totalMinted == 0) return;

    uint256 rewardPerNFT = totalReward / totalMinted;

    for (uint256 i = 1; i <= totalMinted; i++) {
        try genesisNFT.ownerOf(i) returns (address owner) {
            if (owner != address(0) && rewardPerNFT > 0) {
                (bool success, ) = owner.call{value: rewardPerNFT}("");
                // ...
            }
        } catch { }
    }
}
```

**Security Considerations:**
- Loops through all NFT holders (max 100)
- Uses low-level `call` for ETH transfer
- Silently ignores failed transfers
- Potential dust loss from integer division

---

## Known Issues from Static Analysis

Slither analysis completed (December 2024). Summary of triaged findings:

### Fixed Issues

| Finding | Contract | Status |
|---------|----------|--------|
| locked-ether | AdvancedMarkets | FIXED - Added resolution/claim functions |

### Accepted Risks (False Positives / By Design)

| Finding | Contracts | Reason |
|---------|-----------|--------|
| arbitrary-send-eth | Multiple | Intentional transfers to configured addresses |
| incorrect-exp | OpenZeppelin | False positive in dependency |

### Items to Consider

| Finding | Severity | Recommendation |
|---------|----------|----------------|
| divide-before-multiply | Medium | Review precision in fee calculations |
| uninitialized-local | Low | Initialize variable in DecentralizedOracle |
| timestamp dependency | Low | Acceptable for non-critical timing |

See `docs/SECURITY-ANALYSIS.md` for full Slither report.

---

## Test Coverage

### Automated Tests

| Test Suite | Tests | Status |
|------------|-------|--------|
| Hardhat (Contracts) | 109 | Passing |
| Python Unit Tests | 56 | Passing |
| Integration Tests | 15 | Passing |
| **Total** | **180** | **All Passing** |

### Test Categories

**PredictionMarketV2 Tests:**
- Market creation (valid durations, edge cases)
- Submission creation (valid bets, text validation)
- Resolution logic (Levenshtein distance, tie-breaking)
- Payout claims (winner, non-winner rejection)
- Single submission refund
- Emergency withdrawal (timing, refund logic)
- Pause functionality

**GenesisNFT Tests:**
- Minting (quantity limits, payment)
- Finalization (time-based, supply-based)
- On-chain SVG generation
- Transfer restrictions

### CI/CD Pipeline

GitHub Actions runs on every push/PR:
1. Python unit tests with coverage
2. Hardhat contract tests
3. Slither security analysis
4. Ruff and Solhint linting
5. Build verification

---

## Deployment Architecture

### Current (Testnet)

```
BASE Sepolia
├── PredictionMarketV2 (0x5174...)
│   └── Owner: Single EOA
├── GenesisNFT (0x1A5D...)
│   └── No admin (finalized)
└── PayoutManager (not integrated)
```

### Planned (Mainnet)

```
BASE Mainnet
├── PredictionMarketV2 (new deployment)
│   └── Owner: Gnosis Safe 2-of-3 multisig
├── GenesisNFT (new deployment or bridge)
│   └── No admin (finalized)
└── ImprovedDistributedPayoutManager (new deployment)
    └── Integrated with PredictionMarketV2
```

---

## Specific Audit Questions

1. **Levenshtein Gas Bounds:** Is the 280-character limit sufficient to prevent block gas limit DoS?

2. **Tie Resolution:** Is first-submitter-wins acceptable? Any manipulation vectors?

3. **Fee Accumulation:** Is the pull-based `pendingFees` pattern correctly implemented?

4. **Emergency Withdraw:** Is 7-day delay after market end appropriate?

5. **Single Submission Refund:** Any edge cases where 100% refund could be exploited?

6. **NFT Distribution Loops:** Is looping through 100 NFT holders safe for gas?

7. **Integer Division:** Are there precision loss issues in fee calculations?

---

## Invariants to Verify

### PredictionMarketV2

1. `market.totalPool == sum of all submission amounts for that market`
2. Once `resolved == true`, `winningSubmissionId` never changes
3. Each submission can only be claimed once (`claimed == true`)
4. No ETH can be extracted without going through defined exit paths
5. Only owner can call `resolveMarket()` and `emergencyWithdraw()`

### GenesisNFT

1. `totalMinted() <= 100` always
2. After finalization, no new mints possible
3. Token IDs are sequential 1..totalMinted

### PayoutManager

1. Sum of all shares == TOTAL_FEE (700 bps)
2. All NFT holders receive equal share per NFT owned

---

## Documentation References

| Document | Description |
|----------|-------------|
| `docs/CONTRACTS.md` | Contract interface reference |
| `docs/SECURITY-ANALYSIS.md` | Full Slither analysis report |
| `docs/ROADMAP.md` | Development timeline and status |
| `docs/GAPS.md` | Known gaps and technical debt |
| `test/` | All test files |

---

## Contact and Access

**Repository:** [GitHub link]
**Testnet Explorer:** https://sepolia.basescan.org/

**Verified Contracts:**
- [PredictionMarketV2](https://sepolia.basescan.org/address/0x5174Da96BCA87c78591038DEe9DB1811288c9286#code)
- [GenesisNFT](https://sepolia.basescan.org/address/0x1A5D4475881B93e876251303757E60E524286A24#code)

---

*Document prepared for future security audit engagement. Updated February 2026. No auditor engaged yet.*
