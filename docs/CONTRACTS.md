# Smart Contracts

Reference for deployed Clockchain smart contracts.

## BASE Sepolia (Testnet)

| Contract | Address | Description | Status |
|----------|---------|-------------|--------|
| **PredictionMarketV2** | `0x5174Da96BCA87c78591038DEe9DB1811288c9286` | Full resolution with Levenshtein | **RECOMMENDED - Active** |
| PredictionMarket (V1) | `0x667121e8f22570F2c521454D93D6A87e44488d93` | Simple market (no resolution) | **Deprecated** |
| GenesisNFT | `0x1A5D4475881B93e876251303757E60E524286A24` | 100 founder NFTs (60 minted, finalized) | Deployed |
| EnhancedPredictionMarket | `0x6b67cb0daaf78f63bd11195df0fd9ffe4361b93c` | Full governance market (requires actors) | Requires governance |
| ActorRegistry | `0xC71CC19C5573C5E1E144829800cD0005D0eDB723` | X.com actor management | 0 active actors |
| NodeRegistry | `0xA69C842F335dfE1F69288a70054A34018282218d` | Node operator staking | 0 active nodes |
| PayoutManager | `0x88d399C949Ff2f1aaa8eA5a859Ae4d97c74f6871` | Fee distribution | Deployed |
| DecentralizedOracle | `0x7EF22e27D44E3f4Cc2f133BB4ab2065D180be3C1` | Text validation | Deployed |

> **Recommended:** Use **PredictionMarketV2** for all new development. It has complete market lifecycle with on-chain winner determination via Levenshtein distance algorithm.

## Security Analysis

Slither static analysis completed (December 2024):
- **277 findings** triaged
- **1 real bug** found and fixed (AdvancedMarkets locked-ether)
- **PredictionMarket (simple)** has no high/medium severity issues

See [SECURITY-ANALYSIS.md](SECURITY-ANALYSIS.md) for full details.

## BASE Mainnet

Not yet deployed. Pending external security audit.

---

## Governance Architecture

EnhancedPredictionMarket uses a decentralized governance model:

```
NodeRegistry (100 ETH stake)
    │
    ▼ (active nodes can propose)
ActorRegistry (3 node approvals needed)
    │
    ▼ (active actors required)
EnhancedPredictionMarket (market creation)
```

**Current State (Testnet):**
- Active Nodes: 0
- Active Actors: 0
- Markets: Not creatable via EnhancedPredictionMarket

**For Testing:** Use `PredictionMarketV2` which has complete market lifecycle without governance requirements.

---

## Contract Descriptions

### GenesisNFT

ERC-721 NFT with fixed 100 supply.

**Key Features:**
- On-chain SVG art generation
- 24-hour minting window
- Automatic finalization after max supply

**Key Functions:**
```solidity
function mint(address to, uint256 quantity) external payable
function tokenURI(uint256 tokenId) public view returns (string memory)
function totalSupply() public view returns (uint256)
```

### ImprovedDistributedPayoutManager

Distributes platform fees to stakeholders.

**Fee Distribution:**
- Genesis NFT Holders: 20% of fees (1.4% of volume)
- Oracles: 28.6% of fees
- Market Creators: 14.3% of fees
- Node Operators: 14.3% of fees
- Builder Pool: 28.6% of fees

**Key Functions:**
```solidity
function distributeFees(uint256 marketId) external
function claimRewards(address recipient) external
function getPendingRewards(address holder) public view returns (uint256)
```

### EnhancedPredictionMarket

Core market logic for predictions and bets.

**Key Functions:**
```solidity
function createMarket(
    uint256 actorId,
    string memory description,
    uint256 endTime,
    address[] memory oracles
) external payable returns (uint256 marketId)

function submitPrediction(
    uint256 marketId,
    string memory predictedText
) external payable returns (uint256 submissionId)

function placeBet(
    uint256 marketId,
    uint256 submissionId
) external payable

function resolveMarket(
    uint256 marketId,
    string memory actualText
) external

function getMarketSubmissions(uint256 marketId)
    external view returns (Submission[] memory)
```

