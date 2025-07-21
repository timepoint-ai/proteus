# Clockchain Schema Redesign: Competitive Submissions

## Core Concept Change

Instead of betting on whether a prediction will happen, users bet on WHICH submission (original or competitors) will be most similar to what is actually said.

## New Entity Structure

### 1. PredictionMarket
Represents a prediction market for a specific actor and time window.
```
- id: UUID
- actor_id: UUID (FK)
- start_time: DateTime
- end_time: DateTime
- oracle_wallets: JSON array
- status: active, expired, validating, resolved, cancelled
- resolution_text: Text (actual text said by actor)
- winning_submission_id: UUID (FK to Submission)
- created_at: DateTime
- resolution_time: DateTime
```

### 2. Submission (formerly Bet)
Represents a predicted text submission within a market.
```
- id: UUID
- market_id: UUID (FK to PredictionMarket)
- creator_wallet: String
- predicted_text: Text
- submission_type: 'original', 'competitor', 'null'
- initial_stake_amount: Decimal
- currency: ETH/BTC
- transaction_hash: String
- levenshtein_distance: Integer (calculated after resolution)
- total_bet_volume: Decimal (calculated)
- is_winner: Boolean
- created_at: DateTime
```

### 3. Bet (formerly Stake)
Represents a bet on which submission will win.
```
- id: UUID
- submission_id: UUID (FK to Submission)
- bettor_wallet: String
- amount: Decimal
- currency: ETH/BTC
- transaction_hash: String
- status: pending, confirmed, won, lost, refunded
- payout_amount: Decimal
- payout_transaction_hash: String
- created_at: DateTime
```

### 4. Transaction (unchanged)
### 5. OracleSubmission (mostly unchanged)
### 6. Other entities (unchanged)

## Key Business Rules

1. **Market Creation**: 
   - First submission creates the market and becomes the "original"
   - Subsequent submissions are "competitors"
   - Special "null" submission can be created (betting nothing will be said)

2. **Betting Rules**:
   - Bets can only be placed once there are at least 2 submissions
   - Bettors choose which submission they think will win
   - Betting closes when market expires (end_time reached)

3. **Resolution Process**:
   - Oracle submits actual text after end_time
   - System calculates Levenshtein distance for each submission
   - Submission with lowest distance wins
   - If no text (null case), null submission wins

4. **Payout Distribution**:
   - All bets on winning submission share the pool proportionally
   - Platform takes 5% fee
   - Losers get nothing

## Text Comparison Rules

### Allowed Characters (X.com compatible):
- All letters (a-z, A-Z)
- All numbers (0-9)
- Standard punctuation: . , ! ? ' " - : ; ( ) [ ] { }
- Spacing and line breaks
- Common symbols: @ # $ % & * + = / \ | ~ ` ^
- Emojis and Unicode characters

### Normalization Process:
1. Remove only non-X.com compatible special characters
2. Preserve capitalization, punctuation, spacing
3. Trim leading/trailing whitespace
4. No lowercasing or punctuation removal

## Migration Strategy

1. Drop all existing tables
2. Create new schema
3. Generate test data with:
   - Multiple markets with 2-5 submissions each
   - Bets distributed across submissions
   - Some resolved markets showing winner determination
   - Variety of Levenshtein distances to show competition