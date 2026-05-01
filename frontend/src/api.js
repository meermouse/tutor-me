const API_BASE = 'http://localhost:8000'

export async function generateScript(title, topic, wordList) {
  const response = await fetch(`${API_BASE}/generate-script`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, topic, word_list: wordList }),
  })
  if (!response.ok) {
    const detail = await response.text()
    throw new Error(`Script generation failed: ${detail}`)
  }
  return response.json() // { script: string }
}

export async function generateAudio(script) {
  const response = await fetch(`${API_BASE}/generate-audio`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ script }),
  })
  if (!response.ok) {
    const detail = await response.text()
    throw new Error(`Audio generation failed: ${detail}`)
  }
  return response.blob() // MP3 blob
}
