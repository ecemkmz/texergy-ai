import { useState } from 'react'
import RiskCard from './RiskCard.jsx'
import { mockRisks, categories } from '../mock/riskData.js'

export default function Dashboard() {
  const [activeCategory, setActiveCategory] = useState('Tümü')

  // Sprint 1: mock veri kullanılıyor. /analyze hazır olunca
  // burası gerçek veriye bağlanacak.
  const risks = mockRisks

  const filtered =
    activeCategory === 'Tümü' ? risks : risks.filter((r) => r.category === activeCategory)

  const sorted = [...filtered].sort((a, b) => b.score - a.score)

  return (
    <section className="section">
      <p className="section__eyebrow">Risk Panosu · Mock Veri</p>
      <h2 className="section__title">Öncelikli Riskler</h2>

      <div className="filter-row">
        {categories.map((cat) => (
          <button
            key={cat}
            className={`filter-chip ${activeCategory === cat ? 'active' : ''}`}
            onClick={() => setActiveCategory(cat)}
          >
            {cat}
          </button>
        ))}
      </div>
      {sorted.length === 0 ? (
        <div className="empty-state">Bu kategoride risk bulunamadı.</div>
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