# Proteus vs. Binary Markets: Visualization Spec

> **Audience:** Technical readers coming from the whitepaper. They understand information theory, metric spaces, and market microstructure. They don't need hand-holding -- they need the argument rendered visually so it hits harder than the math alone.
>
> **Job of this page:** Five charts that make one point: binary prediction markets are a degenerate special case of what Proteus does, and they get *worse* as AI gets *better*, while Proteus does the opposite.

---

## For the implementing AI

Build a single React page. Five chart components. Dark theme. No external data fetching -- everything is hardcoded from the numbers below, which are sourced from the Proteus whitepaper (February 2026) and public market data.

**Stack:** React + Recharts (`npm install recharts`). Functional components, hooks only.

**Design system:**
- Background: `#0a0a0a`. Cards: `#111111` with `1px solid #1a1a1a` border.
- Proteus: `#00d9ff` (cyan). Polymarket: `#7B3FE4`. Kalshi: `#FF6B35`.
- Win/success: `#00ff00`. Warning: `#ffaa00`. Muted: `#666`. Body: `#b8b8b8`.
- Font: system stack. Data labels: `'Consolas', monospace`.
- Each chart gets a card with `<h3>` title, one-line subtitle in muted text, and the chart. No decorative elements. Let the data do the work.
- Responsive: single column on mobile, cards stack naturally.

**Page title:** `Binary Markets Have a Ceiling. This Doesn't.`

---

## Chart 1: "Information Per Contract"

**Type:** Horizontal bar chart, log-scale x-axis.

**The point:** A binary contract carries 1 bit. A Proteus contract carries 1,840 bits. That's not an incremental improvement -- it's a category change.

| Platform | Bits | How |
|----------|------|-----|
| Kalshi | 1 | `log₂(2) = 1` -- outcome is {Yes, No} |
| Polymarket | 1 | Same -- {Yes, No} on Polygon |
| **Proteus** | **1,840** | `280 × log₂(95) = 280 × 6.57` -- 280-char string over 95-char printable ASCII |

**Rendering notes:**
- Log scale is mandatory (otherwise the binary bars are sub-pixel).
- Annotate the Proteus bar with `1,840:1` in bold.
- Below the chart, one line: *"Conservative estimate. Uniform distribution over outcome space. Natural language concentrates probability mass, but even the 'likely' region dwarfs {0, 1} by hundreds of orders of magnitude."*

---

## Chart 2: "Outcome Space"

**Type:** Vertical log₁₀ axis from 0 to 560, with labeled markers. Not a bar chart -- a scale visualization. Think thermometer or ruler.

**The point:** The outcome space of a binary market is 2. The outcome space of a Proteus market is 10^554. There is no chart that can make these proportional. That *is* the point.

**Markers on the scale:**

| log₁₀ | What |
|-------|------|
| 0.3 | Binary market: 2 outcomes |
| 11 | World population: ~8 × 10¹⁰ |
| 80 | Atoms in the observable universe: ~10⁸⁰ |
| 120 | Possible chess games (Shannon number): ~10¹²⁰ |
| **554** | **Proteus outcome space: 95²⁸⁰ ≈ 10⁵⁵⁴** |

**Rendering notes:**
- Use a single vertical bar, full height of the card, with markers at the correct log positions.
- Binary market marker at the very bottom, barely above zero. Proteus at the top.
- Between the universe marker (80) and Proteus (554), add a bracket: *"474 orders of magnitude beyond all atoms in the observable universe"*.
- The visual gap between 0.3 and 554 on a linear rendering of the log scale should feel absurd. That's correct.

---

## Chart 3: "The Payoff Cliff vs. The Payoff Gradient"

**Type:** Two side-by-side line charts (or one chart with two series and a vertical split). X-axis is prediction quality, Y-axis is expected payout.

**The point:** Binary markets are a step function. You're either right or you're not. Proteus is a continuous curve. Every character of precision pays.

**Left panel -- Binary (Kalshi / Polymarket):**

