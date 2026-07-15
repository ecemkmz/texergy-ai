import { useState } from 'react'
import { analyzeAnomaly } from '../api/client.js'

function Gauge({ score, severity }) {
  const radius = 26
  const circumference = Math.PI * radius
  const filled = (score / 100) * circumference

  return (
    <svg className={`gauge gauge--${severity}`} width="64" height="40" viewBox="0 0 64 40">
      <path
        d="M 6 34 A 26 26 0 0 1 58 34"
        fill="none"
        stroke="var(--border)"
        strokeWidth="6"
        strokeLinecap="round"
      />
      <path
        className="gauge__fill"
        d="M 6 34 A 26 26 0 0 1 58 34"
        fill="none"
        strokeWidth="6"
        strokeLinecap="round"
        strokeDasharray={`${filled} ${circumference}`}
      />
      <text x="32" y="30" textAnchor="middle">
        {score}
      </text>
    </svg>
  )
}

export default function RiskCard({ category, title, score, severity, description, action, raw }) {
  const [aiAction, setAiAction] = useState(action)
  const [loading, setLoading] = useState(false)

  const handleAskAi = async () => {
    if (!raw) return
    setLoading(true)
    try {
      const res = await analyzeAnomaly({
        facility_type: raw.facility_type,
        machine_speed: raw.machine_speed,
        defect_rate: raw.defect_rate,
        quality_score: raw.quality_score,
        energy_waste_flag: raw.energy_waste_flag
      })
      setAiAction(res.suggestion)
    } catch (e) {
      setAiAction('Yapay zeka ile iletişim kurulamadı.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <article className={`risk-card risk-card--${severity}`}>
      <div className="risk-card__top">
        <div>
          <p className="risk-card__category">{category}</p>
          <h3 className="risk-card__title">{title}</h3>
        </div>
        <Gauge score={score} severity={severity} />
      </div>

      <p className="risk-card__desc">{description}</p>

      <div className="risk-card__action">
        <strong>Önerilen aksiyon</strong>
        {aiAction ? (
          <p style={{ marginTop: '0.5rem', fontWeight: 500 }}>{aiAction}</p>
        ) : raw ? (
          <button className="btn btn-primary" onClick={handleAskAi} disabled={loading} style={{ marginTop: '0.5rem' }}>
            {loading ? 'Soruluyor...' : 'Yapay Zeka Yorumu Al ✨'}
          </button>
        ) : (
          <p>{action}</p>
        )}
      </div>
    </article>
  )
}