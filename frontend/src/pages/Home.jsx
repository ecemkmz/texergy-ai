import { useEffect, useState } from 'react'
import UploadPanel from '../components/UploadPanel.jsx'
import Dashboard from '../components/Dashboard.jsx'
import { checkHealth } from '../api/client.js'

export default function Home() {
  const [backendUp, setBackendUp] = useState(null)

  useEffect(() => {
    checkHealth().then(setBackendUp)
  }, [])
  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <h1 className="app-header__title">
            Texergy<span>AI</span>
          </h1>
          <p className="app-header__subtitle">Enerji ve üretim riski karar destek paneli</p>
        </div>
        <div className="app-header__status">
          <span className={`status-dot ${backendUp ? 'live' : 'mock'}`} />
          {backendUp === null
            ? 'Backend kontrol ediliyor…'
            : backendUp
            ? 'Backend bağlı'
            : 'Backend bulunamadı — mock veri gösteriliyor'}
        </div>
      </header>
      <UploadPanel />
      <Dashboard />
    </div>
  )
}