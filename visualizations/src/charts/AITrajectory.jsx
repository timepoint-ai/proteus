import {
  LineChart, Line, XAxis, YAxis, ResponsiveContainer, ReferenceLine,
  CartesianGrid, Tooltip,
} from 'recharts'

const data = [
  { year: '2020', binary: 25, proteus: 5 },
  { year: '2022', binary: 50, proteus: 15 },
  { year: '2024', binary: 75, proteus: 40 },
  { year: '2025', binary: 55, proteus: 60 },
  { year: '2026', binary: 35, proteus: 80 },
  { year: '2028+', binary: 10, proteus: 95 },
]

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div
      style={{
        background: '#111',
        border: '1px solid #1a1a1a',
        padding: '10px 14px',
        fontSize: '0.8rem',
        lineHeight: 1.6,
      }}
    >
      <div style={{ color: '#fff', fontWeight: 600, marginBottom: 4 }}>{label}</div>
      {payload.map((p) => (
        <div key={p.dataKey} style={{ color: p.color }}>
          {p.dataKey === 'binary' ? 'Binary markets' : 'Proteus'}: {p.value}
        </div>
      ))}
    </div>
  )
}

export default function AITrajectory() {
  return (
    <div className="card">
      <h3>AI Gets Better. Then What?</h3>
      <p className="subtitle">
        Binary market depth peaks and falls. Proteus depth only increases.
      </p>

      <ResponsiveContainer width="100%" height={340}>
        <LineChart data={data} margin={{ top: 16, right: 24, left: 0, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1a1a1a" />
          <XAxis
            dataKey="year"
            tick={{ fill: '#888', fontSize: 12 }}
            axisLine={{ stroke: '#1a1a1a' }}
            tickLine={{ stroke: '#1a1a1a' }}
          />
          <YAxis
            domain={[0, 100]}
            tick={{ fill: '#666', fontSize: 11, fontFamily: 'Consolas, monospace' }}
            axisLine={{ stroke: '#1a1a1a' }}
            tickLine={{ stroke: '#1a1a1a' }}
            width={40}
            label={{
              value: 'Strategic depth',
              angle: -90,
              position: 'insideLeft',
              fill: '#555',
              fontSize: 11,
              offset: 10,
            }}
          />
          <Tooltip content={<CustomTooltip />} />

          <Line
            type="monotone"
            dataKey="binary"
            stroke="#7B3FE4"
            strokeWidth={2}
            strokeDasharray="6 3"
            dot={{ r: 4, fill: '#7B3FE4', stroke: '#7B3FE4' }}
            isAnimationActive={false}
          />
          <Line
            type="monotone"
            dataKey="proteus"
            stroke="#00d9ff"
            strokeWidth={2.5}
            dot={{ r: 4, fill: '#00d9ff', stroke: '#00d9ff' }}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>

      <div
        style={{
          display: 'flex',
          justifyContent: 'center',
          gap: 32,
          marginTop: 12,
          fontSize: '0.82rem',
        }}
      >
        <span>
          <span
            style={{
              display: 'inline-block',
              width: 24,
              height: 2,
              background: '#7B3FE4',
              verticalAlign: 'middle',
              marginRight: 8,
              borderTop: '1px dashed #7B3FE4',
              borderBottom: '1px dashed #7B3FE4',
            }}
          />
          <span style={{ color: '#7B3FE4' }}>Binary markets</span>
          <span style={{ color: '#555', marginLeft: 6 }}>— peak at $40B (2024). Diminishing returns.</span>
        </span>
      </div>
      <div
        style={{
          display: 'flex',
          justifyContent: 'center',
          gap: 32,
          marginTop: 6,
          fontSize: '0.82rem',
        }}
      >
        <span>
          <span
            style={{
              display: 'inline-block',
              width: 24,
              height: 2.5,
              background: '#00d9ff',
              verticalAlign: 'middle',
              marginRight: 8,
            }}
          />
          <span style={{ color: '#00d9ff' }}>Proteus</span>
          <span style={{ color: '#555', marginLeft: 6 }}>— increasing returns to AI capability.</span>
        </span>
      </div>

      <p className="footnote" style={{ textAlign: 'center', marginTop: 16 }}>
        The crossover happens around 2025. As AI models converge on binary outcomes,
        spreads collapse and binary markets lose depth. Proteus deepens: the better AI
        gets, the more each edit is worth.
      </p>
    </div>
  )
}
