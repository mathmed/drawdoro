import { ChevronRight, CircleAlert, CircleCheck, TriangleAlert } from 'lucide-react'
import type { TLShapeId } from 'tldraw'

import type { ValidationResult } from '../../api/types'
import { useAppStore } from '../../store/useAppStore'
import Modal from '../ui/Modal'

interface ValidationModalProps {
  results: ValidationResult[]
  onClose: () => void
}

export default function ValidationModal({ results, onClose }: ValidationModalProps) {
  const errors = results.filter((result) => result.severity === 'error')
  const warnings = results.filter((result) => result.severity === 'warning')
  const editor = useAppStore((state) => state.editor)
  const openInspector = useAppStore((state) => state.openInspector)

  // Jump to the offending shapes and open Properties so the fix is one click away.
  function focus(result: ValidationResult): void {
    if (editor === null) {
      return
    }
    const ids = result.shapeIds.filter((id) => editor.getShape(id as TLShapeId) !== undefined) as TLShapeId[]
    if (ids.length === 0) {
      return
    }
    onClose()
    editor.setCurrentTool('select')
    editor.select(...ids)
    editor.zoomToSelection({ animation: { duration: 240 } })
    openInspector('properties')
  }

  return (
    <Modal
      title="Architecture validation"
      description="Click an issue to jump to the shape and fix it in Properties."
      onClose={onClose}
      footer={
        <button type="button" className="btn btn-primary" onClick={onClose}>
          Done
        </button>
      }
    >
      {results.length === 0 ? (
        <div className="validation-ok">
          <CircleCheck size={32} />
          <strong style={{ color: 'var(--text)' }}>No issues found</strong>
          The architecture looks consistent.
        </div>
      ) : (
        <>
          <div className="validation-summary">
            {errors.length > 0 ? (
              <span className="badge badge-danger">
                {errors.length} error{errors.length === 1 ? '' : 's'}
              </span>
            ) : null}
            {warnings.length > 0 ? (
              <span className="badge badge-warning">
                {warnings.length} warning{warnings.length === 1 ? '' : 's'}
              </span>
            ) : null}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {[...errors, ...warnings].map((result, index) => (
              <button
                key={`${result.severity}-${index}`}
                type="button"
                className="validation-item"
                data-severity={result.severity}
                onClick={() => focus(result)}
              >
                {result.severity === 'error' ? <CircleAlert size={16} /> : <TriangleAlert size={16} />}
                <span style={{ flex: 1 }}>{result.message}</span>
                <ChevronRight size={15} className="validation-go" />
              </button>
            ))}
          </div>
        </>
      )}
    </Modal>
  )
}
