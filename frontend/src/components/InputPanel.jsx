import { useState } from 'react'
import { generateScript } from '../api.js'

export default function InputPanel({ onScriptGenerated }) {
  const [title, setTitle] = useState('')
  const [topic, setTopic] = useState('')
  const [wordListRaw, setWordListRaw] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleGenerate() {
    if (!title.trim() || !topic.trim() || !wordListRaw.trim()) return
    const wordList = wordListRaw.split('\n').map(w => w.trim()).filter(Boolean)
    setLoading(true)
    setError(null)
    try {
      const { script } = await generateScript(title.trim(), topic.trim(), wordList)
      onScriptGenerated({ title: title.trim(), topic: topic.trim(), wordList, script })
    } catch (err) {
      setError(err?.message ?? 'An unexpected error occurred.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="panel">
      <h2>New Lesson</h2>

      <div className="field">
        <label htmlFor="title">Lesson title</label>
        <input
          id="title"
          type="text"
          placeholder="e.g. Directions — Train Station"
          value={title}
          onChange={e => setTitle(e.target.value)}
        />
      </div>

      <div className="field">
        <label htmlFor="topic">Topic (sent to Claude)</label>
        <input
          id="topic"
          type="text"
          placeholder="e.g. asking for directions at a train station"
          value={topic}
          onChange={e => setTopic(e.target.value)}
        />
      </div>

      <div className="field">
        <label htmlFor="words">Words and phrases (one per line)</label>
        <textarea
          id="words"
          placeholder={"左 (zuǒ) — left\n右 (yòu) — right\n直走 — go straight"}
          value={wordListRaw}
          onChange={e => setWordListRaw(e.target.value)}
          rows={6}
        />
      </div>

      {error && <p style={{ color: '#dc2626', fontSize: '0.875rem' }}>{error}</p>}

      <div className="actions">
        <button onClick={handleGenerate} disabled={loading || !title.trim() || !topic.trim() || !wordListRaw.trim()}>
          {loading && <span className="spinner" />}
          {loading ? 'Generating…' : 'Generate Script'}
        </button>
      </div>
    </div>
  )
}
