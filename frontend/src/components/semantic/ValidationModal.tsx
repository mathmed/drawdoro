import type { ValidationResult } from '../../api/types'

interface ValidationModalProps {
  results: ValidationResult[]
  onClose: () => void
}

export default function ValidationModal({ results, onClose }: ValidationModalProps) {
  const errors = results.filter((result) => result.severity === 'error')
  const warnings = results.filter((result) => result.severity === 'warning')

  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0,0,0,0.6)',
        zIndex: 900,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <div
        onClick={(event) => event.stopPropagation()}
        style={{
          width: 480,
          maxWidth: '90vw',
          maxHeight: '80vh',
          overflow: 'auto',
          background: '#161b22',
          border: '1px solid #30363d',
          borderRadius: 12,
          boxShadow: '0 8px 32px rgba(0,0,0,0.6)',
          padding: 20,
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: 12,
          }}
        >
          <h2 style={{ fontSize: 16, margin: 0 }}>🔍 Architecture validation</h2>
          <button
            type="button"
            onClick={onClose}
            style={{
              background: 'transparent',
              color: '#8b949e',
              border: 'none',
              cursor: 'pointer',
              fontSize: 16,
            }}
          >
            ✕
          </button>
        </div>

        {results.length === 0 ? (
          <div style={{ color: '#2ea043', fontSize: 14 }}>
            ✅ No issues found. The architecture looks consistent.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            <div style={{ fontSize: 13, color: '#8b949e' }}>
              {errors.length} error(s), {warnings.length} warning(s)
            </div>
            {results.map((result, index) => (
              <div
                key={`${result.severity}-${index}`}
                style={{
                  background: '#0f1117',
                  border: `1px solid ${result.severity === 'error' ? '#f85149' : '#d29922'}`,
                  borderRadius: 8,
                  padding: 10,
                  fontSize: 13,
                  color: '#e6edf3',
                }}
              >
                {result.severity === 'error' ? '❌' : '⚠️'} {result.message}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