### DecentralizedOracle

Validates text and calculates similarity.

**Key Functions:**
```solidity
function submitOracleData(
    uint256 marketId,
    string memory actualText,
    string memory proofHash
) external

function calculateLevenshteinDistance(
    string memory a,
    string memory b
) public pure returns (uint256)

function getConsensusText(uint256 marketId)
    external view returns (string memory)
```

### ActorRegistry

On-chain registry for X.com actors with decentralized approval.

**Key Features:**
- Actors proposed by active node operators
- Requires 3 node approvals to activate
- 24-hour voting period for proposals

**Key Functions:**
```solidity
function proposeActor(
    string memory xUsername,
    string memory displayName,
    string memory bio,
    string memory profileImageUrl,
    bool verified,
    uint256 followerCount,
    bool isTestAccount
) external returns (bytes32 proposalId)

function voteOnProposal(bytes32 proposalId, bool support) external

function isActorActive(string memory xUsername) external view returns (bool)

function getActiveActors() external view returns (string[] memory)
```

### NodeRegistry

Decentralized node operator management with staking.

**Key Features:**
- 100 ETH minimum stake required
- 24-hour voting period for activation
- 51% quorum for decisions
- 7-day inactivity deactivation

**Key Functions:**
```solidity
function registerNode(string memory endpoint) external payable

function heartbeat() external  // Keep node active

function getActiveNodes() external view returns (address[] memory)

function getNodeDetails(address operator) external view returns (
    uint256 stake,
    uint256 reputation,
    bool active,
    string memory endpoint,
    uint256 totalRewards
)
```

### PredictionMarketV2 (Recommended)

**Address:** `0x5174Da96BCA87c78591038DEe9DB1811288c9286`

Full-featured prediction market with on-chain winner determination using Levenshtein distance.

**Key Features:**
- Complete market lifecycle: create → submit → resolve → claim
- On-chain Levenshtein distance calculation for winner selection
- Pull-based fee collection (7% platform fee)
- First-submitter wins in case of tie (deterministic)
- Emergency withdrawal after 7 days
- Pausable by owner for emergencies

**State-Changing Functions:**
```solidity
// Create a prediction market (1 hour to 30 days duration)
function createMarket(
    string calldata _actorHandle,
    uint256 _duration
) external whenNotPaused returns (uint256)

// Submit a prediction with ETH stake (min 0.001 ETH)
function createSubmission(
    uint256 _marketId,
    string calldata _predictedText
) external payable whenNotPaused nonReentrant returns (uint256)

// Resolve market with actual text (owner only)
function resolveMarket(
    uint256 _marketId,
    string calldata _actualText
) external onlyOwner

// Winner claims payout (pool minus 7% fee)
function claimPayout(uint256 _submissionId) external nonReentrant

// Refund if only 1 submission (no fee charged)
function refundSingleSubmission(uint256 _marketId) external nonReentrant

// Withdraw accumulated fees (fee recipient only)
function withdrawFees() external nonReentrant

// Emergency refund after 7 days (owner only)
function emergencyWithdraw(uint256 _marketId) external onlyOwner nonReentrant
```

**View Functions:**
```solidity
function getMarketDetails(uint256 _marketId) external view returns (
    string memory actorHandle,
    uint256 endTime,
    uint256 totalPool,
    bool resolved,
    uint256 winningSubmissionId,
    address creator,
    uint256[] memory submissionIds
)

function getSubmissionDetails(uint256 _submissionId) external view returns (
    uint256 marketId,
    address submitter,
    string memory predictedText,
    uint256 amount,
    bool claimed
)

function getMarketSubmissions(uint256 _marketId) external view returns (uint256[] memory)
function getUserSubmissions(address _user) external view returns (uint256[] memory)
function levenshteinDistance(string memory a, string memory b) public pure returns (uint256)
```

