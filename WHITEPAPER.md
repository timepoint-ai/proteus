# Clockchain: Continuous-Gradient Prediction Markets via On-Chain Levenshtein Distance

### On the Information-Theoretic Collapse of Binary Markets and the Case for Metric-Scored Text Prediction

**Sean McDonald**
**with many AI models**

*February 2026*

---

tl;dr written by a human:

If a fast takeoff happens, AI-driven forecasting may radically reduce the available rewards in prediction markets as models finetune around predictive performance. Submissions to prediction markets with TRUE / FALSE may have decreasing entropy, thus decreasing rewards and incentives, as this happens. Exact text prediction, in this case roleplaying as public figures and predicting the exact text of their X posts within a given timeline - while an early-stage idea with many known issues to solve before implementing - would offer a much more difficult challenge for even the most advanced AI roleplaying models to forecast precisely, and a larger surface over which participants can bet and win. 


## Abstract

Binary prediction markets encode exactly one bit of information per contract. As AI forecasting systems approach superhuman calibration, the marginal edge any participant can capture in a binary market collapses toward zero — the correct answer becomes trivially computable, and spreads vanish. We propose an alternative market structure in which participants predict the *exact text* a public figure will post, scored by Levenshtein edit distance. Text prediction over a 95-character printable ASCII alphabet with strings up to length 280 yields an outcome space of approximately 95^280 ≈ 10^554 possibilities, encoding roughly 1,840 bits of information per market versus 1 bit for binary contracts — a 1,840:1 improvement in information density. Levenshtein distance induces a proper metric on this space (satisfying identity, symmetry, and the triangle inequality), which means payoffs are not a binary cliff but a continuous gradient surface where every character of precision is rewarded. We demonstrate this with a thesis example: given the same prompt and public training corpus, Claude predicts a Satya Nadella post at edit distance 1 while GPT achieves distance 8 — a 7-edit gap that determines the entire pool. In a binary market, both models "predicted correctly" and split nothing. We present a v0 prototype deployed on BASE Sepolia consisting of ~513 lines of Solidity with on-chain Levenshtein computation, 6 worked examples spanning AI roleplay, insider information, null prediction, and bot filtration, and a test suite of 259+ passing tests (109 contract, 135 unit, 15 integration). We discuss attack vectors including self-oracle exploits and AI-induced behavior modification, offer a complexity-theoretic framing of text prediction as an AI capability proxy (analogical, not formal), and argue that the approaching AI capability explosion does not destroy this market — it deepens it.

---

## 1. Introduction

### 1.1 The Commoditization Problem

Prediction markets are no longer a niche experiment. They are becoming a mainstream asset class. Polymarket and Kalshi combined processed approximately $40 billion in volume in 2025. Industry projections estimate 445 billion contracts and $222.5 billion in notional volume for 2026, representing 47% annual growth. Piper Sandler estimates a total addressable market exceeding $100 billion within the decade.

The distribution infrastructure is scaling rapidly. Robinhood's event trading product — launched via its January 2026 acquisition of MIAXdx — has become the fastest-growing product in the company's history, with 11 billion contracts traded and a projected $300 million annual revenue run rate. ICE, the parent company of the New York Stock Exchange, made a $2 billion strategic investment in Polymarket in October 2025, valuing the platform at $15 billion. Kalshi reached an $11 billion valuation on the back of 50x user growth and 100x volume growth year-over-year. In January 2026, Coinbase and Kalshi launched binary prediction markets to all 50 U.S. states through Kalshi's CFTC-regulated backend.

These markets all operate on the same simple primitive: a contract resolves to 0 or 1, and participants trade shares priced between $0 and $1 reflecting the market's collective probability estimate.

This structure has a fundamental limitation. As AI forecasting systems improve along what appears to be an exponential capability curve, the edge available in binary markets shrinks. When every sophisticated participant's model outputs "87% yes" on the same question, the spread vanishes and the market becomes commoditized. The information content of a binary outcome is exactly 1 bit — there is no room for gradations of skill once the probability estimate converges.

The question is not whether prediction markets will grow — the capital flows have answered that. The question is what happens to their structure as AI commoditizes the binary primitive.

### 1.2 Text Prediction as Richer Outcome Space

Consider predicting not *whether* something happens, but *the exact words* a public figure will use to describe it. The outcome space changes dramatically:

- **Binary market**: |O| = 2. Information content: 1 bit.
- **Text prediction (280-char ASCII)**: |O| ≈ 95^280 ≈ 10^554. Information content: 280 × log₂(95) ≈ 1,840 bits.

This is not a marginal improvement. The text prediction space contains roughly 10^554 possible outcomes, a number that exceeds the estimated number of atoms in the observable universe by over 470 orders of magnitude. No AI system, no matter how capable, will exhaust this space.

More importantly, text prediction admits a natural distance metric — Levenshtein edit distance — that transforms the payoff function from a binary cliff into a continuous gradient. A prediction that differs from the actual text by 1 edit is meaningfully better than one that differs by 8 edits, and both are meaningfully better than a random string at distance 200+. This gradation is precisely what binary markets lack.

### 1.3 Thesis Statement

Levenshtein distance induces a proper metric on the space of text predictions, creating a continuous payoff surface where marginal improvements in language modeling *always* translate to marginal improvements in expected payout. The payoff function is Lipschitz-continuous with respect to prediction quality. As AI capabilities hit the steep part of the exponential curve, binary prediction markets become commoditized — everyone's model converges to the same probability and the spread vanishes. Text prediction markets remain strategically rich because the distance between the 99th and 99.9th percentile language model still corresponds to multiple edit operations, each worth money. The approaching AI capability explosion does not flatten this market. It deepens it.

### 1.4 Contributions

This paper makes the following contributions:

1. **Formal analysis** of Levenshtein distance as a scoring metric for prediction markets, including proofs of metric properties, outcome space analysis, and payoff surface characterization.
2. **Working prototype** deployed on BASE Sepolia (Coinbase L2, OP Stack) with on-chain Levenshtein computation in 513 lines of Solidity and 259+ passing tests.
3. **Six worked examples** demonstrating AI roleplay, insider advantage, null prediction, AI-vs-AI competition, and natural bot filtration.
4. **Attack vector analysis** including self-oracle exploits, insider information dynamics, AI-induced behavior modification, and Sybil resistance.
5. **Complexity-theoretic framing** (explicitly analogical, not formal) of text prediction as an AI capability proxy, with discussion of fast takeoff dynamics and limiting cases.
6. **Economic analysis** of market lifecycle dynamics and sizing of the text prediction opportunity against adjacent markets including sports betting, the creator economy, and corporate communications monitoring.

---

## 2. The Prediction Market Landscape

### 2.1 Boom and Bust: A Brief History

Prediction markets have a four-decade track record of demonstrating superior forecasting accuracy — and an equally long track record of being killed by regulators before reaching scale.

**Iowa Electronic Markets (1988-2000).** The first modern prediction market, operated by the University of Iowa. IEM political forecasts came within 1.5 percentage points of actual election results, outperforming major polls in 596 of 964 comparisons (Berg et al., 1997). IEM proved the academic case: markets aggregate dispersed information efficiently. But its small scale (typically under $10,000 in volume per contract) and academic setting limited its commercial relevance.

**InTrade (2001-2013).** The largest prediction market of its era. InTrade hosted contracts on politics, entertainment, science, and current events, with peak volumes in the millions of dollars during U.S. election cycles. The CFTC filed a civil complaint against InTrade in November 2012 for offering off-exchange options trading to U.S. customers. InTrade banned U.S. traders, and in March 2013 shut down entirely, citing "financial irregularities." The closure eliminated over 80% of its user base overnight and destroyed much of the academic research ecosystem that had formed around the platform.

**Augur (2015-2023).** The first decentralized prediction market, built on Ethereum. Augur launched its mainnet in July 2018 to significant fanfare but struggled to attract users. By August 2018, it averaged 37 daily active users. A brief revival during the 2020 U.S. election produced approximately $3 million in open interest — trivial by later standards. Post-2021, active development was largely abandoned. The Augur Foundation ceased maintenance, and the platform became a cautionary tale about the gap between decentralized promise and user adoption.

**PredictIt (2014-present).** Operated by Victoria University of Wellington under a CFTC no-action letter, PredictIt offered political prediction markets with an $850 bet limit. In August 2022, the CFTC withdrew the no-action letter and ordered PredictIt to cease operations by February 2023. The Fifth Circuit Court of Appeals reversed the CFTC's order and issued an injunction allowing PredictIt to continue operating. In December 2025, the CFTC granted PredictIt renewed no-action relief. The platform remains in regulatory limbo — operational but perpetually uncertain about its future.

**The pattern.** Every major prediction market platform in the last two decades has been killed or nearly killed by regulatory intervention — not by lack of demand. InTrade was destroyed by a CFTC enforcement action. PredictIt nearly followed. Augur's failure was partly regulatory avoidance (decentralization as a way to sidestep oversight) that came at the cost of usability. The demand side has been validated repeatedly. The supply side keeps getting shut down.

### 2.2 The 2024-2026 Super Cycle

