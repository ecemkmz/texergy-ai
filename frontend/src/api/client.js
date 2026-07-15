const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export async function checkHealth() {
  try {
    const res = await fetch(`${API_URL}/health`)
    if (!res.ok) return false
    return true
  } catch {
    return false
  }
}

export async function uploadFile(file) {
  const formData = new FormData()
  formData.append('file', file)

  const res = await fetch(`${API_URL}/upload`, {
    method: 'POST',
    body: formData,
  })

  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(text || `Yükleme başarısız (HTTP ${res.status})`)
  }
  return res.json()
}

export async function analyzeAnomaly(info) {
  const res = await fetch(`${API_URL}/analyze_anomaly`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(info)
  });
  if (!res.ok) {
    throw new Error('Yapay Zeka API hatası');
  }
  return res.json();
}