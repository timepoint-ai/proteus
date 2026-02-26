import InformationPerContract from './charts/InformationPerContract'
import OutcomeSpace from './charts/OutcomeSpace'
import PayoffGradient from './charts/PayoffGradient'
import AITrajectory from './charts/AITrajectory'
import SixMarkets from './charts/SixMarkets'

export default function App() {
  return (
    <div className="page">
      <h1 className="page-title">Binary Markets Have a Ceiling. This Doesn't.</h1>
      <p className="page-subtitle">
        Five charts. One argument. Data from the Proteus whitepaper (February 2026) and public market data.
      </p>

      <InformationPerContract />
      <OutcomeSpace />
      <PayoffGradient />
      <AITrajectory />
      <SixMarkets />

      <blockquote className="closing-quote">
        All distances computed on-chain by{' '}
        <code>PredictionMarketV2.levenshteinDistance()</code> on BASE Sepolia
        (contract <code>0x5174...9286</code>). 513 lines of Solidity. 259+ passing
        tests. O(m*n) dynamic programming, two-row space optimization, 280-char cap.
        The math is transparent and the scoring is tamper-proof.
        <br /><br />
        $40B flowed through binary prediction markets in 2025. Projected $222.5B in
        2026. All of it resolves to &#123;0, 1&#125;. None of it rewards precision.
        That's the gap.
      </blockquote>
    </div>
  )
}
