import { useState } from 'react'
import { useLessons } from './hooks/useLessons.js'
import SavedLessonsList from './components/SavedLessonsList.jsx'
import InputPanel from './components/InputPanel.jsx'
import ScriptEditor from './components/ScriptEditor.jsx'
import AudioPlayer from './components/AudioPlayer.jsx'

export default function App() {
  const [panel, setPanel] = useState('input') // 'input' | 'editor' | 'player'
  const [currentLesson, setCurrentLesson] = useState(null)
  const [audioUrl, setAudioUrl] = useState(null)
  const { lessons, saveLesson, deleteLesson } = useLessons()

  function handleScriptGenerated({ title, topic, wordList, script }) {
    const lesson = {
      id: crypto.randomUUID(),
      title,
      topic,
      wordList,
      script,
      createdAt: new Date().toISOString(),
    }
    setCurrentLesson(lesson)
    saveLesson(lesson)
    setPanel('editor')
  }

  function handleScriptChange(updatedScript) {
    if (!currentLesson) return
    const updated = { ...currentLesson, script: updatedScript }
    setCurrentLesson(updated)
    saveLesson(updated)
  }

  function handleAudioGenerated(url) {
    if (!url) return
    if (audioUrl) URL.revokeObjectURL(audioUrl)
    setAudioUrl(url)
    setPanel('player')
  }

  function handleLoadLesson(lesson) {
    if (audioUrl) URL.revokeObjectURL(audioUrl)
    setCurrentLesson(lesson)
    setAudioUrl(null)
    setPanel('editor')
  }

  function handleStartOver() {
    if (audioUrl) URL.revokeObjectURL(audioUrl)
    setAudioUrl(null)
    setCurrentLesson(null)
    setPanel('input')
  }

  return (
    <div className="app">
      <h1>Tutor Me</h1>

      <SavedLessonsList
        lessons={lessons}
        onLoad={handleLoadLesson}
        onDelete={deleteLesson}
      />

      {panel === 'input' && (
        <InputPanel onScriptGenerated={handleScriptGenerated} />
      )}

      {panel === 'editor' && currentLesson && (
        <ScriptEditor
          lesson={currentLesson}
          onScriptChange={handleScriptChange}
          onAudioGenerated={handleAudioGenerated}
        />
      )}

      {panel === 'player' && audioUrl && (
        <AudioPlayer
          audioUrl={audioUrl}
          lessonTitle={currentLesson.title}
          onStartOver={handleStartOver}
        />
      )}
    </div>
  )
}