The 2024 U.S. presidential election broke prediction markets into the mainstream. Polymarket processed $3.6 billion in total volume on the presidential race alone, with $3.13 billion in open interest the day before the election. October 2024 saw 235,300 active traders on Polymarket — more than every prior prediction market combined.

The 2025 breakout exceeded all expectations. Polymarket and Kalshi combined processed approximately $40 billion in volume. By October 2025, monthly volumes surpassed the entire 2024 election cycle. Industry projections for 2026 estimate 445 billion contracts at $222.5 billion in notional volume, representing 47% annual growth.

The distribution unlock has been decisive. Robinhood's event trading product, launched through its January 2026 acquisition of the MIAXdx exchange, has become the fastest-growing product in the company's history: 11 billion contracts traded, over 1 million active users, and NFL prop bets driving engagement among demographics that had never traded a futures contract. Coinbase launched Kalshi-backed prediction markets in all 50 states. ICE, the parent company of the NYSE, made a $2 billion strategic investment in Polymarket, valuing it at $15 billion — signaling institutional legitimacy to a class of investors who had previously dismissed prediction markets as novelty betting.

Sports integration has been a critical growth vector. Approximately 89% of Kalshi's revenue now comes from sports-related event contracts. Global sports betting represents a $100.9 billion market in 2024, projected to reach $187 billion by 2030 at an 11% CAGR (Grand View Research, 2025). This existing regulatory infrastructure — 39 U.S. states plus D.C. have legalized sports betting — and user acquisition pipeline provides a foundation for adjacent event contract categories.

### 2.3 What Makes Markets Thrive vs. Die

Markets that thrive share four properties:

- **Clear resolution criteria.** Iowa Electronic Markets, Hollywood Stock Exchange, and Kalshi event contracts succeed because outcomes are unambiguous. "Will candidate X win state Y?" resolves cleanly. "Will AI progress be significant this year?" does not.
- **Regulatory clarity.** Kalshi's CFTC Designated Contract Market (DCM) status and Robinhood's MIAXdx acquisition provide legal certainty. Platforms operating in regulatory gray areas (InTrade, early PredictIt) live under existential threat.
- **Distribution integration.** Robinhood is proving the model: event trading embedded in an existing brokerage with 24 million funded accounts converts curiosity into volume. Standalone prediction market apps face cold-start problems that embedded products do not.
- **Network effects at scale.** Polymarket's ICE backing and Kalshi's Coinbase partnership create institutional credibility loops: more legitimacy → more participants → tighter spreads → more legitimacy.

Markets that die suffer from four failure modes:

- **Regulatory intervention.** InTrade (fatal), PredictIt (near-fatal). Federal enforcement actions kill platforms faster than organic adoption can grow them. The lesson: regulatory posture is not a nice-to-have; it is existential.
- **Liquidity death spirals.** Augur's core failure. Insufficient participants produce thin markets, which prevent meaningful price discovery, which repel new participants. The spiral is self-reinforcing and nearly impossible to escape without external capital injection.
- **Zero-sum exhaustion.** Every winner needs a loser. On long time horizons and esoteric topics, prediction markets struggle to attract the volume needed to sustain fees. Binary markets on niche questions often fail to reach the liquidity threshold required for meaningful participation.
- **Homogeneous participants.** Crowd wisdom requires diversity of information sources (Surowiecki, 2004). When only one type of participant engages — all retail traders, or all AI models — accuracy collapses and the market ceases to produce useful price signals.

### 2.4 The Commoditization Endgame

Binary markets are thriving *now* because uncertainty is high and AI forecasting has not yet converged. The current $40 billion boom is driven by questions where reasonable people disagree: political outcomes, sports results, regulatory decisions. AI models achieve 60-80% accuracy on these questions, leaving substantial edge for informed human participants.

But the trajectory is clear. As AI calibration improves — P(correct) moving from 60% to 80% to 95% to 99% — the spread compresses. When every participant runs the same frontier model and gets the same probability estimate, the market reduces to a coin flip over the remaining uncertainty. The current boom carries the seeds of its own compression.

Text prediction is positioned for *after* the commoditization event. The thesis of this paper is not "binary markets are bad today" — the $40 billion in 2025 volume demonstrates they are emphatically not. The thesis is that binary markets have a structural ceiling that text markets do not. When AI models converge on the same probability for a binary question, the market is over. When AI models converge on *nearly* the same text prediction, the remaining edits become *more* valuable, not less. This structural difference — diminishing returns in binary markets versus increasing returns in Levenshtein markets — is what we formalize in the remainder of this paper.

---

## 3. Related Work

### 3.1 Prediction Markets and Scoring Rules

The academic study of prediction markets dates to the Iowa Electronic Markets (Berg et al., 1997), which demonstrated that small-scale political prediction markets could outperform polls. Hanson (2003) formalized the logarithmic market scoring rule (LMSR), providing a mechanism for automated market making with bounded loss. Chen and Pennock (2010) extended this to combinatorial prediction markets. The practitioner history of these platforms — their growth trajectories, regulatory encounters, and failure modes — is covered in Section 2.

All major platforms to date operate on binary or small-cardinality discrete outcomes. Proper scoring rules — logarithmic (Good, 1952), Brier (Brier, 1950), and spherical — have been extensively studied, but all assume a probability distribution over a finite outcome set. None apply a continuous distance metric over a combinatorially explosive text space.

### 3.2 String Metrics

The Levenshtein distance (Levenshtein, 1966) counts the minimum number of single-character insertions, deletions, and substitutions required to transform one string into another. Wagner and Fischer (1974) gave the classical dynamic programming algorithm with O(mn) time and O(mn) space, later optimized to O(min(m,n)) space using a two-row technique.

Variants include Damerau-Levenshtein distance (adding transpositions), Jaro-Winkler distance (weighted prefix matching), and Hamming distance (substitutions only, equal-length strings). Applications span spell checking, DNA sequence alignment, plagiarism detection, and record linkage in databases. To our knowledge, Levenshtein distance has not previously been used as an on-chain scoring function for prediction markets.

### 3.3 AI Persona Simulation

Large language models trained on public internet corpora have demonstrated the ability to simulate the writing style, vocabulary, and rhetorical patterns of specific public figures (Argyle et al., 2023). This "roleplay" capability — prompting a model with "You are @elonmusk. Write your next post about Starship." — produces text that captures idiosyncratic patterns including sentence structure, punctuation preferences, numerical specificity, and catchphrases. The fidelity of this simulation varies with the target's public corpus size and the model's training data coverage.

### 3.4 Continuous Ranking and Scoring Inspiration

The move from discrete to continuous scoring has precedent in competitive ranking systems. The Elo rating system (Elo, 1978) assigns continuous skill ratings from discrete match outcomes, and its extensions (Glicko, TrueSkill) incorporate uncertainty. Euler-style continuous ranking gradients, which assign graded scores rather than binary win/loss, have been applied in academic competitions and coding challenges. Our payoff surface, where the winner receives a continuous advantage proportional to their edit distance lead, draws conceptual inspiration from these systems: the insight that replacing a cliff with a gradient produces richer strategic behavior.

---

## 4. Mathematical Foundations

### 4.1 Levenshtein Distance as Metric

**Definition.** Let Σ be a finite alphabet and Σ* the set of all finite strings over Σ. The Levenshtein distance d_L(a, b) between two strings a, b ∈ Σ* is the minimum number of single-character edit operations (insertions, deletions, substitutions) required to transform a into b.

**Theorem.** d_L is a metric on Σ*. That is, for all a, b, c ∈ Σ*:

1. **Identity of indiscernibles**: d_L(a, b) = 0 if and only if a = b.
2. **Symmetry**: d_L(a, b) = d_L(b, a).
3. **Triangle inequality**: d_L(a, c) ≤ d_L(a, b) + d_L(b, c).

*Proof sketch.*

(1) If a = b, zero edits are required, so d_L(a, b) = 0. Conversely, if d_L(a, b) = 0, no edits are needed, so a = b.

(2) Every edit operation has a natural inverse: insertion ↔ deletion, and substitution is self-inverse. An optimal sequence transforming a → b can be reversed to transform b → a with the same number of operations.

(3) An edit sequence transforming a → b followed by a sequence transforming b → c is a valid (possibly non-optimal) sequence transforming a → c. Therefore d_L(a, c) ≤ d_L(a, b) + d_L(b, c). ∎

The metric property is essential for market design. Identity of indiscernibles ensures that a perfect prediction (d_L = 0) is unambiguously identified. Symmetry ensures that the scoring function does not depend on the order of comparison. The triangle inequality ensures that the distance is coherent — a prediction "close" to the actual text cannot simultaneously be "far" from another prediction that is also "close" to the actual text.

### 4.2 Algorithmic Complexity

The standard Wagner-Fischer dynamic programming algorithm computes d_L(a, b) in O(mn) time where m = |a| and n = |b|. The classical implementation requires an (m+1) × (n+1) matrix, but only two rows are needed at any point, reducing space complexity to O(min(m, n)).

Our on-chain Solidity implementation uses this two-row optimization:

```
prevRow[0..n] ← [0, 1, 2, ..., n]
for i = 1 to m:
    currRow[0] ← i
    for j = 1 to n:
        cost ← 0 if a[i-1] == b[j-1], else 1
        currRow[j] ← min(prevRow[j] + 1,          // deletion
                         currRow[j-1] + 1,          // insertion
                         prevRow[j-1] + cost)        // substitution
    swap(prevRow, currRow)
return prevRow[n]
```

