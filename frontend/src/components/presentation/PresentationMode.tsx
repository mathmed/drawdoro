import { useEffect } from 'react'

import { usePresentation } from '../../hooks/usePresentation'
import { useAppStore } from '../../store/useAppStore'

export default function PresentationMode() {
  const editor = useAppStore((state) => state.editor)
  const isPresentationMode = useAppStore((state) => state.isPresentationMode)
  const exitPresentation = useAppStore((state) => state.exitPresentation)

  const { frameCount, currentIndex, goToNext, goToPrevious } = usePresentation(
    editor,
    isPresentationMode,
  )

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

  const buttonStyle: React.CSSProperties = {
    background: '#21262d',
    color: '#e6edf3',
    border: '1px solid #30363d',
    borderRadius: 6,
    padding: '6px 12px',
    fontSize: 13,
    cursor: 'pointer',
  }

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        pointerEvents: 'none',
        zIndex: 1000,
      }}
    >
      <div
        style={{
          position: 'absolute',
          bottom: 20,
          left: '50%',
          transform: 'translateX(-50%)',
          pointerEvents: 'auto',
          display: 'flex',
          alignItems: 'center',
          gap: 10,
          background: 'rgba(22, 27, 34, 0.92)',
          border: '1px solid #30363d',
          borderRadius: 10,
          padding: '8px 12px',
          boxShadow: '0 4px 16px rgba(0,0,0,0.5)',
        }}
      >
        <button type="button" onClick={goToPrevious} style={buttonStyle}>
          ← Anterior
        </button>
        <span style={{ fontSize: 13, color: '#8b949e', minWidth: 90, textAlign: 'center' }}>
          {frameCount === 0 ? 'no frames' : `frame ${currentIndex + 1} / ${frameCount}`}
        </span>
        <button type="button" onClick={goToNext} style={buttonStyle}>
          Próximo →
        </button>
        <button
          type="button"
          onClick={exitPresentation}
          style={{ ...buttonStyle, color: '#f85149' }}
        >
          ✕ Sair
        </button>
      </div>
    </div>
  )
}
