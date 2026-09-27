import mermaid from 'mermaid'
import { useEffect, useRef, useState } from 'react'

import { useDebounce } from '../../hooks/useDebounce'
import { useAppStore } from '../../store/useAppStore'

mermaid.initialize({ startOnLoad: false, theme: 'dark', securityLevel: 'loose' })

function MermaidPreview({ source }: { source: string }) {
  const [svg, setSvg] = useState('')
  const [error, setError] = useState<string | null>(null)
  const renderId = useRef(0)

  useEffect(() => {
    const trimmed = source.trim()
    if (trimmed === '') {
      setSvg('')
      setError(null)
      return
    }

    renderId.current += 1
    const currentId = renderId.current
    const elementId = `mermaid-preview-${currentId}`

    mermaid
      .render(elementId, trimmed)
      .then(({ svg: rendered }) => {
        // Ignore stale renders when the source changed while rendering.
        if (currentId === renderId.current) {
          setSvg(rendered)
          setError(null)
        }
      })
      .catch((cause: unknown) => {
        if (currentId === renderId.current) {
          setSvg('')
          setError(cause instanceof Error ? cause.message : 'Invalid Mermaid syntax')
        }
      })
  }, [source])

  if (error !== null) {
    return (
      <div style={{ color: '#f85149', fontSize: 12, whiteSpace: 'pre-wrap' }}>{error}</div>
    )
  }

  if (svg === '') {
    return <div style={{ color: '#8b949e', fontSize: 12 }}>Nothing to preview yet.</div>
  }

  return <div dangerouslySetInnerHTML={{ __html: svg }} />
}

export default function CodePanel() {
  const activeDiagram = useAppStore((state) => state.activeDiagram)
  const codeLanguage = useAppStore((state) => state.codeLanguage)
  const setCodeLanguage = useAppStore((state) => state.setCodeLanguage)
  const toggleCodePanel = useAppStore((state) => state.toggleCodePanel)
  const saveMermaidSource = useAppStore((state) => state.saveMermaidSource)
  const saveD2Source = useAppStore((state) => state.saveD2Source)

  const stored =
    (codeLanguage === 'mermaid' ? activeDiagram?.mermaid_source : activeDiagram?.d2_source) ?? ''

  const [code, setCode] = useState(stored)
  const debounced = useDebounce(code, 1500)
  const lastSaved = useRef(stored)

  // Reset the editor when switching diagrams or toggling the language tab.
  useEffect(() => {
    setCode(stored)
    lastSaved.current = stored
  }, [stored, activeDiagram?.id, codeLanguage])

  useEffect(() => {
    if (debounced === lastSaved.current) {
      return
    }
    lastSaved.current = debounced
    if (codeLanguage === 'mermaid') {
      void saveMermaidSource(debounced)
    } else {
      void saveD2Source(debounced)
    }
  }, [debounced, codeLanguage, saveMermaidSource, saveD2Source])

  return (
    <div
      style={{
        position: 'absolute',
        left: 0,
        right: 0,
        bottom: 0,
        height: 280,
        zIndex: 250,
        display: 'flex',
        flexDirection: 'column',
        background: '#161b22',
        borderTop: '1px solid #30363d',
        boxShadow: '0 -2px 12px rgba(0,0,0,0.4)',
      }}
    >
      <header
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '8px 12px',
          borderBottom: '1px solid #30363d',
        }}
      >
        <div style={{ display: 'flex', gap: 6 }}>
          {(['mermaid', 'd2'] as const).map((lang) => (
            <button
              key={lang}
              type="button"
              onClick={() => setCodeLanguage(lang)}
              style={{
                background: codeLanguage === lang ? '#2f81f7' : '#21262d',
                color: '#e6edf3',
                border: '1px solid #30363d',
                borderRadius: 6,
                padding: '4px 10px',
                fontSize: 12,
                cursor: 'pointer',
                textTransform: 'capitalize',
              }}
            >
              {lang}
            </button>
          ))}
        </div>
        <button
          type="button"
          onClick={toggleCodePanel}
          style={{
            background: 'transparent',
            color: '#8b949e',
            border: 'none',
            cursor: 'pointer',
            fontSize: 14,
          }}
        >
          ✕
        </button>
      </header>
      <div style={{ flex: 1, display: 'flex', minHeight: 0 }}>
        <textarea
          value={code}
          onChange={(event) => setCode(event.target.value)}
          spellCheck={false}
          placeholder={
            codeLanguage === 'mermaid' ? 'graph TB\n  A-->B' : 'a -> b: request'
          }
          style={{
            flex: 1,
            resize: 'none',
            background: '#0f1117',
            color: '#e6edf3',
            border: 'none',
            borderRight: '1px solid #30363d',
            outline: 'none',
            padding: 12,
            fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace',
            fontSize: 13,
            lineHeight: 1.5,
          }}
        />
        <div
          style={{
            flex: 1,
            overflow: 'auto',
            padding: 12,
            display: 'flex',
            alignItems: 'flex-start',
            justifyContent: 'center',
          }}
        >
          {codeLanguage === 'mermaid' ? (
            <MermaidPreview source={code} />
          ) : (
            <div style={{ color: '#8b949e', fontSize: 12, textAlign: 'center' }}>
              D2 rendering coming soon
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