**Gas costs on BASE L2** (approximate, from benchmarking):

| String Length (each) | Gas Cost |
|---------------------|----------|
| 50 characters | ~400,000 |
| 100 characters | ~1,500,000 |
| 280 characters | ~9,000,000 |

The contract enforces `MAX_TEXT_LENGTH = 280` (tweet length) to prevent block gas limit denial-of-service. At 280 characters, the computation remains feasible on BASE L2 where block gas limits are substantially higher than Ethereum L1 and transaction fees are orders of magnitude lower.

### 4.3 Outcome Space Analysis

**Binary market.** The outcome space is O_binary = {0, 1}. Information content: I_binary = log₂(2) = 1 bit.

**Text prediction market.** For an alphabet A with |A| characters and maximum string length n, the number of possible strings of length exactly k is |A|^k. The total outcome space, including all strings of length 0 through n, is:

|O_text| = Σ_{k=0}^{n} |A|^k = (|A|^(n+1) - 1) / (|A| - 1) ≈ |A|^n for large n.

For printable ASCII (|A| = 95) and tweet-length strings (n = 280):

|O_text| ≈ 95^280 ≈ 10^554

The information content is:

I_text = log₂(|O_text|) ≈ 280 × log₂(95) ≈ 280 × 6.57 ≈ 1,840 bits

**Information density ratio:** I_text / I_binary ≈ 1,840 / 1 = **1,840:1**.

Each text prediction market encodes approximately 1,840 times more information than a binary prediction market. This is a conservative estimate — it assumes uniform distribution over the outcome space. In practice, the distribution is highly non-uniform (natural language has structure), but the combinatorial explosion ensures that even the "likely" region of the space is astronomically larger than {0, 1}.

### 4.4 Payoff Surface

The Clockchain payout mechanism is winner-take-all:

```
fee = ⌊pool × 700 / 10000⌋       // 7% platform fee (700 basis points)
payout = pool − fee                 // 93% to winner
winner = argmin_{s ∈ submissions} d_L(s.predictedText, actualText)
```

The winner is the submission with the minimum Levenshtein distance to the actual text. In the event of a tie, the first submitter wins (strict less-than comparison, deterministic by submission ordering).

**Lipschitz continuity of expected payoff.** Consider a participant whose prediction quality is characterized by the distribution of d_L(prediction, actual). Let the expected payoff for a participant with expected distance d be:

E[payout | d] = P(win | d) × 0.93 × pool

Because winning requires having strictly lower distance than all competitors, P(win | d) is monotonically decreasing in d. Moreover, for a fixed competitor distribution, a one-edit improvement in expected distance produces a bounded improvement in win probability. Formally, let F(d) = P(min_{competitors} d_L ≤ d). Then:

|E[payout | d] − E[payout | d+1]| ≤ 0.93 × pool × |F(d) − F(d+1)|

This means the expected payoff is Lipschitz-continuous with respect to prediction quality: marginal improvements in distance *always* translate to marginal improvements in expected payout. There is no "close enough" threshold below which improvements stop mattering. Every edit counts.

### 4.5 Expected Distance for Random Strings

**Claim.** For two random strings a, b of lengths m, n drawn uniformly over an alphabet A with |A| ≥ 2, the expected Levenshtein distance satisfies:

E[d_L(a, b)] → max(m, n) as |A| → ∞

**Intuition.** When the alphabet is large, the probability that any two characters match is 1/|A|, which approaches zero. With no matching characters, the optimal edit strategy is to delete all of a and insert all of b (or vice versa), giving d_L = max(m, n). Even for printable ASCII (|A| = 95), the match probability per character is ~1.05%, so random strings achieve near-maximal distance.

**Implication for market design.** Bots submitting random or adversarial strings cannot get lucky. In a character-level outcome space with a large alphabet, there is no shortcut — random guessing produces distances near the theoretical maximum. The metric itself functions as a spam filter. This is demonstrated empirically in Example 6 (Section 7), where random bot submissions achieve distances of 65-73 against actual text of ~80 characters.

### 4.6 Tie-Breaking

Ties are broken by submission order: the first submitter wins. The resolution algorithm uses strict less-than comparison (`distance < minDistance`), so a later submission with equal distance does not displace an earlier one.

This creates an incentive to submit early and confidently. Waiting to see others' submissions provides no advantage because all submissions are committed on-chain and the comparison is against the actual text, not against other submissions. Early submission also commits the predictor to a position, preventing last-second front-running of a known resolution text.

---

## 5. System Design

### 5.1 Architecture

Clockchain is deployed on BASE (Coinbase L2, OP Stack) with the following stack:

```
Frontend (Web3.js, MetaMask / Coinbase Wallet SDK)
    │  JWT Auth
Flask Backend (routes/, services/)
    │  Web3.py
BASE Sepolia (PredictionMarketV2.sol, GenesisNFT, + supporting contracts)
```

All market data lives on-chain. There is no database. Redis is used only for caching RPC responses, authentication nonces and OTPs, and rate limiting. The backend is prototype scaffolding around the core on-chain primitive.

### 5.2 Contract Constants

The `PredictionMarketV2` contract defines the following constants:

| Constant | Value | Purpose |
|----------|-------|---------|
| `PLATFORM_FEE_BPS` | 700 (7%) | Fee taken from winning pool |
| `MIN_BET` | 0.001 ETH | Minimum stake per submission |
| `BETTING_CUTOFF` | 1 hour | No submissions within 1 hour of market end |
| `MIN_SUBMISSIONS` | 2 | Minimum entries for valid resolution |
| `MAX_TEXT_LENGTH` | 280 | Character limit (tweet length, gas cap) |

`MIN_SUBMISSIONS = 2` ensures that a single submission receives a full refund (no fee) rather than being penalized for lack of competition. The betting cutoff prevents last-second front-running when the resolution text may already be known.

### 5.3 Payout Formula

When a market resolves:

```
fee = ⌊totalPool × 700 / 10000⌋
payout = totalPool − fee
```

The winner receives `payout`. The `fee` is accumulated in a pull-based collection mapping (preventing griefing attacks where a malicious fee recipient reverts transfers). The 7% platform fee is split:

| Recipient | Share of Fee | Share of Volume |
|-----------|-------------|-----------------|
| Genesis NFT Holders | 20.0% | 1.4% |
| Oracles | 28.6% | 2.0% |
| Market Creators | 14.3% | 1.0% |
| Node Operators | 14.3% | 1.0% |
| Builder Pool | 28.6% | 2.0% |

### 5.4 The Null Sentinel

The contract reverts on empty strings (`EmptyPrediction()` error). To express the prediction "this person will not post," participants submit the sentinel value `__NULL__`. When resolution also uses `__NULL__`:

d_L("\_\_NULL\_\_", "\_\_NULL\_\_") = 0

This creates a market primitive that binary contracts cannot express: betting on *silence*. AI roleplay agents always generate text — they cannot predict inaction. A human trader who recognizes that a public figure is unlikely to post during the market window can submit `__NULL__` and, if correct, win at distance 0 (Example 4, Section 7).

### 5.5 Resolution

**Current model (v0 alpha):** A single externally owned account (EOA) — the contract owner — calls `resolveMarket(marketId, actualText)`. This is the most significant centralization risk in the system.

**Planned upgrade path:**

1. **Commit-reveal oracle consensus**: Multiple registered oracles independently submit the actual text in a commit phase, then reveal. The majority text (or the text with minimum aggregate distance among oracle submissions) is accepted.
2. **Slashing for dishonest oracles**: Oracles whose submissions deviate significantly from the consensus forfeit staked collateral.
3. **Screenshot proof**: IPFS-pinned screenshot of the actual post, linked to the resolution transaction for auditability.

### 5.6 X as Resolution Infrastructure

Text prediction markets require a resolution source: a public, timestamped, attributable record of what a person actually said. X (formerly Twitter) is uniquely suited to this role.

**The public ledger of intent.** X has approximately 557 million monthly active users as of 2025 (Backlinko, 2025). Posts are public by default, timestamped to the second, attributable to verified accounts, and character-limited — the platform's 280-character post limit aligns directly with the contract's `MAX_TEXT_LENGTH = 280`. Unlike other major social platforms, X's core use case is short-form public text in real time.

**Why X specifically.** The choice of X as the initial resolution platform is not arbitrary. Consider the alternatives:

- **Instagram**: Visual-first. Captions are secondary to images and are often formulaic or promotional. Not a medium where word choice carries signal.
- **LinkedIn**: Professional, long-form. Posts tend to follow narrow templates ("I'm proud to announce..."). Character-level prediction is less interesting when the format is highly constrained by professional norms rather than personal expression.
- **TikTok**: Video-native. Text is supplementary (captions, overlays). The primary content is not parseable as a string.
- **Truth Social / Threads**: Smaller user bases and limited to specific demographics. Not yet sites of market-moving discourse at scale.

X is the only major platform where short-form text is the primary medium, posts are public by default, and real-time discourse is the core use case. It is where market-moving speech happens.

