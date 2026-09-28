import { create } from 'zustand'

export type ToastKind = 'success' | 'error' | 'info'

export interface Toast {
  id: number
  kind: ToastKind
  message: string
}

interface ToastState {
  toasts: Toast[]
  dismiss: (id: number) => void
}

let nextId = 1

export const useToastStore = create<ToastState>((set, get) => ({
  toasts: [],
  dismiss: (id) => set({ toasts: get().toasts.filter((toast) => toast.id !== id) }),
}))

export function toast(message: string, kind: ToastKind = 'info'): void {
  const id = nextId++
  useToastStore.setState((state) => ({ toasts: [...state.toasts.slice(-3), { id, kind, message }] }))
  setTimeout(() => useToastStore.getState().dismiss(id), kind === 'error' ? 6000 : 3500)
}
