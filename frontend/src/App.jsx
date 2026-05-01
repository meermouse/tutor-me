import { useState } from 'react'

export default function App() {
  const [panel, setPanel] = useState('input') // 'input' | 'editor' | 'player'
  const [currentLesson, setCurrentLesson] = useState(null)
  const [audioUrl, setAudioUrl] = useState(null)

  return (
    <div className="app">
      <h1>Tutor Me</h1>
      <p>Panel: {panel}</p>
    </div>
  )
}