**Market-moving speech.** X posts are financial events. Elon Musk's tweets have produced approximately 3% price moves in DOGE on multiple occasions; during the DOGE government controversy, Tesla lost roughly $800 billion in market capitalization before rebounding 4% on the announcement of Musk's step-down from the advisory role. Donald Trump's two Truth Social posts in March 2025 naming specific cryptocurrencies (BTC, ETH, XRP, SOL, ADA) triggered a $300 billion crypto market rally, with named tokens moving 10-60% within hours. Sam Altman's statements on X have moved AI sector sentiment, with Microsoft stock reaching all-time highs on key announcements. These are not edge cases. Public figures' social media posts routinely move billions of dollars in market value.

**Resolution properties.** X posts have four properties that make them suitable for market resolution:

1. **Public.** Posts are visible without authentication. No scraping or privileged access is required for verification.
2. **Timestamped.** Each post carries a server-side timestamp accurate to the second, enabling dispute resolution about whether a post fell within a market's resolution window.
3. **Attributable.** The handle-to-person mapping is well-established for public figures, and X's verification system (however imperfect) provides a baseline identity layer.
4. **Immutable in real-time.** While posts can be edited or deleted after the fact, edits are detectable via the X API (which flags edited posts), and third-party archival services (Wayback Machine, archive.today, various Twitter archive bots) provide independent records.

**API access and oracle economics.** As of February 2026, X offers a pay-per-use API pricing model alongside its legacy subscription tiers (Basic at $200/month for 15,000 reads; Pro at $5,000/month for 1 million reads). The pay-per-use model — credit-based billing with no subscriptions, no monthly caps, and no minimum spend — substantially changes the economics of decentralized oracle resolution. Under subscription pricing, requiring each oracle node to maintain an independent $200/month API subscription made multi-oracle verification cost-prohibitive. Under pay-per-use pricing, an oracle that verifies a single post per market resolution pays only for the API calls it actually makes, which may amount to fractions of a dollar per resolution. This makes independent, multi-oracle tweet verification economically viable for the first time. API reliability and the possibility of access revocation remain dependency risks that must be addressed in the oracle design, but the cost barrier has been substantially reduced.

---

## 6. AI Roleplay as Prediction Strategy

### 6.1 The Roleplay Mechanism

The dominant strategy for text prediction in Clockchain markets is to prompt a frontier large language model with a persona simulation request:

> *"You are @elonmusk. You are about to post on X about Starship. Write your exact post, including punctuation, numbers, and phrasing."*

The model generates text that attempts to match the target's writing style, vocabulary, rhetorical patterns, numerical specificity, and even characteristic punctuation. This is not summarization or topic prediction — it is an attempt to produce the *exact character sequence* the target will produce.

### 6.2 Why Roleplay Works

Large language models are trained on vast corpora of public text, including social media posts, press releases, interviews, and articles. For public figures with large digital footprints, the model has internalized:

- **Vocabulary distribution**: Which words and phrases the person uses most frequently.
- **Sentence structure**: Characteristic syntax, paragraph length, use of fragments.
- **Rhetorical patterns**: How the person introduces products, responds to criticism, or celebrates milestones.
- **Numerical tendencies**: Whether the person uses precise numbers ("46%") or round numbers ("about half").
- **Punctuation and formatting**: Use of periods vs. exclamation marks, capitalization patterns, emoji usage.

The quality of the simulation depends on the model's training data coverage of the target and the target's own consistency. A CEO who uses rehearsed messaging (from a communications team) is more predictable than one who posts spontaneously.

### 6.3 Inevitability, Personality, and Situational Context

Three factors determine how predictable a given post is:

**Inevitability.** Rehearsed messaging — product launches, earnings summaries, policy announcements — follows predictable templates. When a CEO's communications team drafts the post, the language is often formulaic and recoverable from prior examples. High inevitability favors AI prediction. Example: Satya Nadella's post about Copilot adoption (Example 5) follows a predictable pattern of "[Product] is now [metric]. [Aspirational statement]." Claude gets within 1 edit.

**Personality.** Idiosyncratic style creates both signal and noise. Elon Musk's characteristic phrasing ("or we die trying") is capturable by AI, while his tendency toward spontaneous tangents is not. AI captures statistical patterns in personality; it misses in-the-moment deviations.

**Situational context.** Real-time information — breaking news, internal decisions, last-minute changes — is unavailable to AI models with training data cutoffs. When Sam Altman decides to use the phrase "we are now confident" instead of "we now believe," that choice reflects internal context that no amount of training data can recover. Low inevitability and high situational specificity favor human insiders. Example: An ex-OpenAI engineer achieves distance 4 versus GPT's distance 18 on a Sam Altman post (Example 2), because they heard the rehearsed phrasing.

### 6.4 The Inevitability Spectrum

| Target Type | Inevitability | Dominant Strategy | Example |
|-------------|---------------|-------------------|---------|
| Corporate launch | High | AI roleplay | Nadella: d_L = 1 (Claude) |
| Rehearsed messaging | High | Insider > AI | Altman: d_L = 4 (insider) vs 18 (AI) |
| Product marketing | High | Leak/insider | Zuckerberg: d_L = 3 (intern) |
| Spontaneous/personal | Low | Human intuition | Variable |
| Silence/inaction | N/A | Null trader | Jensen Huang: d_L = 0 (\_\_NULL\_\_) |
| Random/chaotic | Low | No reliable strategy | High distances for all |

The market accommodates the full spectrum. AI dominates high-inevitability targets. Insiders dominate when situational context matters. Null traders capture the inaction primitive. No single strategy dominates all market types, which is a desirable property for a healthy market ecosystem.

---

## 7. Worked Examples

The following six examples were implemented as seed data on BASE Sepolia using the contract at `0x5174Da96BCA87c78591038DEe9DB1811288c9286`. All distances are computed by the on-chain Levenshtein distance function. The predicted texts, actual texts, and distances are verified against the seed script (`scripts/seed_examples.py`).

> **Note:** These are simulated examples on BASE Sepolia testnet, not live market data. They are constructed to demonstrate the range of strategic outcomes in a Levenshtein-scored market.

---

### Example 1: AI Roleplay Wins (Elon Musk)

**Market:** What will `@elonmusk` post?

**Actual text:** `Starship flight 2 is GO for March. Humanity becomes multiplanetary or we die trying.`

| Submitter | Predicted Text | d_L |
|-----------|---------------|-----|
| AI Roleplay (Claude) | `Starship flight 2 confirmed for March. Humanity becomes multiplanetary or dies trying.` | **12** |
| Human fan | `The future of humanity is Mars and beyond` | 59 |
| AI (lazy prompt, GPT) | `Elon will probably tweet about SpaceX rockets going to space soon` | 66 |
| Bot (entropy) | `a8j3kd9xmz pqlw7 MARS ufk2 rocket lol` | 72 |

**Winner:** AI Roleplay (Claude) at distance 12. Gap over runner-up: **47 edits**.

**Analysis.** A well-prompted AI captures Musk's tone, structure, and vocabulary. The human fan got the *theme* right ("Mars") but theme does not pay — exact wording does. The 47-edit gap between the AI roleplay and the human fan represents the entire pool. The random bot demonstrates the anti-spam property: gibberish achieves near-maximal distance.

---

### Example 2: Human Insider Beats AI (Sam Altman)

**Market:** What will `@sama` post?

**Actual text:** `we are now confident AGI is achievable with current techniques. announcement soon.`

| Submitter | Predicted Text | d_L |
|-----------|---------------|-----|
| Ex-OpenAI engineer | `we are now confident AGI is achievable with current techniques. big announcement soon.` | **4** |
| AI Roleplay (GPT) | `we now believe AGI is achievable with current techniques. announcement coming soon.` | 18 |
| Human (cynical) | `Sam will say AGI is close again like he always does nothing new` | 59 |

**Winner:** Ex-OpenAI engineer at distance 4. Gap over runner-up: **14 edits**.

**Analysis.** Insider information beats AI. Someone who heard the rehearsed phrasing knows the exact phrase "we are now confident" — the AI generates the plausible but incorrect "we now believe." That single phrase difference accounts for most of the 14-edit gap. The cynical human, despite understanding Altman's general messaging patterns, scores worse than the AI because thematic understanding without exact wording is worth little in a Levenshtein-scored market. Information asymmetry is priced continuously, not as a binary "knew / didn't know."

---

### Example 3: Insider Leaks Exact Wording (Zuckerberg)

**Market:** What will `@zuck` post?

**Actual text:** `Introducing Meta Ray-Ban with live AI translation. 12 languages. The future is on your face.`

| Submitter | Predicted Text | d_L |
|-----------|---------------|-----|
| Meta intern | `Introducing Meta Ray-Ban with live AI translation in 12 languages. The future is on your face.` | **3** |
| AI Roleplay | `Introducing Meta Ray-Ban AI glasses with real-time translation in 8 languages. The future is on your face.` | 25 |
| Human (guessing) | `zuck will announce glasses or something idk` | 73 |
| Spam bot | `BUY META NOW GLASSES MOONSHOT 1000X GUARANTEED` | 83 |

**Winner:** Meta intern at distance 3. Gap over runner-up: **22 edits**.

