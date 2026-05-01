import { useState, useEffect } from 'react'
import { generateAudio } from '../api.js'

export default function ScriptEditor({ lesson, onScriptChange, onAudioGenerated }) {
  const [script, setScript] = useState(lesson.script)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    setScript(lesson.script)
  }, [lesson.id])

  function handleScriptChange(e) {
    const updated = e.target.value
    setScript(updated)
    onScriptChange(updated)
  }

  async function handleGenerateAudio() {
    setLoading(true)
    setError(null)
    try {
      const blob = await generateAudio(script)
      const url = URL.createObjectURL(blob)
      onAudioGenerated(url)
    } catch (err) {
      setError(err?.message ?? 'An unexpected error occurred.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="panel">
      <h2>{lesson.title}</h2>
      <p style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '0.75rem' }}>
        Review and edit the script below, then generate your audio lesson.
      </p>

      <div className="field">
        <textarea
          value={script}
          onChange={handleScriptChange}
          rows={20}
          style={{ fontFamily: 'monospace', fontSize: '0.875rem' }}
        />
      </div>

      {error && <p style={{ color: '#dc2626', fontSize: '0.875rem' }}>{error}</p>}

      <div className="actions">
        <button onClick={handleGenerateAudio} disabled={loading || !script.trim()}>
          {loading && <span className="spinner" />}
          {loading ? 'Generating audio…' : 'Generate Audio'}
        </button>
      </div>
    </div>
  )
}
