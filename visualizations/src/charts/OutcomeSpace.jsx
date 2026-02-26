const MAX_LOG = 560
const SCALE_HEIGHT = 480

const markers = [
  { log: 0.3, label: 'Binary market', value: '2 outcomes', color: '#7B3FE4' },
  { log: 11, label: 'World population', value: '~8 \u00d7 10\u00b9\u2070', color: '#666' },
  { log: 80, label: 'Atoms in observable universe', value: '~10\u2078\u2070', color: '#666' },
  { log: 120, label: 'Possible chess games', value: '~10\u00b9\u00b2\u2070', color: '#888' },
  { log: 554, label: 'Proteus outcome space', value: '95\u00b2\u2078\u2070 \u2248 10\u2075\u2075\u2074', color: '#00d9ff' },
]

function pct(log) {
  return ((1 - log / MAX_LOG) * 100).toFixed(2) + '%'
}

export default function OutcomeSpace() {
  const universeTop = pct(80)
  const proteusTop = pct(554)
  const bracketTopNum = (1 - 554 / MAX_LOG) * SCALE_HEIGHT
  const bracketBottomNum = (1 - 80 / MAX_LOG) * SCALE_HEIGHT
  const bracketHeight = bracketBottomNum - bracketTopNum

  return (
    <div className="card">
      <h3>Outcome Space</h3>
      <p className="subtitle">
        Number of possible outcomes for a single contract (log\u2081\u2080 scale).
      </p>

      <div className="scale-container">
        <div className="scale-wrapper" style={{ height: SCALE_HEIGHT }}>
          <div className="scale-bar" />

          {/* Bracket between universe and Proteus */}
          <div
            className="bracket"
            style={{
              top: bracketTopNum,
              height: bracketHeight,
            }}
          />
          <div
            className="bracket-label"
            style={{
              top: bracketTopNum + bracketHeight / 2 - 16,
            }}
          >
            474 orders of magnitude beyond all atoms in the observable universe
          </div>

          {markers.map((m) => (
            <div
              className="scale-marker"
              key={m.log}
              style={{ top: pct(m.log) }}
            >
              <div className="dot" style={{ background: m.color }} />
              <div className="marker-label">
                <span className="marker-value" style={{ color: m.color }}>
                  10^{m.log}
                </span>
                <br />
                <span style={{ color: '#888' }}>{m.label}</span>
                <br />
                <span style={{ color: '#555', fontSize: '0.72rem' }}>{m.value}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <p className="footnote">
        There is no chart that can make these proportional. That <em>is</em> the
        point. A binary outcome sits at the bottom. Proteus sits 474 orders of
        magnitude above the number of atoms in the observable universe.
      </p>
    </div>
  )
}
