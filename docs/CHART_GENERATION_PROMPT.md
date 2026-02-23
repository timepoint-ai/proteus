# Chart Generation Prompt: Proteus vs Binary Prediction Markets

> **For AI code generation.** This document contains all the data and design instructions needed to build a React page with 4-6 comparison charts. The coding AI should use this as the sole source of truth.

---

## Context

Proteus is a prediction market protocol that scores predictions by **Levenshtein edit distance** (character-by-character closeness to the actual text) instead of binary yes/no resolution. The charts below compare Proteus to the two dominant binary prediction market platforms: **Polymarket** (crypto-native, Polygon) and **Kalshi** (CFTC-regulated, centralized).

The goal: make the structural differences visually obvious to someone who has never heard of Proteus. Each chart should stand alone as a compelling comparison.

---

## Tech Stack

- **React** (functional components, hooks)
- **Recharts** for all charts (install: `npm install recharts`)
- **Dark theme**: background `#0a0a0a`, card background `#111111`, border `#222222`
- **Color palette**:
  - Proteus: `#00d9ff` (cyan)
  - Polymarket: `#7B3FE4` (purple)
  - Kalshi: `#FF6B35` (orange)
  - Accent green: `#00ff00`
  - Accent amber: `#ffaa00`
  - Muted text: `#888888`
  - Body text: `#b8b8b8`
- **Font**: system font stack (`-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`), monospace for data (`'Consolas', 'Monaco', monospace`)
- Each chart should be in its own card component with a title, subtitle, and optional annotation

---

## Chart 1: Information Density Per Market (Log-Scale Bar Chart)

**Type**: Horizontal bar chart, logarithmic x-axis

**Title**: "Information Density Per Market"
**Subtitle**: "Bits of information encoded in a single market contract"

**Data**:

| Platform | Bits per Market | Label |
|----------|----------------|-------|
| Kalshi | 1 | "Binary: Yes or No" |
| Polymarket | 1 | "Binary: Yes or No" |
| Proteus | 1,840 | "280-char text over 95-char ASCII alphabet" |

**How to compute**: Kalshi and Polymarket resolve to {0, 1}, so log2(2) = 1 bit. Proteus: 280 characters over printable ASCII (95 chars) = 280 x log2(95) = 280 x 6.57 = 1,840 bits.

**Design notes**:
- Use a **logarithmic scale** on the x-axis (otherwise the binary bars are invisible)
- Show the ratio `1,840:1` as an annotation on or near the Proteus bar
- The visual contrast should be dramatic even on log scale -- 1 bit vs 1,840 bits
- Add a footnote: "Conservative estimate assuming uniform distribution. Natural language structure concentrates probability mass but the combinatorial explosion ensures the 'likely' region is still astronomically larger than {0, 1}."

---

## Chart 2: Outcome Space Comparison (Log-Scale Visualization)

**Type**: Custom visualization -- stacked/comparative representation with logarithmic labels

**Title**: "Possible Outcomes Per Market"
**Subtitle**: "Number of distinct outcomes a single market contract can resolve to"

**Data**:

| Platform | Outcomes | Log10 | Comparison |
|----------|----------|-------|------------|
| Kalshi | 2 | 0.3 | "2 outcomes: Yes or No" |
| Polymarket | 2 | 0.3 | "2 outcomes: Yes or No" |
| Proteus | ~10^554 | 554 | "95^280 possible strings" |

**Context annotations to display**:
- Atoms in the observable universe: ~10^80
- Possible chess games (Shannon number): ~10^120
- Proteus outcome space: ~10^554
- "Exceeds atoms in the universe by 474 orders of magnitude"

**Design notes**:
- This is hard to visualize because the numbers are so different. Consider a "powers of 10" staircase or a dot-scale representation where each dot = 10 orders of magnitude.
- The point is to create visceral shock: 2 outcomes vs 10^554 outcomes
- Don't try to make the bars proportional (impossible). Instead, use labeled segments on a log10 axis from 0 to 560, with callout markers for universe atoms (80), chess games (120), and Proteus (554).

---

## Chart 3: Payoff Surface -- Binary Cliff vs Continuous Gradient (Line/Area Chart)

**Type**: Dual-panel line chart or overlaid area chart

**Title**: "Payoff Structure: Binary Cliff vs Continuous Gradient"
**Subtitle**: "How prediction quality maps to expected payout"

**Panel A -- Binary Market (Kalshi/Polymarket)**:

| Prediction Quality | Payout (% of max) |
|-------------------|-------------------|
| 0% correct | 0% |
| 25% correct | 0% |
| 50% correct | 0% |
| 75% correct | 0% |
| 99% correct | 0% |
| 100% correct | 100% |

This is a step function: 0% payout for anything less than perfectly correct, 100% payout for exact correctness. In binary markets, "almost right" pays nothing. You either predicted the outcome or you didn't.

**Panel B -- Proteus (Levenshtein)**:

| Edit Distance (d_L) | Relative Payout Signal | Label |
|---------------------|----------------------|-------|
| 0 | 100% | "Perfect match" |
| 1 | 98% | "One character off" |
| 5 | 85% | "Minor phrasing difference" |
| 10 | 70% | "Close but imprecise" |
| 25 | 40% | "Right topic, wrong wording" |
| 50 | 15% | "Thematic only" |
| 100 | 3% | "Mostly wrong" |
| 200+ | 0% | "Random noise" |

These are illustrative win-probability curves, not exact payouts. The key insight: in a winner-take-all Levenshtein market, your probability of winning is monotonically decreasing in d_L, and every edit of improvement increases your win probability. The function is Lipschitz-continuous -- there is no cliff.

**Design notes**:
- Panel A should look like a cliff/step function (dramatic vertical line at "correct")
- Panel B should look like a smooth decreasing curve
- Label the critical difference: "Every edit counts" on the Proteus side, "Close doesn't count" on the binary side
- Use the thesis example as a callout: "Claude (d_L=1) vs GPT (d_L=8): 7-edit gap = entire pool. In a binary market, both 'correct' -- no one wins."

---

## Chart 4: AI Capability vs Market Value (Diverging Trajectories)

**Type**: Dual-line chart with diverging trajectories over time

**Title**: "AI Gets Smarter: What Happens to Markets?"
**Subtitle**: "Binary markets commoditize. Text markets deepen."

**X-axis**: AI Capability Level (qualitative stages)
**Y-axis**: Market Value / Strategic Depth (relative, 0-100 scale)

**Data -- Binary Markets (Kalshi/Polymarket)**:

| AI Capability Stage | Accuracy | Market Value | Note |
|--------------------|----------|-------------|------|
| 2020: Early | 55% | 30 | "Uncertainty high, markets active" |
| 2022: Growing | 65% | 55 | "Spreads still wide" |
| 2024: Strong | 80% | 75 | "Peak value -- $40B volume" |
| 2025: Converging | 90% | 60 | "Models agree, spreads tighten" |
| 2026: Near-perfect | 95% | 40 | "Commoditization begins" |
| 2028+: Superhuman | 99% | 15 | "Everyone's model says the same thing" |

**Data -- Proteus (Levenshtein)**:

| AI Capability Stage | Avg d_L | Market Value | Note |
|--------------------|---------|-------------|------|
| 2020: Early | 150+ | 10 | "Random noise, no signal" |
| 2022: Growing | 80 | 20 | "Theme-level accuracy" |
| 2024: Strong | 30 | 45 | "Structural accuracy" |
| 2025: Converging | 12 | 65 | "Phrase-level precision" |
| 2026: Near-perfect | 5 | 80 | "Every edit = high stakes" |
| 2028+: Superhuman | 1-2 | 95 | "Character-level competition" |

**Design notes**:
- The binary market line should rise then fall (inverted U)
- The Proteus line should rise continuously (monotonically increasing)
- The crossover point (where Proteus becomes more valuable than binary) is the key visual moment
- Annotate the divergence: "Binary: diminishing returns to AI improvement" vs "Proteus: increasing returns to AI improvement"
- This is the core thesis visualization. Make it clean and compelling.

---

## Chart 5: Worked Example Comparison Table (Interactive/Visual)

**Type**: Horizontal bar chart showing edit distances for the 6 worked examples

**Title**: "Six Markets, Six Strategies"
**Subtitle**: "Edit distance (d_L) for each submission across 6 simulated markets on BASE Sepolia"

**Data** (each market is a group, each submitter is a bar within the group):

**Market 1: @elonmusk (Starship)**
- Claude roleplay: d_L = 12 (winner, cyan)
- Human fan: d_L = 59
- GPT (lazy prompt): d_L = 66
- Bot (entropy): d_L = 72

**Market 2: @sama (AGI announcement)**
- Ex-OpenAI engineer: d_L = 4 (winner, cyan)
- GPT roleplay: d_L = 18
- Human (cynical): d_L = 59

**Market 3: @zuck (Meta Ray-Ban)**
- Meta intern: d_L = 3 (winner, cyan)
- AI roleplay: d_L = 25
- Human (guessing): d_L = 73
- Spam bot: d_L = 83

**Market 4: @JensenHuang (Silence)**
- Null trader (__NULL__): d_L = 0 (winner, cyan)
- Human (guessing): d_L = 46
- AI roleplay: d_L = 90

**Market 5: @satyanadella -- THE THESIS EXAMPLE**
- Claude roleplay: d_L = 1 (winner, cyan, highlighted)
- GPT roleplay: d_L = 8
- Human (vague): d_L = 101

**Market 6: @tim_cook (Apple Intelligence)**
- AI roleplay: d_L = 28 (winner, cyan)
- Human (thematic): d_L = 53
- Random bot: d_L = 65
- Degenerate bot: d_L = 73