**Events:**
```solidity
event MarketCreated(uint256 indexed marketId, string actorHandle, uint256 endTime, address creator);
event SubmissionCreated(uint256 indexed submissionId, uint256 indexed marketId, address submitter, string predictedText, uint256 amount);
event MarketResolved(uint256 indexed marketId, uint256 winningSubmissionId, string actualText, uint256 winningDistance);
event PayoutClaimed(uint256 indexed submissionId, address indexed claimer, uint256 amount);
event SingleSubmissionRefunded(uint256 indexed marketId, uint256 indexed submissionId, address submitter, uint256 amount);
event FeesWithdrawn(address indexed recipient, uint256 amount);
```

**Constants:**
| Constant | Value | Description |
|----------|-------|-------------|
| `PLATFORM_FEE_BPS` | 700 | 7% platform fee on payouts |
| `MIN_BET` | 0.001 ETH | Minimum stake for submissions |
| `BETTING_CUTOFF` | 1 hour | No submissions allowed within 1 hour of end |
| `MIN_SUBMISSIONS` | 2 | Minimum submissions required for resolution |
| `MAX_TEXT_LENGTH` | 280 | Maximum prediction text length (tweet-sized) |

**Gas Limits:**
| Operation | Typical Gas | Notes |
|-----------|-------------|-------|
| createMarket | ~120,000 | Creating new market |
| createSubmission | ~200,000-400,000 | Depends on text length |
| resolveMarket | ~1,500,000-9,000,000 | Levenshtein calculation, varies by text length |
| claimPayout | ~90,000 | Winner claiming funds |

> **Note:** Resolution gas costs depend on submission text lengths due to Levenshtein algorithm.

---

### PredictionMarket (V1 - Deprecated)

**Address:** `0x667121e8f22570F2c521454D93D6A87e44488d93`

> **Warning:** This contract has no resolution mechanism. Use PredictionMarketV2 instead.

Core prediction market without governance requirements. Originally used for testing but has a critical gap: no way to determine winners.

**Key Functions:**
```solidity
function createMarket(
    string memory question,
    uint256 duration,
    string memory actorTwitterHandle,
    bool xcomOnly
) external payable returns (uint256 marketId)

function createSubmission(
    uint256 marketId,
    string memory predictedText,
    string memory screenshotIpfsHash
) external payable returns (uint256 submissionId)

function placeBet(uint256 submissionId) external payable returns (uint256 betId)
```

**Minimums:**
- Market creation: 0.01 ETH
- Submission stake: 0.001 ETH
- Bet amount: 0.0001 ETH

**Limitation:** No `resolveMarket` function - cannot determine winners or distribute payouts.

---

## Gas Limits

| Operation | Gas Limit |
|-----------|-----------|
| Create Market | 500,000 |
| Submit Prediction | 300,000 |
| Place Bet | 200,000 |
| Resolve Market | 400,000 |
| Mint NFT | 200,000 |

Gas price: 1 gwei on BASE

---

## Verification

All contracts are verified on Basescan. View source code:

```
https://sepolia.basescan.org/address/<CONTRACT_ADDRESS>#code
```

---

## Interacting with Contracts

### Using Hardhat Console

```bash
npx hardhat console --network baseSepolia
```

```javascript
const market = await ethers.getContractAt(
  "EnhancedPredictionMarket",
  "0x6b67cb0daaf78f63bd11195df0fd9ffe4361b93c"
);

const count = await market.getMarketCount();
console.log("Total markets:", count.toString());
```

### Using Web3.py

```python
from web3 import Web3

w3 = Web3(Web3.HTTPProvider("https://sepolia.base.org"))
contract = w3.eth.contract(address=address, abi=abi)
market_count = contract.functions.getMarketCount().call()
```

---

## Events

### EnhancedPredictionMarket

```solidity
event MarketCreated(uint256 indexed marketId, uint256 actorId, address creator);
event SubmissionAdded(uint256 indexed marketId, uint256 submissionId, address submitter);
event BetPlaced(uint256 indexed marketId, uint256 submissionId, address bettor, uint256 amount);
event MarketResolved(uint256 indexed marketId, uint256 winningSubmissionId, string actualText);
```

### GenesisNFT

```solidity
event Transfer(address indexed from, address indexed to, uint256 indexed tokenId);
event MintingFinalized(uint256 totalSupply);
```