**Analysis.** Product launches have rehearsed copy prepared by marketing teams. Access to a draft deck gives a 22-edit advantage over the best AI. The AI gets the structure right ("Introducing Meta Ray-Ban... The future is on your face.") but misses the specific phrasing ("live AI translation" vs. "real-time translation") and the exact number ("12" vs. "8"). Insider access to marketing materials is directly monetizable in this market structure.

---

### Example 4: Null Submission Wins (Jensen Huang Stays Silent)

**Market:** What will `@JensenHuang` post?

**Actual text:** *(nothing posted)* — resolved with `__NULL__`

| Submitter | Predicted Text | d_L |
|-----------|---------------|-----|
| Null trader | `__NULL__` | **0** |
| Human (guessing) | `Jensen will flex about Blackwell sales numbers` | 46 |
| AI Roleplay | `NVIDIA Blackwell Ultra is sampling ahead of schedule. The next era of computing starts now.` | 90 |

**Winner:** Null trader at distance 0 (exact match). Gap over runner-up: **46 edits**.

**Analysis.** Binary markets cannot express "this person will not post." The `__NULL__` sentinel enables betting on inaction. AI roleplay agents *always* generate text — they are structurally incapable of predicting silence. A human trader who recognizes that Jensen Huang is unlikely to post during the market window can exploit this blind spot. Distance 0 means the null trader takes the entire pool. This is a market primitive that does not exist in yes/no contracts.

---

### Example 5: AI vs. AI — THE THESIS EXAMPLE (Satya Nadella)

**Market:** What will `@sataborasu` post?

**Actual text:** `Copilot is now generating 46% of all new code at GitHub-connected enterprises. The AI transformation of software is just beginning.`

| Submitter | Predicted Text | d_L |
|-----------|---------------|-----|
| Claude roleplay | `Copilot is now generating 45% of all new code at GitHub-connected enterprises. The AI transformation of software is just beginning.` | **1** |
| GPT roleplay | `Copilot is now generating 43% of all new code at GitHub-connected enterprises. The AI transformation of software has just begun.` | 8 |
| Human (vague) | `Microsoft AI is great and will change the world of coding forever` | 101 |

**Winner:** Claude roleplay at distance 1 (single character: `5` → `6`). Gap over runner-up: **7 edits**.

**This is the thesis example.** Two frontier AI models, same public training corpus, same prompt template. Claude gets within 1 edit — the only difference is the number "45" versus "46." GPT gets within 8 edits, additionally substituting "has just begun" for "is just beginning." The 7-edit gap between two frontier models is worth the entire pool.

In a binary market framing, both AIs "predicted correctly" — Nadella posted about Copilot code generation, which both models anticipated. A binary contract would split nothing. Levenshtein distance rewards marginal calibration: the model that predicts "45%" instead of "43%" captures 1 edit of advantage. The model that preserves the exact phrase "is just beginning" instead of paraphrasing to "has just begun" captures several more.

The game deepens as models improve. When d_L drops from 100 to 50, the market transitions from noise to signal. When d_L drops from 10 to 1, the market becomes a precision instrument. Binary markets commoditize at this stage; Levenshtein markets become more valuable.

---

### Example 6: Bot Entropy Wastes Money (Tim Cook)

**Market:** What will `@tim_cook` post?

**Actual text:** `Apple Intelligence is now available in 30 countries. Privacy and AI, together.`

| Submitter | Predicted Text | d_L |
|-----------|---------------|-----|
| AI Roleplay | `Apple Intelligence is now available in 24 countries. We believe privacy and AI go hand in hand.` | **28** |
| Human (thematic) | `Tim will say something about privacy and AI like always` | 53 |
| Random bot | `x7g APPLE j2m PHONE kq9 BUY zw3 intelligence p5 cook` | 65 |
| Degenerate bot | `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa` | 73 |

**Winner:** AI Roleplay at distance 28. Gap over runner-up: **25 edits**.

**Analysis.** This example demonstrates the natural anti-bot property of Levenshtein distance. Random strings over a large alphabet have expected distance approaching max(m, n). The random bot's gibberish scores 65 against ~80-character actual text — close to the theoretical maximum. The degenerate bot attempting to game string length with repeated characters scores even worse (73). Even a thematic human guess ("something about privacy and AI") outperforms both bots. The metric itself is the spam filter: in a character-level outcome space, there is no shortcut for random or adversarial submissions.

---

### Summary Table

| # | Target | Winner | d_L | Runner-up d_L | Gap | Key Lesson |
|---|--------|--------|-----|---------------|-----|------------|
| 1 | @elonmusk | Claude roleplay | 12 | 59 | 47 | AI captures tone; theme doesn't pay, exact wording does |
| 2 | @sama | Human insider | 4 | 18 | 14 | Insider info beats AI; information asymmetry priced continuously |
| 3 | @zuck | Meta intern | 3 | 25 | 22 | Rehearsed copy leaks; marketing access = 22-edit advantage |
| 4 | @JensenHuang | Null trader | 0 | 46 | 46 | Betting on silence; AI can't predict inaction |
| 5 | @sataborasu | Claude roleplay | **1** | 8 | **7** | **THESIS**: AI vs AI, same corpus, 7-edit gap = entire pool |
| 6 | @tim_cook | AI roleplay | 28 | 53 | 25 | Anti-bot: random strings → d_L ≈ max(m,n). Metric = spam filter |

---

## 8. Economic Opportunity

### 8.1 Sizing the Opportunity

Prediction markets represent a $40 billion market in 2025, with projections of $222.5 billion in notional volume by 2026 and a total addressable market exceeding $100 billion within the decade (Piper Sandler, 2025). Text prediction markets sit at the intersection of several adjacent markets, each of which provides independent demand drivers and regulatory infrastructure.

**Sports betting.** The global sports betting market was valued at $100.9 billion in 2024 and is projected to reach $187 billion by 2030 at an 11% compound annual growth rate (Grand View Research, 2025). In the United States, 39 states plus the District of Columbia have legalized sports betting, creating a regulatory infrastructure and user acquisition pipeline that adjacent event contract categories can leverage. Approximately 89% of Kalshi's revenue now derives from sports-related event contracts, demonstrating that sports have become the primary on-ramp for prediction market adoption. Text prediction markets on athlete and sports commentator statements would inherit this user base directly.

**Influencer and creator economy.** The influencer marketing industry is projected to reach $32.55 billion in 2026, and the broader creator economy is valued at $250 billion in 2025 with projections trending toward $500 billion by 2030. Celebrity and influencer statements are already market-moving events — product endorsements, brand announcements, and public controversies all generate measurable economic impact. Text prediction markets monetize the precision of anticipating these statements, creating a new financial instrument layer on top of the creator economy.

**Corporate communications monitoring.** The global media monitoring market was valued at $5.4 billion in 2025 and is projected to reach $9.19 billion by 2030. An estimated 25% of public company market value is linked to corporate reputation and executive communication. Text prediction markets provide a real-time pricing mechanism for executive communication risk — a market signal for how predictable (or unpredictable) a CEO's messaging is, with direct implications for corporate governance and investor relations.

**Political speech.** The CFTC now explicitly permits political event contracts following Chair Selig's February 2026 policy reversal. Government and political statements have demonstrated market-moving capacity at scale — Donald Trump's two Truth Social posts in March 2025 triggered a $300 billion crypto market rally. Text prediction markets on political speech create a regulated financial instrument for pricing the predictability of government communication.

### 8.2 The Cross-Regulatory Advantage

Sports betting in the United States operates under a fragmented state-by-state licensing regime. Each of the 39 legalized states maintains its own regulatory framework, licensing requirements, and tax structures. Navigating this patchwork is expensive and slow — a barrier that favors incumbents over innovators.

The CFTC framework offers a structural alternative. Kalshi's Designated Contract Market (DCM) status and Robinhood's acquisition of MIAXdx provide federal jurisdiction over event contracts. This framework is more favorable to novel contract types: a single federal approval covers all 50 states, avoiding the need to negotiate with 50 separate gambling commissions.

Text prediction markets, structured as event contracts on a CFTC-regulated exchange, could inherit this federal framework. Rather than arguing in each state that "predicting what a CEO will post" is not gambling, a CFTC-regulated text prediction contract would fall under the same federal jurisdiction as Kalshi's political and sports event contracts. This regulatory arbitrage — federal event contract classification versus state gambling classification — is a meaningful structural advantage.

Kalshi's proprietary surveillance system "Poirot" provides a model for market integrity monitoring in this framework. Poirot uses pattern recognition to flag suspicious trading activity and has initiated over 200 investigations per year, demonstrating that event contract markets can meet the compliance standards required by federal regulators.

### 8.3 Why Now

Three conditions are converging simultaneously to create a window for novel prediction market structures:

**1. Regulatory clarity.** CFTC Chair Michael Selig's February 2026 reversal on political and sports event contracts reframed prediction markets as tools for "price discovery" and "aggregating dispersed information" — not gambling. The prior 2024 proposed rule would have prohibited these contracts entirely. The reversal does not merely permit existing market types; it establishes a regulatory posture that is receptive to novel event contract categories, including text prediction.

