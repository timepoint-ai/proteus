const CYAN = '#00d9ff'
const AMBER = '#ffaa00'
const RUNNER_UP = '#444'
const GRAY = '#2a2a2a'
const MAX_DL = 110

const markets = [
  {
    handle: '@elonmusk',
    text: '"Starship flight 2 is GO for March. Humanity becomes multiplanetary or we die trying."',
    gap: 47,
    lesson: 'AI captures tone. Theme doesn\'t pay.',
    thesis: false,
    submissions: [
      { name: 'Claude roleplay', dl: 12, winner: true },
      { name: 'Human fan', dl: 59 },
      { name: 'GPT (lazy prompt)', dl: 66 },
      { name: 'Bot (entropy)', dl: 72 },
    ],
  },
  {
    handle: '@sama',
    text: '"we are now confident AGI is achievable with current techniques. announcement soon."',
    gap: 14,
    lesson: 'Insider info beats AI. "we are now confident" vs "we now believe" = 14 edits.',
    thesis: false,
    submissions: [
      { name: 'Ex-OpenAI engineer', dl: 4, winner: true },
      { name: 'GPT roleplay', dl: 18 },
      { name: 'Human (cynical)', dl: 59 },
    ],
  },
  {
    handle: '@zuck',
    text: '"Introducing Meta Ray-Ban with live AI translation. 12 languages. The future is on your face."',
    gap: 22,
    lesson: 'Draft deck access = 22-edit advantage over frontier AI.',
    thesis: false,
    submissions: [
      { name: 'Meta intern', dl: 3, winner: true },
      { name: 'AI roleplay', dl: 25 },
      { name: 'Human (guessing)', dl: 73 },
      { name: 'Spam bot', dl: 83 },
    ],
  },
  {
    handle: '@JensenHuang',
    text: '(nothing posted) \u2014 resolved with __NULL__',
    gap: 46,
    lesson: 'AI can\'t predict silence. Binary markets can\'t express it. d_L = 0.',
    thesis: false,
    submissions: [
      { name: 'Null trader (__NULL__)', dl: 0, winner: true },
      { name: 'Human (guessing)', dl: 46 },
      { name: 'AI roleplay', dl: 90 },
    ],
  },
  {
    handle: '@satyanadella',
    text: '"Copilot is now generating 46% of all new code at GitHub-connected enterprises. The AI transformation of software is just beginning."',
    gap: 7,
    lesson: 'Same corpus. Same prompt. 7 characters = entire pool. Binary market: tie.',
    thesis: true,
    submissions: [
      { name: 'Claude roleplay', dl: 1, winner: true, highlight: true },
      { name: 'GPT roleplay', dl: 8, runnerUp: true },
      { name: 'Human (vague)', dl: 101 },
    ],
  },
  {
    handle: '@tim_cook',
    text: '"Apple Intelligence is now available in 30 countries. Privacy and AI, together."',
    gap: 25,
    lesson: 'Random strings \u2192 d_L \u2248 max(m,n). The metric is the spam filter.',
    thesis: false,
    submissions: [
      { name: 'AI roleplay', dl: 28, winner: true },
      { name: 'Human (thematic)', dl: 53 },
      { name: 'Random bot', dl: 65 },
      { name: 'Degenerate bot ("aaa...")', dl: 73 },
    ],
  },
]

function BarRow({ name, dl, winner, runnerUp, highlight }) {
  const widthPct = Math.max((dl / MAX_DL) * 100, 1.5)
  let barColor = GRAY
  if (winner) barColor = highlight ? CYAN : CYAN
  else if (runnerUp) barColor = AMBER
  else barColor = RUNNER_UP

  // Override non-winner colors
  if (!winner && !runnerUp) barColor = RUNNER_UP

  return (
    <div className="bar-row">
      <div
        className="bar-label"
        style={{ color: winner ? '#fff' : '#666' }}
      >
        {name}
      </div>
      <div className="bar-track">
        <div
          className="bar-fill"
          style={{
            width: `${widthPct}%`,
            background: barColor,
            boxShadow: highlight ? `0 0 12px ${CYAN}40` : 'none',
          }}
        >
          <span className="bar-value" style={{ color: winner ? '#fff' : '#666' }}>
            {dl}
          </span>
        </div>
      </div>
    </div>
  )
}

export default function SixMarkets() {
  return (
    <div className="card">
      <h3>Six Markets. Six Winners. Six Lessons.</h3>
      <p className="subtitle">
        Different market conditions produce different winning strategies. The metric is
        the game.
      </p>

      {markets.map((m) => (
        <div
          key={m.handle}
          className={`market-group ${m.thesis ? 'thesis' : ''}`}
        >
          <div className="market-header">
            <span>
              <span className="market-handle">{m.handle}</span>
              {m.thesis && <span className="thesis-badge">THESIS</span>}
            </span>
            <span className="market-gap">Gap: {m.gap} edits</span>
          </div>
          <div className="market-text">{m.text}</div>

          {m.submissions.map((s) => (
            <BarRow key={s.name} {...s} />
          ))}

          <div className="market-lesson">{m.lesson}</div>
        </div>
      ))}
    </div>
  )
}
