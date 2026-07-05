import { useRef, useState } from 'react'
import { uploadFile } from '../api/client.js'

export default function UploadPanel() {
  const [file, setFile] = useState(null)
  const [dragging, setDragging] = useState(false)
  const [status, setStatus] = useState(null)
  const [busy, setBusy] = useState(false)
  const inputRef = useRef(null)

  function handleFiles(fileList) {
    const picked = fileList?.[0]
    if (!picked) return
    if (!picked.name.toLowerCase().endsWith('.csv')) {
      setStatus({ type: 'error', text: 'Sadece .csv dosyaları kabul ediliyor.' })
      return
    }
    setFile(picked)
    setStatus(null)
  }
  async function handleUpload() {
    if (!file) return
    setBusy(true)
    setStatus({ type: 'info', text: 'Yükleniyor...' })
    try {
      const result = await uploadFile(file)
      setStatus({
        type: 'ok',
        text: `Yüklendi: ${result?.filename ?? file.name} (${result?.row_count ?? '—'} satır)`,
      })
    } catch (err) {
      setStatus({
        type: 'error',
        text: `Backend'e ulaşılamadı: ${err.message}`,
      })
    } finally {
      setBusy(false)
    }
  }
  return (
    <section className="section">
      <p className="section__eyebrow">Adım 1</p>
      <h2 className="section__title">Veri Yükle</h2>

      <div className="upload-panel">
        <div
          className={`dropzone ${dragging ? 'dragging' : ''}`}
          onClick={() => inputRef.current?.click()}
          onDragOver={(e) => {
            e.preventDefault()
            setDragging(true)
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault()
            setDragging(false)
            handleFiles(e.dataTransfer.files)
          }}
        >
          {file ? (
            <span className="dropzone__filename">{file.name}</span>
          ) : (
            <span>Dosyayı buraya sürükleyin ya da seçmek için tıklayın</span>
          )}
          <p className="dropzone__hint">.csv · enerji / üretim / kalite / bakım verisi</p>
          <input
            ref={inputRef}
            type="file"
            accept=".csv"
            hidden
            onChange={(e) => handleFiles(e.target.files)}
          />
        </div>
        <div className="upload-panel__actions">
          <button className="btn btn-primary" disabled={!file || busy} onClick={handleUpload}>
            {busy ? 'Yükleniyor…' : 'Yükle'}
          </button>
          <button
            className="btn btn-ghost"
            disabled={!file || busy}
            onClick={() => {
              setFile(null)
              setStatus(null)
            }}
          >
            Temizle
          </button>
        </div>
        {status && <p className={`upload-message ${status.type}`}>{status.text}</p>}
      </div>
    </section>
  )
}