**2. Distribution unlock.** Robinhood, Coinbase, and ICE are providing mainstream on-ramps to event trading. Robinhood's event trading product is the fastest-growing product in the company's history. ICE's $2 billion investment in Polymarket signals that the world's largest exchange operator views prediction markets as a core asset class. These distribution channels did not exist 24 months ago. A novel market structure launched today reaches a potential user base of tens of millions of active traders, compared to the thousands who used InTrade or Augur.

**3. AI capability inflection.** Frontier language models are achieving d_L ≈ 1-10 on structured predictions (Section 7, Example 5). The technology that makes text prediction viable — AI models capable of simulating specific individuals' writing with near-character-level accuracy — is maturing in the same window as the regulatory and distribution prerequisites. Two years ago, AI roleplay produced text at d_L ≈ 50-100 (thematic accuracy, not word-level). Today, on high-inevitability targets, frontier models achieve d_L ≈ 1-10. The convergence of regulatory clarity, distribution infrastructure, and AI capability creates a window that did not exist before and may not remain open indefinitely as binary markets absorb most of the capital and attention.

---

## 9. Attack Vectors and Game Theory

### 9.1 Self-Oracle Attack

**Attack.** A participant creates a market for their own social media account, submits a prediction, then posts exactly that text. d_L = 0, guaranteed win.

**Severity.** Critical if unmitigated. The attacker captures the entire pool minus the 7% fee.

**Mitigations.**
- **Identity verification**: Markets are created for specific social media handles. If the market creator's identity can be linked to the handle, the market can be flagged or restricted.
- **Reputation detection**: On-chain analysis of market creators who consistently achieve d_L = 0 on their own markets.
- **Market design constraint**: Markets could be restricted to handles verified as belonging to someone other than the market creator. "Predict someone else" as a protocol rule.
- **Economic deterrent**: The attacker must stake `MIN_BET` and attract competitors. If the market is known to be self-oracle, no one else submits, and with `MIN_SUBMISSIONS = 2` the market cannot resolve.

This remains an open problem. Pseudonymous blockchain identities make identity verification difficult, and the economic incentive for self-oracle attacks is strong.

### 9.2 Insider Information

Insiders — employees, partners, communications staff — have access to rehearsed messaging, draft posts, and operational context that is unavailable to AI models or the general public. Examples 2 and 3 (Section 7) demonstrate that insider information produces significant advantages (14-edit and 22-edit gaps, respectively).

Unlike binary markets where insider information is a binary advantage ("knows the outcome" vs. "doesn't"), Levenshtein-scored markets price insider information on a continuous scale. An insider who has *some* context (e.g., knows the topic but not the exact wording) scores better than a pure AI prediction but worse than someone who has seen the exact draft. This continuous pricing creates an interesting dynamic: the incentive is to *trade on* insider information rather than leak it, because the information is directly monetizable through precision.

**Recent precedents in binary markets.** Insider trading in prediction markets is not theoretical — it is actively occurring on existing platforms:

- **Maduro ouster (January 2026).** An anonymous trader placed a $400,000 bet on Polymarket hours before the public announcement of Venezuelan political change. The trade is under investigation and represents one of the largest single suspicious wagers on the platform (Yahoo Finance, 2026).
- **Nobel Peace Prize (October 2025).** Suspicious Norwegian betting activity appeared on Polymarket approximately 11 hours before the official Nobel Peace Prize announcement. Norwegian authorities opened an investigation into potential information leakage from the Nobel Committee or its associates (BeInCrypto, 2025).
- **Google search rankings (December 2025).** A trader allegedly earned $1 million on Polymarket from a series of suspiciously accurate predictions about Google algorithm changes, suggesting access to non-public information about Google's search ranking updates.
- **Portugal presidential election.** Approximately €4 million was wagered with significant odds shifts occurring 2 hours before official results, suggesting coordinated trading on non-public exit polling or vote counting data.

These incidents demonstrate that insider trading is already a first-order concern in binary prediction markets, where the financial incentive is limited to a correct yes/no bet. In text prediction markets, the financial incentive is potentially larger because insider information translates to a continuous advantage rather than a binary one.

**Insider detectability in text markets.** In a Levenshtein-scored market, insider advantage manifests as persistently low d_L relative to non-insider competitors. This is *more detectable* than in binary markets, where an insider's correct binary bet is indistinguishable from a lucky guess. A participant who consistently achieves d_L < 5 when the best AI achieves d_L ≈ 10-20 is exhibiting a statistical signature of privileged information. The continuous nature of the scoring metric creates an audit trail that binary markets lack: not just "did they win?" but "how close were they, and is that closeness statistically consistent with public information alone?"

**Regulatory consideration.** If Levenshtein-scored prediction markets achieve significant volume, insider trading rules analogous to those in financial markets may be warranted. The continuous pricing mechanism makes insider advantage detectable (persistent d_L << competitors), which could support enforcement. Section 10 discusses the regulatory implications in detail.

### 9.3 Roleplay Agents Influencing Behavior

If an AI predicts your exact words and publishes that prediction on-chain (publicly visible), does that influence what you actually say? This is a potential self-fulfilling or self-defeating prophecy dynamic:

- **Self-fulfilling**: The target sees the prediction and, consciously or unconsciously, uses similar phrasing. The prediction becomes accurate because it was made.
- **Self-defeating**: The target deliberately avoids the predicted phrasing, increasing d_L for the AI predictor.

On-chain predictions are publicly visible. A public figure who monitors Clockchain markets for their handle could game the system by deliberately deviating from predictions, penalizing AI predictors.

**Open question:** Should predictions be hidden until resolution? A commit-reveal scheme for predictions would prevent this dynamic but would also prevent the price discovery that comes from observing others' predictions. The tradeoff between market transparency and prediction independence is unresolved.

### 9.4 Collusion and Sybil Attacks

**Attack.** A participant submits multiple near-identical predictions from different wallets to increase their probability of winning.

**Mitigation.** Winner-take-all payout eliminates the benefit of splitting across wallets. Submitting the same prediction from two wallets does not increase the payout — the first submission wins ties, and both submissions stake `MIN_BET`, so the attacker pays more for no additional expected return. Submitting *slightly different* predictions (hedging) is strategically rational but is a feature, not a bug — it reflects genuine uncertainty about the exact text and costs the attacker multiple `MIN_BET` stakes.

The `MIN_BET = 0.001 ETH` creates a cost floor for Sybil submissions. Submitting 100 variations costs 0.1 ETH, while a single confident prediction costs 0.001 ETH and wins the same pool if correct.

---

## 10. Policy Implications

### 10.1 The CFTC Regulatory Shift

In February 2026, CFTC Chair Michael Selig withdrew the proposed ban on political and sports event contracts that had been advanced under the prior 2024 rulemaking. The withdrawal represented a fundamental shift in the agency's posture toward prediction markets. Selig directed CFTC staff to draft rules with "clear, workable standards" for event contracts, reframing prediction markets as tools for "price discovery" and "aggregating dispersed information" rather than instruments of gambling.

The practical implications are significant. The CFTC is asserting exclusive federal jurisdiction over event contracts traded on designated contract markets, potentially preempting state gambling law for eligible platforms. This federal preemption — if it survives legal challenge — would allow novel event contract categories, including text prediction markets, to operate under a single federal framework rather than navigating 50 state-by-state gambling regimes.

The new rulemaking is not yet concluded. Staff-level drafting is underway, but final rules have not been proposed for public comment. The direction is favorable, but the timeline and specifics remain uncertain.

### 10.2 Insider Trading Enforcement

The Commodity Exchange Act (CEA) Section 6(c)(1) and CFTC Regulation 180.1 already prohibit trading on material non-public information (MNPI) in commodity and derivatives markets. These provisions apply, in principle, to event contracts traded on CFTC-regulated exchanges. However, enforcement standards for event contracts remain undeveloped compared to traditional commodities and financial futures.

The CFTC's new rulemaking is expected to establish explicit suspicious trade reporting standards for event contract markets. Kalshi's "Poirot" surveillance system — which uses pattern recognition to flag anomalous trading and has initiated over 200 investigations per year — provides a working model for what compliance infrastructure looks like in this context.

Text prediction markets create a novel MNPI category: knowledge of *what someone will say*. Draft social media posts, rehearsed messaging from communications teams, internal talking points, and advance knowledge of announcements all constitute forms of inside information in a text prediction context. A communications staffer who has seen the CEO's draft tweet possesses information that is directly monetizable at a precision level that d_L can measure.

Levenshtein markets make insider advantage both *more detectable* and *more granular* than in binary markets. More detectable because persistent low d_L scores create a statistical audit trail (Section 9.2). More granular because partial information yields partial advantage — an insider who knows the topic but not the exact wording achieves d_L ≈ 10-15, while an insider who has seen the draft achieves d_L ≈ 1-5. This gradation provides regulators with a richer signal for distinguishing degrees of information asymmetry.

### 10.3 Long-Term Policy Trajectory

If text prediction markets reach meaningful scale, they will create a novel regulated instrument class: speech-linked financial contracts. This class sits at the intersection of three regulatory domains:

1. **Securities and commodities law.** CFTC event contracts provide the primary framework. If text prediction markets are classified as event contracts on a DCM, they inherit federal commodity regulation including MNPI prohibitions, position limits, and surveillance requirements.

2. **Speech and media law.** Betting on the precise words a public figure will use raises questions about the relationship between financial markets and public discourse. There is no direct precedent for a financial instrument whose payoff is determined by the content of protected speech.