```
Prediction quality:  0%   25%   50%   75%   99%   100%
Expected payout:     0     0     0     0     0    100%
```

This is a Heaviside step function. Label it: *"Almost right = completely wrong."*

**Right panel -- Proteus (Levenshtein):**

| d_L (edit distance) | Win probability (illustrative) | Label |
|--------------------|-----------------------------|-------|
| 0 | ~100% | Perfect match |
| 1 | ~95% | One character off (Claude on Nadella) |
| 5 | ~75% | Minor phrasing diff |
| 8 | ~55% | GPT on Nadella |
| 15 | ~30% | Right structure, wrong details |
| 30 | ~10% | Right topic |
| 60 | ~2% | Theme only |
| 150+ | ~0% | Random noise |

This is a smooth, monotonically decreasing curve. Label it: *"Every edit counts. Payoff is Lipschitz-continuous w.r.t. prediction quality."*

**Callout box between the panels:**

> **The thesis example.** Satya Nadella posts about Copilot. Claude predicts "45%" -- actual is "46%." d_L = 1. GPT predicts "43%" and paraphrases the ending. d_L = 8.
>
> **Binary market:** Both "predicted correctly." Nobody wins anything interesting.
> **Proteus:** The 7-edit gap is the entire pool. `argmin d_L` takes 93%.

---

## Chart 4: "AI Gets Better. Then What?"

**Type:** Dual-line chart. X-axis is time / AI capability. Y-axis is "strategic depth" or "market value" (relative, 0-100). Two diverging lines.

**The point:** Binary markets have an inverted-U relationship with AI capability. They peak when uncertainty is high and collapse as models converge. Proteus has a monotonically increasing relationship. The better AI gets, the more each edit is worth.

**Binary markets (purple/orange dashed line):**

| Stage | AI accuracy | Market depth | Why |
|-------|------------|-------------|-----|
| 2020 | ~55% | 25 | Uncertainty high, thin markets |
| 2022 | ~65% | 50 | Growing, spreads wide |
| 2024 | ~80% | 75 | **Peak.** $40B volume. Everyone disagrees just enough. |
| 2025 | ~90% | 55 | Models converging. Spreads tighten. |
| 2026 | ~95% | 35 | Commoditization. Everyone's model says "87% yes." |
| 2028+ | ~99% | 10 | Spread → 0. Market is a coin flip over residual noise. |

**Proteus (cyan solid line):**

| Stage | Best d_L | Market depth | Why |
|-------|---------|-------------|-----|
| 2020 | ~150 | 5 | Random noise. No AI can do this yet. |
| 2022 | ~80 | 15 | Theme-level accuracy. Signal emerges. |
| 2024 | ~30 | 40 | Structural accuracy. AI captures sentence patterns. |
| 2025 | ~12 | 60 | Phrase-level. Every word choice matters. |
| 2026 | ~5 | 80 | Character-level competition. "45%" vs "46%" = pool. |
| 2028+ | ~1-2 | 95 | Frontier models separated by single edits. Maximum stakes per edit. |

**Rendering notes:**
- The crossover happens around 2025-2026. Mark it.
- Binary line: dashed, peaks and falls. Annotate the peak: *"$40B in 2025. All binary."*
- Proteus line: solid, only goes up. Annotate the right side: *"Increasing returns to AI capability."*
- Annotate the divergence zone: *"Binary: diminishing returns. Proteus: deepening."*
- This is the thesis in one picture. It needs to be immediately legible.

---

## Chart 5: "Six Markets. Six Winners. Six Lessons."

**Type:** Grouped horizontal bar chart. Six groups (one per worked example). Within each group, bars for each submitter sorted by d_L ascending. Winner bar in cyan, others in gray gradient.

**The point:** Different market conditions produce different winning strategies. AI roleplay wins on rehearsed targets. Insiders win on contextual targets. Null traders win on silence. Bots always lose. The metric is the game.

**Data:**

