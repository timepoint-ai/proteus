import {
  LineChart, Line, XAxis, YAxis, ResponsiveContainer, ReferenceLine, Dot,
} from 'recharts'

const binaryData = [
  { quality: 0, payout: 0 },
  { quality: 25, payout: 0 },
  { quality: 50, payout: 0 },
  { quality: 75, payout: 0 },
  { quality: 99, payout: 0 },
  { quality: 99.9, payout: 0 },
  { quality: 100, payout: 100 },
]

const proteusData = [
  { distance: 0, payout: 100, label: 'Perfect match' },
  { distance: 1, payout: 95, label: 'd_L = 1 (Claude on Nadella)' },
  { distance: 5, payout: 75, label: 'Minor phrasing diff' },
  { distance: 8, payout: 55, label: 'GPT on Nadella' },
  { distance: 15, payout: 30, label: 'Right structure' },
  { distance: 30, payout: 10, label: 'Right topic' },
  { distance: 60, payout: 2, label: 'Theme only' },
  { distance: 150, payout: 0, label: 'Random noise' },
]

function BinaryDot(props) {
  const { cx, cy, payload } = props
  if (payload.quality === 100) {
    return <circle cx={cx} cy={cy} r={5} fill="#7B3FE4" stroke="#7B3FE4" />
  }
  return <circle cx={cx} cy={cy} r={3} fill="#7B3FE4" opacity={0.5} />
}

function ProteusDot(props) {
  const { cx, cy, payload } = props
  const highlight = payload.distance <= 1
  return (
    <circle
      cx={cx}
      cy={cy}
      r={highlight ? 5 : 3}
      fill="#00d9ff"
      opacity={highlight ? 1 : 0.7}
    />
  )
}

export default function PayoffGradient() {
  return (
    <div className="card">
      <h3>The Payoff Cliff vs. The Payoff Gradient</h3>
      <p className="subtitle">
        Binary markets are a step function. Proteus is a continuous curve.
      </p>

      <div className="panels">
        <div className="panel">
          <h4 style={{ color: '#7B3FE4' }}>Binary (Kalshi / Polymarket)</h4>
          <p className="panel-sub">"Almost right = completely wrong."</p>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart
              data={binaryData}
              margin={{ top: 8, right: 16, left: 0, bottom: 8 }}
            >
              <XAxis
                dataKey="quality"
                tick={{ fill: '#666', fontSize: 11, fontFamily: 'Consolas, monospace' }}
                tickFormatter={(v) => `${v}%`}
                axisLine={{ stroke: '#1a1a1a' }}
                tickLine={{ stroke: '#1a1a1a' }}
                label={{
                  value: 'Prediction quality',
                  position: 'insideBottom',
                  offset: -4,
                  fill: '#555',
                  fontSize: 11,
                }}
              />
              <YAxis
                domain={[0, 100]}
                tick={{ fill: '#666', fontSize: 11, fontFamily: 'Consolas, monospace' }}
                tickFormatter={(v) => `${v}%`}
                axisLine={{ stroke: '#1a1a1a' }}
                tickLine={{ stroke: '#1a1a1a' }}
                width={44}
              />
              <Line
                type="stepAfter"
                dataKey="payout"
                stroke="#7B3FE4"
                strokeWidth={2}
                dot={<BinaryDot />}
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="panel">
          <h4 style={{ color: '#00d9ff' }}>Proteus (Levenshtein)</h4>
          <p className="panel-sub">
            "Every edit counts. Payoff is Lipschitz-continuous w.r.t. prediction quality."
          </p>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart
              data={proteusData}
              margin={{ top: 8, right: 16, left: 0, bottom: 8 }}
            >
              <XAxis
                dataKey="distance"
                tick={{ fill: '#666', fontSize: 11, fontFamily: 'Consolas, monospace' }}
                axisLine={{ stroke: '#1a1a1a' }}
                tickLine={{ stroke: '#1a1a1a' }}
                label={{
                  value: 'Edit distance (d_L)',
                  position: 'insideBottom',
                  offset: -4,
                  fill: '#555',
                  fontSize: 11,
                }}
              />
              <YAxis
                domain={[0, 100]}
                tick={{ fill: '#666', fontSize: 11, fontFamily: 'Consolas, monospace' }}
                tickFormatter={(v) => `${v}%`}
                axisLine={{ stroke: '#1a1a1a' }}
                tickLine={{ stroke: '#1a1a1a' }}
                width={44}
              />
              <Line
                type="monotone"
                dataKey="payout"
                stroke="#00d9ff"
                strokeWidth={2}
                dot={<ProteusDot />}
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="callout">
        <strong>The thesis example.</strong> Satya Nadella posts about Copilot.
        Claude predicts "45%" — actual is "46%." d<sub>L</sub> = 1. GPT
        predicts "43%" and paraphrases the ending. d<sub>L</sub> = 8.
        <br /><br />
        <span className="label-binary">Binary market:</span> Both "predicted
        correctly." Nobody wins anything interesting.
        <br />
        <span className="label-proteus">Proteus:</span> The 7-edit gap is the
        entire pool. <code className="mono" style={{ color: '#00d9ff' }}>
        argmin d<sub>L</sub></code> takes 93%.
      </div>
    </div>
  )
}