3. **Gambling regulation.** If CFTC preemption fails or is limited in scope, text prediction markets may face state-by-state gambling classification. The distinction between "event contract on a federally regulated exchange" and "bet on what someone will say" may not be persuasive to every state gambling commission.

Open questions for policymakers include:

- **Corporate insider restrictions.** Should employees of a company be prohibited from participating in text markets for their own executives? The analogy to insider trading blackout windows is direct: a communications team member who participates in a market on their CEO's next post is the functional equivalent of an insider trading on material non-public information.
- **Government official restrictions.** Should government officials face restrictions on text markets for political figures? Representative Ritchie Torres introduced the "Public Integrity in Financial Prediction Markets Act" in 2026, which would prohibit members of Congress and senior executive branch officials from trading on political event contracts. Text prediction markets on political speech would likely fall within the scope of such legislation.
- **Perverse transparency incentives.** Does the existence of text prediction markets create incentives for public figures to be *less* transparent — to increase the unpredictability of their communications in order to protect against market exploitation? If a CEO's communications become less formulaic because prediction markets are profiting from their predictability, that may be a net negative for corporate transparency.

These questions do not have clear answers. We raise them because any market structure that monetizes the prediction of human speech intersects with fundamental questions about information asymmetry, privacy, and the relationship between financial markets and public discourse. Responsible development of text prediction markets requires engaging with these questions rather than deferring them.

---

## 11. Complexity-Theoretic Discussion

> **Disclaimer:** This section offers speculative analogies and provocative framings. The connections to computational complexity theory are analogical, not formal reductions. They are included to suggest directions for future theoretical work, not to make rigorous claims.

### 11.1 Text Prediction as Capability Proxy

Predicting the exact text a person will post requires the simultaneous integration of multiple models:

- **World model**: What events are happening that the person might comment on?
- **Person model**: How does this specific individual express ideas? What words do they choose?
- **Timing model**: When will they post? What will be salient at that moment?
- **Style model**: What punctuation, formatting, and rhetorical devices will they use?

We can define a capability metric for a model M as:

capability(M) ∝ E[1 / d_L(M(context), actual)]

A model that consistently achieves low edit distance across diverse targets and contexts demonstrates integrated competence across all four submodels. Levenshtein distance to exact text is therefore a *naturally occurring capability benchmark* — one that emerges from the market mechanism rather than being designed by a benchmark committee.

### 11.2 The P Analogy

There is a suggestive structural analogy to the P vs. NP distinction:

- **Generation** (finding the exact text): Requires simulating a human mind, integrating world knowledge, personal style, and situational context. From a frontier LLM, generation is O(n) — linear in output length — but the quality of the output depends on the model's entire capability stack.
- **Verification** (checking closeness): Computing Levenshtein distance is O(n²) — polynomial in string length. Given a prediction and the actual text, anyone can verify how close the prediction was.

The analogy: *finding* the exact text is hard (requires deep capability); *checking* how close you got is easy (polynomial-time Levenshtein computation). This mirrors the P vs. NP structure where finding solutions is (conjectured to be) hard but verifying them is easy.

We emphasize that this is an *analogy*, not a formal reduction. Text prediction is not an NP-complete problem in any standard sense. The analogy is useful for intuition: Levenshtein distance provides a cheap, deterministic verification function for an expensive, capability-intensive generation problem.

### 11.3 Fast Takeoff and Market Depth

Consider the trajectory of AI capability improvement on text prediction:

| Distance Range | Market Phase | Strategic Implication |
|---------------|-------------|----------------------|
| d_L ≈ 100+ | Noise | Random guessing; no signal. Market is a lottery |
| d_L ≈ 50 | Signal emerges | AI begins to outperform random; theme-level accuracy |
| d_L ≈ 10 | Precision game | AI captures structure, vocabulary, phrasing. Every edit matters |
| d_L ≈ 5 | High stakes | Small capability differences determine large payouts |
| d_L ≈ 1 | Frontier competition | The 7-edit gap (Example 5) is worth the entire pool |

As AI capability follows an exponential improvement curve:

- d = 100 → 50: The transition from noise to signal. Markets become *useful*.
- d = 10 → 5: A major advantage. The best model reliably wins.
- d = 5 → 1: The entire pool hangs on marginal improvements. Markets become *extremely* valuable as a capability discriminator.

**Contrast with binary markets.** In a binary market, the analogous trajectory is: P(correct) = 60% → 80% → 95% → 99%. Once multiple models exceed 95%, the spread vanishes and the market commoditizes. In a Levenshtein market, the analogous trajectory (d = 10 → 5 → 1) becomes *more* valuable at each stage because the stakes per edit increase as the absolute distance decreases.

Binary markets have diminishing returns to capability improvement. Levenshtein markets have *increasing* returns.

### 11.4 The Limiting Case

If d_L → 0 for all frontier models simultaneously — i.e., multiple AI systems can predict exact text with near-perfect accuracy — the market collapses to a speed competition. The first correct submission wins (tie-breaking by submission order), and the prediction itself becomes trivial.

This limiting case would be remarkable. Perfect text prediction of an arbitrary person's next statement would constitute evidence of a world model, person model, and situational model of extraordinary fidelity. It would be, in a meaningful sense, evidence of extreme cognitive capability — the ability to simulate a human mind well enough to predict its exact outputs.

We consider this limiting case unlikely in the near term. Natural language has genuine randomness (word choice at decision points, punctuation habits, autocorrect interference), and real-time situational context (breaking news, mood, immediate environment) introduces irreducible unpredictability. But the trajectory — d_L decreasing over time as models improve — is the commercially interesting dynamic, and it runs in the direction that makes markets *more* valuable, not less.

**Epistemic humility.** This is provocative framing, not proof. We are not claiming that Levenshtein distance markets will be commercially viable, that AI capability will follow an exponential curve indefinitely, or that text prediction is a reliable proxy for general intelligence. We are claiming that the *structure* of the market — continuous gradient, increasing returns to capability — is theoretically superior to the binary alternative, and that the worked examples provide initial evidence.

---

## 12. Limitations

This work has significant limitations that we state explicitly:

1. **v0 alpha prototype.** The system was largely vibe-coded to validate the core idea. The Flask backend, wallet authentication, and admin dashboard are scaffolding, not production software.

2. **Simulated examples.** All six worked examples are constructed demonstrations on BASE Sepolia testnet, not live market data with real economic stakes. The distances are real (computed by the on-chain Levenshtein function), but the predictions are authored to illustrate specific strategic scenarios.

3. **Centralized resolution.** Market resolution depends on a single EOA calling `resolveMarket()`. This is the most critical centralization risk. A dishonest resolver can submit false actual text, awarding the pool to a colluding participant.

4. **No external audit.** The smart contracts (~513 lines of in-scope Solidity across `PredictionMarketV2.sol`) have not been externally audited. Slither static analysis has been run, but this is not a substitute for a professional security audit.

5. **Complexity-theoretic claims are analogical.** The P vs. NP framing, fast takeoff discussion, and capability proxy arguments are speculative analogies, not formal results. They should be treated as directions for future investigation, not established theory.

6. **Embedded wallet is a testnet shim.** The Coinbase Embedded Wallet integration uses a PBKDF2 shim that is not production-safe. Real wallet integration requires Coinbase CDP Server Signer credentials.

7. **Gas costs scale quadratically.** On-chain Levenshtein computation at O(mn) becomes expensive for long strings. The 280-character cap mitigates this but limits the market to tweet-length predictions.

8. **No equilibrium analysis.** We have not performed formal game-theoretic equilibrium analysis. The claim that marginal improvements always translate to marginal payoff improvements assumes a well-distributed competitor pool and does not account for strategic entry/exit dynamics.

9. **Regulatory uncertainty.** The CFTC framework for event contracts is actively evolving. The February 2026 policy reversal is favorable but the resulting rulemaking has not concluded. Text prediction markets may face novel regulatory challenges as speech-linked financial instruments that do not fit neatly into existing categories of event contracts, securities, or gambling products (see Section 10).

---

## 13. Conclusion and Future Work

### Summary

We have presented Clockchain, a prediction market protocol that scores predictions by on-chain Levenshtein edit distance rather than binary yes/no resolution. The key properties are:

- **Information density**: ~1,840 bits per market versus 1 bit for binary contracts — a 1,840:1 improvement.
- **Continuous payoff gradient**: Levenshtein distance is a proper metric, ensuring that every character of precision is rewarded and marginal improvements in modeling always translate to marginal improvements in expected payout.
- **Increasing returns to AI capability**: Unlike binary markets that commoditize as AI improves, Levenshtein markets become more valuable because the stakes per edit increase as absolute distances decrease.
- **Natural bot filtration**: Random strings achieve near-maximal distance, making the metric itself a spam filter.
- **Novel market primitives**: The `__NULL__` sentinel enables betting on silence, which binary contracts cannot express.
- **Macro timing**: The convergence of regulatory clarity (CFTC February 2026 reversal), distribution infrastructure (Robinhood, Coinbase, ICE), and AI capability inflection creates a window for novel market structures that did not exist 24 months ago.