**@elonmusk** -- "Starship flight 2 is GO for March. Humanity becomes multiplanetary or we die trying."
| Submitter | d_L | Color |
|-----------|-----|-------|
| Claude roleplay | 12 | cyan (winner) |
| Human fan | 59 | gray |
| GPT (lazy prompt) | 66 | gray |
| Bot (entropy) | 72 | gray |
Gap annotation: **47 edits.** *"AI captures tone. Theme doesn't pay."*

**@sama** -- "we are now confident AGI is achievable with current techniques. announcement soon."
| Submitter | d_L | Color |
|-----------|-----|-------|
| Ex-OpenAI engineer | 4 | cyan (winner) |
| GPT roleplay | 18 | gray |
| Human (cynical) | 59 | gray |
Gap: **14 edits.** *"Insider info beats AI. 'we are now confident' vs 'we now believe' = 14 edits."*

**@zuck** -- "Introducing Meta Ray-Ban with live AI translation. 12 languages. The future is on your face."
| Submitter | d_L | Color |
|-----------|-----|-------|
| Meta intern | 3 | cyan (winner) |
| AI roleplay | 25 | gray |
| Human (guessing) | 73 | gray |
| Spam bot | 83 | gray |
Gap: **22 edits.** *"Draft deck access = 22-edit advantage over frontier AI."*

**@JensenHuang** -- *(nothing posted)* -- resolved with `__NULL__`
| Submitter | d_L | Color |
|-----------|-----|-------|
| Null trader (`__NULL__`) | 0 | cyan (winner) |
| Human (guessing) | 46 | gray |
| AI roleplay | 90 | gray |
Gap: **46 edits.** *"AI can't predict silence. Binary markets can't express it. d_L = 0."*

**@satyanadella** -- THE THESIS EXAMPLE -- "Copilot is now generating 46% of all new code at GitHub-connected enterprises. The AI transformation of software is just beginning."
| Submitter | d_L | Color |
|-----------|-----|-------|
| Claude roleplay | 1 | cyan (winner) -- **HIGHLIGHT THIS ROW** |
| GPT roleplay | 8 | amber |
| Human (vague) | 101 | gray |
Gap: **7 edits.** *"Same corpus. Same prompt. 7 characters = entire pool. Binary market: tie."*

**@tim_cook** -- "Apple Intelligence is now available in 30 countries. Privacy and AI, together."
| Submitter | d_L | Color |
|-----------|-----|-------|
| AI roleplay | 28 | cyan (winner) |
| Human (thematic) | 53 | gray |
| Random bot | 65 | gray |
| Degenerate bot ("aaa...") | 73 | gray |
Gap: **25 edits.** *"Random strings → d_L ≈ max(m,n). The metric is the spam filter."*

**Rendering notes:**
- Nadella (thesis example) gets a gold/amber left border and a `THESIS` badge. It should visually pop.
- Winner bars are full cyan. Runner-up bars in `#444`. Rest in `#2a2a2a`.
- Each group gets the gap annotation right-aligned: "Gap: N edits" in bold.
- The lesson text goes below each group in muted italic.
- Bars should be proportional to d_L, max scale around 110 (to fit Human vague at 101).

---

## Closing annotation (below all charts)

Render as a `<blockquote>` in muted text at the bottom of the page:

> All distances computed on-chain by `PredictionMarketV2.levenshteinDistance()` on BASE Sepolia (contract `0x5174...9286`). 513 lines of Solidity. 259+ passing tests. O(m*n) dynamic programming, two-row space optimization, 280-char cap. The math is transparent and the scoring is tamper-proof.
>
> $40B flowed through binary prediction markets in 2025. Projected $222.5B in 2026. All of it resolves to {0, 1}. None of it rewards precision. That's the gap.

---

## What NOT to build

- No pie/donut charts (fee breakdown is interesting but doesn't serve the argument).
- No animated counters or scrolljacking.
- No "vs competitor" feature matrices. This is not a SaaS landing page.
- No tooltips that contain the actual argument. The argument should be visible without hovering.
- No 3D anything.

Keep it flat, typographic, data-dense, and honest. Five charts. One argument. Ship it.
