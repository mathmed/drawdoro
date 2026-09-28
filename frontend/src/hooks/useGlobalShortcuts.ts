import { useEffect } from 'react'

import { useAppStore } from '../store/useAppStore'

function isEditable(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) {
    return false
  }
  return target.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName)
}

export function useGlobalShortcuts(): void {
  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent): void {
      if (!(event.metaKey || event.ctrlKey) || event.altKey) {
        return
      }
      const store = useAppStore.getState()
      if (store.isPresentationMode) {
        return
      }
      if (event.shiftKey) {
        // ⌘. alone is tldraw's focus mode, so the details panel lives on ⌘⇧. instead.
        if (event.code === 'Period' && store.activeDiagram !== null && !isEditable(event.target)) {
          event.preventDefault()
          store.toggleInspector()
        }
        return
      }
      const key = event.key.toLowerCase()

      if (key === 'k') {
        event.preventDefault()
        store.setCommandPaletteOpen(!store.isCommandPaletteOpen)
        return
      }
      if (isEditable(event.target)) {
        return
      }
      if (key === '\\') {
        event.preventDefault()
        store.toggleSidebar()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])
}