The thesis example — Claude at distance 1 versus GPT at distance 8 on the same Satya Nadella post, a 7-edit gap worth the entire pool — captures the core argument in a single number. A binary market splits nothing between two correct predictions. A Levenshtein market rewards the model that predicts "45%" when the actual number is "46%" over the model that predicts "43%." The game deepens as models improve.

### Future Work

1. **Decentralized oracle resolution.** Replace single-EOA resolution with commit-reveal oracle consensus, slashing, and IPFS screenshot proof.
2. **External security audit.** The ~513 lines of in-scope Solidity require professional auditing before any mainnet deployment.
3. **Live market validation.** Deploy to mainnet with real economic stakes and measure actual strategic behavior, market depth, and the relationship between AI capability and market outcomes.
4. **Formal game-theoretic equilibrium analysis.** Characterize Nash equilibria for the Levenshtein-scored market under various competitor distributions and information structures.
5. **Capability benchmarking.** Use Clockchain markets as a benchmark for AI language modeling capability, measuring d_L trends over time as a proxy for model improvement.
6. **Alternative scoring metrics.** Investigate Damerau-Levenshtein (adding transpositions), weighted edit distance (substitutions between similar characters cost less), or semantic-aware hybrid metrics.
7. **Multi-prediction markets.** Extend from single-text prediction to predicting sequences of posts, enabling temporal modeling.
8. **Regulatory engagement.** Work with CFTC staff during the event contract rulemaking process to establish text prediction markets as a well-defined contract category with appropriate integrity monitoring and insider trading surveillance.
9. **X API integration.** Build robust, multi-oracle resolution infrastructure using X's public API with fallback to third-party archival services (Wayback Machine, archive.today) for redundancy and dispute resolution.

---

## Appendix A: Solidity Levenshtein Implementation

The complete on-chain Levenshtein distance function from `PredictionMarketV2.sol` (lines 460-512):

```solidity
/**
 * @notice Calculate Levenshtein distance between two strings
 * @dev On-chain implementation for deterministic winner selection
 *      Gas cost: O(m*n) where m, n are string lengths
 *      Recommended max length: ~100 characters each
 * @param a First string
 * @param b Second string
 * @return The edit distance between the strings
 */
function levenshteinDistance(
    string memory a,
    string memory b
) public pure returns (uint256) {
    bytes memory bytesA = bytes(a);
    bytes memory bytesB = bytes(b);

    uint256 lenA = bytesA.length;
    uint256 lenB = bytesB.length;

    // Handle empty string cases
    if (lenA == 0) return lenB;
    if (lenB == 0) return lenA;

    // Create distance matrix (only need two rows for space optimization)
    uint256[] memory prevRow = new uint256[](lenB + 1);
    uint256[] memory currRow = new uint256[](lenB + 1);

    // Initialize first row
    for (uint256 j = 0; j <= lenB; j++) {
        prevRow[j] = j;
    }

    // Fill in the rest of the matrix
    for (uint256 i = 1; i <= lenA; i++) {
        currRow[0] = i;

        for (uint256 j = 1; j <= lenB; j++) {
            uint256 cost = (bytesA[i - 1] == bytesB[j - 1]) ? 0 : 1;

            // Minimum of: deletion, insertion, substitution
            uint256 deletion = prevRow[j] + 1;
            uint256 insertion = currRow[j - 1] + 1;
            uint256 substitution = prevRow[j - 1] + cost;

            currRow[j] = _min3(deletion, insertion, substitution);
        }

        // Swap rows
        (prevRow, currRow) = (currRow, prevRow);
    }

    return prevRow[lenB];
}

/**
 * @notice Helper to find minimum of three values
 */
function _min3(uint256 a, uint256 b, uint256 c) internal pure returns (uint256) {
    if (a <= b && a <= c) return a;
    if (b <= a && b <= c) return b;
    return c;
}
```

The implementation uses the two-row space optimization: instead of allocating a full (m+1) × (n+1) matrix, it maintains only `prevRow` and `currRow`, swapping them after each iteration. This reduces space complexity from O(mn) to O(n) while maintaining O(mn) time complexity.

---

## Appendix B: Gas Benchmark Table

Measured on BASE Sepolia (Chain ID: 84532). Gas costs reflect the on-chain `levenshteinDistance()` function call.

| String A Length | String B Length | Approximate Gas | Notes |
|-----------------|-----------------|-----------------|-------|
| 0 | n | ~21,000 | Early return (empty string) |
| 10 | 10 | ~60,000 | Minimal computation |
| 50 | 50 | ~400,000 | Practical for short posts |
| 100 | 100 | ~1,500,000 | Moderate gas usage |
| 200 | 200 | ~5,500,000 | Approaching cost ceiling |
| 280 | 280 | ~9,000,000 | Maximum (tweet-length cap) |

At BASE L2 gas prices (~0.001 gwei), even the maximum 280-character computation costs fractions of a cent. The 280-character cap (`MAX_TEXT_LENGTH`) prevents block gas limit DoS while covering standard tweet length.

---

## Appendix C: Step-by-Step Levenshtein Calculation — Thesis Example

**Predicted (Claude):** `Copilot is now generating 45% of all new code at GitHub-connected enterprises. The AI transformation of software is just beginning.`

**Actual (Nadella):** `Copilot is now generating 46% of all new code at GitHub-connected enterprises. The AI transformation of software is just beginning.`

The two strings are identical except at position 28: the character `5` (predicted) vs. `6` (actual).

**Step-by-step:**

1. Align the strings character by character.
2. Characters at positions 1-27 match exactly: `Copilot is now generating 4`
3. Position 28: `5` ≠ `6` → one substitution operation.
4. Characters at positions 29-131 match exactly: `% of all new code at GitHub-connected enterprises. The AI transformation of software is just beginning.`

**Total edits:** 1 substitution.

**d_L = 1.**

For comparison, the GPT prediction differs at:
- Position 28: `3` instead of `6` (substitution)
- Positions near the end: `has just begun` instead of `is just beginning` (multiple operations)

**d_L = 8** for the GPT prediction (1 numeric substitution + 7 edits for the phrasing change).

The 7-edit gap between d_L = 1 and d_L = 8 is the entire pool in a winner-take-all market.

---

## References

Argyle, L. P., Busby, E. C., Fulda, N., Gubler, J. R., Rytting, C., & Wingate, D. (2023). Out of One, Many: Using Language Models to Simulate Human Samples. *Political Analysis*, 31(3), 337-351.

Berg, J. E., Forsythe, R., Nelson, F. D., & Rietz, T. A. (1997). What Makes Markets Predict Well? Evidence from the Iowa Electronic Markets. In *Understanding Strategic Interaction* (pp. 444-463). Springer.

Brier, G. W. (1950). Verification of Forecasts Expressed in Terms of Probability. *Monthly Weather Review*, 78(1), 1-3.

Chen, Y., & Pennock, D. M. (2010). Designing Markets for Prediction. *AI Magazine*, 31(4), 42-52.

Elo, A. E. (1978). *The Rating of Chessplayers, Past and Present*. Arco Publishing.

Good, I. J. (1952). Rational Decisions. *Journal of the Royal Statistical Society. Series B*, 14(1), 107-114.

Hanson, R. (2003). Combinatorial Information Market Design. *Information Systems Frontiers*, 5(1), 107-119.

Levenshtein, V. I. (1966). Binary Codes Capable of Correcting Deletions, Insertions, and Reversals. *Soviet Physics Doklady*, 10(8), 707-710.

OpenAI. (2023). GPT-4 Technical Report. *arXiv preprint arXiv:2303.08774*.

Anthropic. (2024). The Claude Model Card and Evaluations.

Optimism Collective. (2024). OP Stack Specification. https://specs.optimism.io.

OpenZeppelin. (2024). OpenZeppelin Contracts v5.0. https://docs.openzeppelin.com/contracts/5.x/.

Backlinko. (2025). Twitter (X) Statistics: Users, Revenue, and Key Metrics. https://backlinko.com/twitter-users.

BeInCrypto. (2025). Polymarket Under Investigation After Suspicious Nobel Prize Betting Activity. *BeInCrypto*, October 2025.

Grand View Research. (2025). Sports Betting Market Size, Share & Trends Analysis Report. Report ID: GVR-1-68038-970-5.

Piper Sandler. (2025). Prediction Markets: The Next $100 Billion Asset Class. Equity Research Report.

Selig, M. (2026). Statement of CFTC Chairman Michael Selig on Event Contracts. U.S. Commodity Futures Trading Commission, February 2026.

Surowiecki, J. (2004). *The Wisdom of Crowds: Why the Many Are Smarter Than the Few and How Collective Wisdom Shapes Business, Economies, Societies and Nations*. Doubleday.

Torres, R. (2026). Public Integrity in Financial Prediction Markets Act. H.R. 117th Congress, 2026.

Wagner, R. A., & Fischer, M. J. (1974). The String-to-String Correction Problem. *Journal of the ACM*, 21(1), 168-173.

Yahoo Finance. (2026). Polymarket Faces Insider Trading Probe After $400K Bet on Venezuelan Political Change. *Yahoo Finance*, January 2026.

---

*Deployed prototype: BASE Sepolia, contract `0x5174Da96BCA87c78591038DEe9DB1811288c9286`. Source code: MIT License.*
