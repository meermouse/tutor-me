export default function SavedLessonsList({ lessons, onLoad, onDelete }) {
  if (lessons.length === 0) return null

  return (
    <div className="saved-lessons">
      <h2>Saved Lessons</h2>
      <ul>
        {lessons.map(lesson => (
          <li key={lesson.id}>
            <div>
              <strong>{lesson.title}</strong>
              <div className="lesson-meta">
                {new Date(lesson.createdAt).toLocaleDateString()}
              </div>
            </div>
            <div className="actions" style={{ marginTop: 0 }}>
              <button className="secondary" onClick={() => onLoad(lesson)}>
                Load
              </button>
              <button className="danger" onClick={() => onDelete(lesson.id)}>
                Delete
              </button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}
