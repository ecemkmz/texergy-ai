import { useState } from 'react'
import RiskCard from './RiskCard.jsx'
import { mockRisks, categories } from '../mock/riskData.js'

export default function Dashboard({ anomalies }) {
  const [activeCategory, setCategory] = useState('Tümü')

  let risks = mockRisks;
  let isMock = true;

  if (anomalies) {
    isMock = false;
    risks = anomalies.map((a, idx) => {
      let severity = 'low'
      if (a.defect_rate > 2.0 && a.energy_waste_flag === 1) severity = 'high'
      else if (a.defect_rate > 1.0 || a.energy_waste_flag === 1) severity = 'medium'
      
      let category = 'Üretim'
      if (a.facility_type === 'Dyeing' || a.facility_type === 'Finishing') category = 'Kalite'
      else if (a.energy_waste_flag === 1) category = 'Enerji'
      
      return {
          id: `real_${idx}`,
          category: category,
          title: `${a.facility_type || 'Tesis'} Hattı Anomaly`,
          score: Math.round(100 - (a.quality_score || 0)),
          severity: severity,
          description: `Makine Hızı: ${Math.round(a.machine_speed || 0)}, Hata Oranı: %${(a.defect_rate || 0).toFixed(2)}, Enerji İsrafı: ${a.energy_waste_flag === 1 ? 'Evet' : 'Hayır'}`,
          action: null,
          raw: a
      }
    })
  }

  const filtered = activeCategory === 'Tümü' ? risks : risks.filter((r) => r.category === activeCategory)
  const sorted = [...filtered].sort((a, b) => b.score - a.score)

  return (
    <section className="section">
      <p className="section__eyebrow">Risk Panosu {isMock ? '· Mock Veri' : '· Gerçek Veri'}</p>
      <h2 className="section__title">Öncelikli Riskler</h2>

      <div className="filter-row">
        {categories.map((cat) => (
          <button
            key={cat}
            className={`filter-chip ${activeCategory === cat ? 'active' : ''}`}
            onClick={() => setCategory(cat)}
          >
            {cat}
          </button>
        ))}
      </div>
      {sorted.length === 0 ? (
        <div className="empty-state">Bu kategoride risk bulunamadı. (Anomali yok)</div>
      ) : (
        <div className="risk-grid">
          {sorted.map((risk) => (
            <RiskCard key={risk.id} {...risk} />
          ))}
        </div>
      )}
    </section>
  )
}