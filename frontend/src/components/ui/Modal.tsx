import { X } from 'lucide-react'
import { useEffect, type ReactNode } from 'react'
import { createPortal } from 'react-dom'

interface ModalProps {
  title: string
  description?: string
  size?: 'md' | 'lg'
  onClose: () => void
  footer?: ReactNode
  children: ReactNode
}

export default function Modal({ title, description, size = 'md', onClose, footer, children }: ModalProps) {
  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent): void {
      if (event.key === 'Escape') {
        event.stopPropagation()
        onClose()
      }
    }
    window.addEventListener('keydown', handleKeyDown, true)
    return () => window.removeEventListener('keydown', handleKeyDown, true)
  }, [onClose])

  return createPortal(
    <div className="modal-overlay" onMouseDown={onClose}>
      <div
        className={size === 'lg' ? 'modal modal-lg' : 'modal'}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="modal-header">
          <div>
            <h2 className="modal-title">{title}</h2>
            {description !== undefined ? <p className="modal-description">{description}</p> : null}
          </div>
          <button type="button" className="btn btn-ghost btn-icon btn-sm" aria-label="Close" onClick={onClose}>
            <X size={16} />
          </button>
        </div>
        <div className="modal-body scroll">{children}</div>
        {footer !== undefined ? <div className="modal-footer">{footer}</div> : null}
      </div>
    </div>,
    document.body,
  )
}
