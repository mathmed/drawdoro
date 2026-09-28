import { create } from 'zustand'

export interface PromptOptions {
  title: string
  description?: string
  label?: string
  placeholder?: string
  initialValue?: string
  confirmLabel?: string
}

export interface ConfirmOptions {
  title: string
  description?: string
  confirmLabel?: string
  danger?: boolean
}

export type DialogRequest =
  | { kind: 'prompt'; options: PromptOptions; resolve: (value: string | null) => void }
  | { kind: 'confirm'; options: ConfirmOptions; resolve: (value: boolean) => void }

interface DialogState {
  request: DialogRequest | null
}

export const useDialogStore = create<DialogState>(() => ({ request: null }))

// Promise-based replacements for window.prompt / window.confirm rendered by <DialogHost />.
export function promptDialog(options: PromptOptions): Promise<string | null> {
  return new Promise((resolve) => {
    useDialogStore.setState({
      request: {
        kind: 'prompt',
        options,
        resolve: (value) => {
          useDialogStore.setState({ request: null })
          resolve(value)
        },
      },
    })
  })
}

export function confirmDialog(options: ConfirmOptions): Promise<boolean> {
  return new Promise((resolve) => {
    useDialogStore.setState({
      request: {
        kind: 'confirm',
        options,
        resolve: (value) => {
          useDialogStore.setState({ request: null })
          resolve(value)
        },
      },
    })
  })
}
