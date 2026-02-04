/**
 * Phase 11: Analyst Notes Persistence
 * 
 * Non-destructive storage for analyst annotations.
 * Separate from immutable Phase 9 intelligence outputs.
 */

import { AnalystAnnotation, AnalystStore } from '../types/analyst'

const STORAGE_KEY = 'phase11_analyst_annotations'

export const useAnalystNotes = () => {
  const getAnnotation = (projectId: string): AnalystAnnotation | null => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (!stored) return null
      const store: AnalystStore = JSON.parse(stored)
      return store[projectId] || null
    } catch (e) {
      console.warn('Failed to read analyst notes from storage:', e)
      return null
    }
  }

  const saveAnnotation = (annotation: AnalystAnnotation): boolean => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY) || '{}'
      const store: AnalystStore = JSON.parse(stored)
      store[annotation.projectId] = {
        ...annotation,
        timestamp: new Date().toISOString()
      }
      localStorage.setItem(STORAGE_KEY, JSON.stringify(store))
      return true
    } catch (e) {
      console.error('Failed to save analyst notes:', e)
      return false
    }
  }

  const clearAnnotations = (): boolean => {
    try {
      localStorage.removeItem(STORAGE_KEY)
      return true
    } catch (e) {
      console.error('Failed to clear analyst notes:', e)
      return false
    }
  }

  return { getAnnotation, saveAnnotation, clearAnnotations }
}
