import {
  BarChart, Bar, XAxis, YAxis, Cell, ResponsiveContainer, LabelList,
} from 'recharts'

const data = [
  { name: 'Kalshi', bits: 1, color: '#FF6B35' },
  { name: 'Polymarket', bits: 1, color: '#7B3FE4' },
  { name: 'Proteus', bits: 1840, color: '#00d9ff' },
]

function CustomLabel({ x, y, width, height, value, index }) {
  if (index !== 2) return null
  return (
    <text
      x={x + width + 8}
      y={y + height / 2}
      fill="#fff"
      fontWeight="700"
      fontSize={14}
      fontFamily="Consolas, Monaco, Courier New, monospace"
      dominantBaseline="central"
    >
      1,840:1
    </text>
  )
}

export default function InformationPerContract() {
  return (
    <div className="card">
      <h3>Information Per Contract</h3>
      <p className="subtitle">
        Bits of information resolvable by a single contract.
      </p>

      <ResponsiveContainer width="100%" height={160}>
        <BarChart
          data={data}
          layout="vertical"
          margin={{ top: 0, right: 80, left: 0, bottom: 0 }}
        >
          <XAxis
            type="number"
            scale="log"
            domain={[0.5, 5000]}
            tick={{ fill: '#666', fontSize: 12, fontFamily: 'Consolas, monospace' }}
            tickFormatter={(v) => v.toLocaleString()}
            ticks={[1, 10, 100, 1000]}
            axisLine={{ stroke: '#1a1a1a' }}
            tickLine={{ stroke: '#1a1a1a' }}
          />
          <YAxis
            type="category"
            dataKey="name"
            width={100}
            tick={{ fill: '#b8b8b8', fontSize: 13 }}
            axisLine={false}
            tickLine={false}
          />
          <Bar dataKey="bits" radius={[0, 3, 3, 0]} barSize={28}>
            {data.map((d, i) => (
              <Cell key={i} fill={d.color} />
            ))}
            <LabelList dataKey="bits" content={<CustomLabel />} />
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      <p className="footnote">
        Conservative estimate. Uniform distribution over outcome space. Natural
        language concentrates probability mass, but even the "likely" region dwarfs
        &#123;0, 1&#125; by hundreds of orders of magnitude.
      </p>
    </div>
  )
}
