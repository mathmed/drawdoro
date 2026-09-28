import { useState, type FormEvent } from 'react'

import { useDialogStore, type ConfirmOptions, type PromptOptions } from '../../store/useDialogStore'
import Modal from './Modal'

function PromptDialog({ options, onResolve }: { options: PromptOptions; onResolve: (value: string | null) => void }) {
  const [value, setValue] = useState(options.initialValue ?? '')

  function handleSubmit(event: FormEvent): void {
    event.preventDefault()
    const trimmed = value.trim()
    if (trimmed !== '') {
      onResolve(trimmed)
    }
  }

  return (
    <Modal
      title={options.title}
      description={options.description}
      onClose={() => onResolve(null)}
      footer={
        <>
          <button type="button" className="btn btn-secondary" onClick={() => onResolve(null)}>
            Cancel
          </button>
          <button type="submit" form="prompt-dialog-form" className="btn btn-primary" disabled={value.trim() === ''}>
            {options.confirmLabel ?? 'Create'}
          </button>
        </>
      }
    >
      <form id="prompt-dialog-form" onSubmit={handleSubmit} className="field">
        {options.label !== undefined ? <label className="field-label">{options.label}</label> : null}
        <input
          className="input"
          autoFocus
          value={value}
          placeholder={options.placeholder}
          onChange={(event) => setValue(event.target.value)}
          onFocus={(event) => event.currentTarget.select()}
        />
      </form>
    </Modal>
  )
}

function ConfirmDialog({ options, onResolve }: { options: ConfirmOptions; onResolve: (value: boolean) => void }) {
  return (
    <Modal
      title={options.title}
      onClose={() => onResolve(false)}
      footer={
        <>
          <button type="button" className="btn btn-secondary" onClick={() => onResolve(false)}>
            Cancel
          </button>
          <button
            type="button"
            autoFocus
            className={options.danger === true ? 'btn btn-danger' : 'btn btn-primary'}
            onClick={() => onResolve(true)}
          >
            {options.confirmLabel ?? 'Confirm'}
          </button>
        </>
      }
    >
      {options.description !== undefined ? (
        <p style={{ fontSize: 13.5, color: 'var(--text-muted)' }}>{options.description}</p>
      ) : null}
    </Modal>
  )
}

export default function DialogHost() {
  const request = useDialogStore((state) => state.request)

  if (request === null) {
    return null
  }
  if (request.kind === 'prompt') {
    return <PromptDialog options={request.options} onResolve={request.resolve} />
  }
  return <ConfirmDialog options={request.options} onResolve={request.resolve} />
}
