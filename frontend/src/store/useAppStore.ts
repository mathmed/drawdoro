import { create } from 'zustand'

interface AppState {
  activeDiagramId: string | null
  setActiveDiagramId: (id: string | null) => void
}

export const useAppStore = create<AppState>((set) => ({
  activeDiagramId: null,
  setActiveDiagramId: (id) => set({ activeDiagramId: id }),
}))
