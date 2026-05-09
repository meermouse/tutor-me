export default function AudioPlayer({ audioUrl, lessonTitle, onStartOver }) {
  function handleDownload() {
    const a = document.createElement('a')
    a.href = audioUrl
    a.download = `${lessonTitle.replace(/\s+/g, '-').toLowerCase()}.mp3`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
  }

  return (
    <div className="panel">
      <h2>Your Lesson is Ready</h2>
      <audio src={audioUrl} controls />
      <div className="actions">
        <button onClick={handleDownload}>Download MP3</button>
        <button className="secondary" onClick={onStartOver}>Start Over</button>
      </div>
    </div>
  )
}
