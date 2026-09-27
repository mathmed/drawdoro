import { useEffect, useRef, useState } from 'react'
import type { Editor } from 'tldraw'

import { useAppStore } from '../../store/useAppStore'

function triggerDownload(url: string, filename: string): void {
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  anchor.click()
}

function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob)
  triggerDownload(url, filename)
  URL.revokeObjectURL(url)
}

async function exportImage(
  editor: Editor,
  format: 'png' | 'svg',
  diagramName: string,
): Promise<void> {
  const shapeIds = [...editor.getCurrentPageShapeIds()]
  if (shapeIds.length === 0) {
    return
  }
  const { blob } = await editor.toImage(shapeIds, {
    format,
    background: true,
    pixelRatio: 2,
  })
  downloadBlob(blob, `${diagramName}.${format}`)
}

export default function ExportMenu() {
  const editor = useAppStore((state) => state.editor)
  const activeDiagram = useAppStore((state) => state.activeDiagram)
  const [isOpen, setIsOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!isOpen) {
      return
    }
    function handleClickOutside(event: MouseEvent): void {
      if (containerRef.current !== null && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [isOpen])

  const diagramName = activeDiagram?.name ?? 'diagram'

  function handleExportPng(): void {
    setIsOpen(false)
    if (editor !== null) {
      void exportImage(editor, 'png', diagramName)
    }
  }

  function handleExportSvg(): void {
    setIsOpen(false)
    if (editor !== null) {
      void exportImage(editor, 'svg', diagramName)
    }
  }

  function handleExportMermaid(): void {
    setIsOpen(false)
    const source = activeDiagram?.mermaid_source ?? ''
    const blob = new Blob([source], { type: 'text/plain;charset=utf-8' })
    downloadBlob(blob, `${diagramName}.mmd`)
  }

  function handleExportJson(): void {
    setIsOpen(false)
    const state = activeDiagram?.canvas_state ?? {}
    const blob = new Blob([JSON.stringify(state, null, 2)], {
      type: 'application/json;charset=utf-8',
    })
    downloadBlob(blob, `${diagramName}.json`)
  }

  const options: { label: string; onClick: () => void }[] = [
    { label: 'PNG', onClick: handleExportPng },
    { label: 'SVG', onClick: handleExportSvg },
    { label: 'Mermaid (.mmd)', onClick: handleExportMermaid },
    { label: 'JSON (.json)', onClick: handleExportJson },
  ]

  return (
    <div ref={containerRef} style={{ position: 'relative' }}>
      <button
        type="button"
        onClick={() => setIsOpen((open) => !open)}
        style={{
          background: isOpen ? '#2f81f7' : '#21262d',
          color: '#e6edf3',
          border: '1px solid #30363d',
          borderRadius: 6,
          padding: '5px 10px',
          fontSize: 13,
          cursor: 'pointer',
        }}
      >
        ⬇️ Export ▼
      </button>
      {isOpen ? (
        <div
          style={{
            position: 'absolute',
            top: 'calc(100% + 4px)',
            right: 0,
            minWidth: 160,
            background: '#161b22',
            border: '1px solid #30363d',
            borderRadius: 8,
            boxShadow: '0 4px 16px rgba(0,0,0,0.5)',
            padding: 4,
            display: 'flex',
            flexDirection: 'column',
            gap: 2,
          }}
        >
          {options.map((option) => (
            <button
              key={option.label}
              type="button"
              onClick={option.onClick}
              style={{
                background: 'transparent',
                color: '#e6edf3',
                border: 'none',
                borderRadius: 6,
                padding: '7px 10px',
                fontSize: 13,
                textAlign: 'left',
                cursor: 'pointer',
              }}
              onMouseEnter={(event) => {
                event.currentTarget.style.background = '#21262d'
              }}
              onMouseLeave={(event) => {
                event.currentTarget.style.background = 'transparent'
              }}
            >
              {option.label}
            </button>
          ))}
        </div>
      ) : null}
    </div>
  )
}