**Design notes**:
- Winner bars in cyan, others in graduated grays
- Market 5 (Nadella) should have special visual treatment -- gold border, "THESIS EXAMPLE" label
- Sort bars within each market by d_L (lowest first)
- Add a label for each market showing the "gap" (winner d_L vs runner-up d_L): "Gap: 47", "Gap: 14", "Gap: 22", "Gap: 46", "Gap: 7", "Gap: 25"
- The key insight per market:
  - 1: "AI captures tone; theme doesn't pay"
  - 2: "Insider info beats AI"
  - 3: "Rehearsed copy leaks"
  - 4: "Betting on silence -- AI can't predict inaction"
  - 5: "AI vs AI: 7-edit gap = entire pool"
  - 6: "Random strings -> near-maximal distance (metric = spam filter)"

---

## Chart 6: Fee Structure & Market Economics (Donut/Pie Chart + Comparison)

**Type**: Side-by-side comparison: Proteus fee breakdown donut + binary market fee comparison

**Title**: "Market Economics"
**Subtitle**: "Where the money goes"

**Proteus Fee Breakdown (7% of pool)**:

| Recipient | Share of Fee | Share of Volume |
|-----------|-------------|----------------|
| Oracles | 28.6% | 2.0% |
| Builder Pool | 28.6% | 2.0% |
| Genesis NFT Holders | 20.0% | 1.4% |
| Node Operators | 14.3% | 1.0% |
| Market Creators | 14.3% | 1.0% |

**Payout split**: 93% to winner, 7% platform fee

**Comparison data**:

| Platform | Fee Structure | Winner Gets |
|----------|-------------|-------------|
| Proteus | 7% of pool | 93% of pool (winner-take-all, lowest d_L) |
| Polymarket | ~2% spread (maker-taker) | Binary: full position value if correct |
| Kalshi | $0.01-$0.99 per contract + fees | Binary: $1.00 per contract if correct |

**Design notes**:
- Proteus donut chart with 5 segments in the cyan color family (different saturations/brightnesses)
- Show the 93/7 split prominently
- The comparison table can be a simple styled table below the donut
- Key difference to highlight: Proteus fees fund a decentralized ecosystem (oracles, nodes, builders, NFT holders, creators). Binary platform fees go to the platform operator.

---

## Additional Data Points for Annotations

Use these throughout the charts as callouts, footnotes, or hover tooltips:

**Market size**:
- 2025 combined Polymarket + Kalshi volume: ~$40 billion
- 2026 projected: $222.5 billion, 445 billion contracts (47% YoY growth)
- Piper Sandler TAM estimate: $100 billion+ within the decade
- Robinhood event trading: 11 billion contracts, fastest-growing product in company history
- ICE (NYSE parent) invested $2 billion in Polymarket at $15B valuation
- Kalshi: $11B valuation, 50x user growth, 100x volume growth YoY
- Global sports betting: $100.9B (2024), projected $187B by 2030 at 11% CAGR
- 89% of Kalshi revenue from sports-related event contracts

**Proteus specifics**:
- Contract: PredictionMarketV2 at `0x5174Da96BCA87c78591038DEe9DB1811288c9286` on BASE Sepolia
- 513 lines of Solidity
- 259+ passing tests (109 contract, 135 unit, 15 integration)
- MAX_TEXT_LENGTH: 280 (tweet length)
- MIN_BET: 0.001 ETH
- Betting cutoff: 1 hour before market end
- Gas costs: ~400K gas (50 chars) to ~9M gas (280 chars) for Levenshtein computation
- At BASE L2 gas prices (~0.001 gwei), even max computation costs fractions of a cent

**The thesis in one paragraph**:
Binary prediction markets encode 1 bit of information per contract. As AI forecasting converges, spreads vanish and the market commoditizes. Text prediction over 280-character ASCII encodes ~1,840 bits per market -- a 1,840:1 improvement in information density. Levenshtein distance is a proper metric (identity, symmetry, triangle inequality), so payoffs are a continuous gradient, not a binary cliff. The approaching AI capability explosion does not flatten this market -- it deepens it, because the stakes per edit increase as absolute distances decrease.

---

## Implementation Notes

1. **Each chart should be a self-contained React component** that can be imported individually or rendered together on a single page.

2. **Responsive**: Charts should work on mobile (stack panels vertically, reduce font sizes).

3. **Animations**: Subtle entrance animations on scroll (fade-in, not flashy). Recharts has built-in animation support -- use it with `isAnimationActive={true}`.

4. **Tooltips**: All charts should have hover tooltips with the detailed data.

5. **Export**: The page should be a single `ComparisonCharts.tsx` (or split into `Chart1.tsx` through `Chart6.tsx` with an `index.tsx` that composes them).

6. **No external data fetching**: All data is hardcoded from the values above. This is a static comparison page.

7. **Accessibility**: Use aria-labels on chart elements. Ensure color contrast meets WCAG AA.

8. **The page title**: "Proteus vs Binary Prediction Markets" with subtitle "Why text prediction is a different category of game"

---

*Data source: Proteus whitepaper (February 2026), landing page, and public market data. All Levenshtein distances computed by on-chain contract on BASE Sepolia.*
