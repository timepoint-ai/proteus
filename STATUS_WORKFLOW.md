# Clockchain Status Workflow Documentation

## Overview
This document defines the logical status progression for all entities in the Clockchain system. Each entity has specific states that reflect its lifecycle and ensure consistency across the platform.

## Entity Status Definitions

### 1. Bet Status
Represents the lifecycle of a prediction submission.

```
active → expired → validating → resolved
                              ↘ cancelled (edge case)
```

- **active**: Bet is open, accepting stakes, within the prediction time window
- **expired**: End time has passed, awaiting oracle submissions (oracle_allowed = true)
- **validating**: Oracle submissions received, undergoing consensus voting
- **resolved**: Consensus reached, Levenshtein distance calculated, winners determined
- **cancelled**: Bet cancelled due to invalid conditions or network decision

### 2. Stake Status
Represents individual user positions on bets.

```
pending → confirmed → won/lost
                   ↘ refunded (if bet cancelled)
```

- **pending**: Stake transaction submitted to blockchain, awaiting confirmation
- **confirmed**: Stake transaction confirmed on blockchain, position active
- **won**: Stake won based on bet resolution (lowest Levenshtein distance)
- **lost**: Stake lost based on bet resolution
- **refunded**: Stake refunded if bet was cancelled

### 3. Transaction Status
Represents blockchain transaction states (used for all financial movements).

```
pending → confirmed
       ↘ failed
```

- **pending**: Transaction broadcast to blockchain, awaiting confirmation
- **confirmed**: Transaction confirmed on blockchain with sufficient blocks
- **failed**: Transaction failed or rejected by blockchain

### 4. Oracle Submission Status
Represents oracle data submission states.

```
pending → consensus
       ↘ rejected
```

- **pending**: Oracle submission awaiting consensus votes
- **consensus**: Achieved required votes for acceptance
- **rejected**: Failed to achieve consensus, deemed invalid

## Status Transition Rules

### Bet Resolution Flow
1. When `current_time > bet.end_time`: 
   - Bet status: `active` → `expired`
   - Oracle submissions become allowed

2. When first valid oracle submission arrives:
   - Bet status: `expired` → `validating`

3. When oracle consensus is reached:
   - Bet status: `validating` → `resolved`
   - Calculate Levenshtein distances
   - Determine winning stakes

4. Upon resolution:
   - All confirmed stakes → `won` or `lost`
   - Create payout transactions for winners
   - Platform fee transactions created

### Transaction Types & Relationships

1. **Initial Stake Transaction**
   - Type: `stake`
   - Created when: User places bet
   - Related to: Specific bet via `related_bet_id`

2. **Payout Transaction**
   - Type: `payout`
   - Created when: Bet resolved, stake won
   - Related to: Original bet via `related_bet_id`
   - Amount: Original stake + winnings share

3. **Platform Fee Transaction**
   - Type: `fee`
   - Created when: Bet resolved
   - Related to: Original bet via `related_bet_id`
   - Amount: Percentage of total pool

4. **Refund Transaction**
   - Type: `refund`
   - Created when: Bet cancelled
   - Related to: Original bet via `related_bet_id`
   - Amount: Original stake amount

## Data Integrity Rules

1. **Resolved Bet Constraints**:
   - All stakes must be either `won` or `lost`
   - No stakes can remain `pending` or `confirmed`
   - All related transactions must be `confirmed` or `failed`
   - No transactions can remain `pending` indefinitely

2. **Transaction Finality**:
   - Blockchain transactions (`pending` → `confirmed`/`failed`) represent blockchain state
   - Stake outcomes (`won`/`lost`) represent game logic state
   - These are separate concerns that must be tracked independently

3. **Oracle Timing Enforcement**:
   - Oracle submissions only allowed when `current_time > bet.end_time`
   - Prevents premature resolution
   - Ensures temporal integrity of predictions

## Implementation Notes

1. **Status Updates Should Be Atomic**:
   - When resolving a bet, update all related entities in a transaction
   - Prevent partial state updates

2. **Cascade Effects**:
   - Bet resolution triggers stake status updates
   - Stake wins trigger payout transaction creation
   - Transaction confirmation triggers balance updates

3. **Audit Trail**:
   - All status changes should be logged with timestamps
   - Maintain history of state transitions for accountability

## Test Data Requirements

When generating test data, ensure:
1. Resolved bets have all stakes marked as won/lost
2. All transactions for resolved bets are confirmed
3. Active bets only have pending/confirmed stakes
4. No orphaned pending transactions for resolved bets
5. Oracle submissions respect timing constraints