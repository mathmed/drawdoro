import { ChevronLeft, ChevronRight, X } from 'lucide-react'
import { useEffect } from 'react'

import { usePresentation } from '../../hooks/usePresentation'
import { useAppStore } from '../../store/useAppStore'

export default function PresentationMode() {
  const editor = useAppStore((state) => state.editor)
  const isPresentationMode = useAppStore((state) => state.isPresentationMode)
  const exitPresentation = useAppStore((state) => state.exitPresentation)

  const { frameCount, currentIndex, goToNext, goToPrevious } = usePresentation(editor, isPresentationMode)

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent): void {
      if (event.key === 'ArrowRight' || event.key === ' ') {
        event.preventDefault()
        goToNext()
      } else if (event.key === 'ArrowLeft') {
        event.preventDefault()
        goToPrevious()
      } else if (event.key === 'Escape') {
        exitPresentation()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [goToNext, goToPrevious, exitPresentation])

  // Leaving fullscreen through the browser (F11 / Esc) must also exit the mode.
  useEffect(() => {
    function handleFullscreenChange(): void {
      if (document.fullscreenElement === null) {
        exitPresentation()
      }
    }
    document.addEventListener('fullscreenchange', handleFullscreenChange)
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange)
  }, [exitPresentation])

  return (
    <div className="presentation-bar">
      <button
        type="button"
        className="btn btn-ghost btn-icon"
        aria-label="Previous frame"
        onClick={goToPrevious}
        disabled={frameCount === 0 || currentIndex === 0}
      >
        <ChevronLeft size={18} />
      </button>
      <span className="presentation-counter">
        {frameCount === 0 ? 'No frames — add frames to create slides' : `${currentIndex + 1} / ${frameCount}`}
      </span>
      <button
        type="button"
        className="btn btn-ghost btn-icon"
        aria-label="Next frame"
        onClick={goToNext}
        disabled={frameCount === 0 || currentIndex === frameCount - 1}
      >
        <ChevronRight size={18} />
      </button>
      <span className="topbar-divider" style={{ margin: '0 2px' }} />
      <button type="button" className="btn btn-ghost" onClick={exitPresentation}>
        <X size={16} /> Exit
      </button>
    </div>
  )
}
