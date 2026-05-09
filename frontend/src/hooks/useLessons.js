import { useState, useEffect } from 'react'

const STORAGE_KEY = 'tutor-me-lessons'

function loadFromStorage() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

function saveToStorage(lessons) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(lessons))
}

export function useLessons() {
  const [lessons, setLessons] = useState(loadFromStorage)

  useEffect(() => {
    saveToStorage(lessons)
  }, [lessons])

  function saveLesson(lesson) {
    setLessons(prev => {
      const exists = prev.findIndex(l => l.id === lesson.id)
      if (exists >= 0) {
        const updated = [...prev]
        updated[exists] = lesson
        return updated
      }
      return [lesson, ...prev]
    })
  }

  function deleteLesson(id) {
    setLessons(prev => prev.filter(l => l.id !== id))
  }

  return { lessons, saveLesson, deleteLesson }
}
