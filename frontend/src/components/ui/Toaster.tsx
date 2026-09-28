import { CircleAlert, CircleCheck, Info, X } from 'lucide-react'
import { createPortal } from 'react-dom'

import { useToastStore, type ToastKind } from '../../store/useToastStore'

const ICONS: Record<ToastKind, typeof Info> = {
  success: CircleCheck,
  error: CircleAlert,
  info: Info,
}

export default function Toaster() {
  const toasts = useToastStore((state) => state.toasts)
  const dismiss = useToastStore((state) => state.dismiss)

  return createPortal(
    <div className="toaster" aria-live="polite">
      {toasts.map((item) => {
        const Icon = ICONS[item.kind]
        return (
          <div key={item.id} className="toast" data-kind={item.kind} role="status">
            <Icon size={16} className="toast-icon" />
            <span className="toast-message">{item.message}</span>
            <button type="button" className="btn btn-ghost btn-icon btn-xs" aria-label="Dismiss" onClick={() => dismiss(item.id)}>
              <X size={13} />
            </button>
          </div>
        )
      })}
    </div>,
    document.body,
  )
}
