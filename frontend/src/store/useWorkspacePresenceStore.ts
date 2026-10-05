import { create } from 'zustand'

import type { PresenceUser } from '../hooks/useRealtime'
import {
  applyPresence,
  EMPTY_PRESENCE_INDEX,
  type DiagramPresenceUpdate,
  type PresenceIndex,
} from '../utils/workspacePresence'

interface WorkspacePresenceState extends PresenceIndex {
  // Which presence entry is this person; null until the server says so, or with login disabled.
  you: string | null
  applySnapshot: (you: string | null, diagrams: DiagramPresenceUpdate[]) => void
  applyDelta: (diagrams: DiagramPresenceUpdate[]) => void
  reset: () => void
}

const NOBODY: PresenceUser[] = []

// Who is in each diagram of the active workspace, for the sidebar. Kept apart from the app store so
// presence changes never wake the rest of the app.
export const useWorkspacePresenceStore = create<WorkspacePresenceState>((set, get) => ({
  ...EMPTY_PRESENCE_INDEX,
  you: null,

  applySnapshot: (you, diagrams) => set({ you, ...applyPresence(get(), diagrams, true) }),

  applyDelta: (diagrams) => set(applyPresence(get(), diagrams, false)),

  reset: () => set({ ...EMPTY_PRESENCE_INDEX, you: null }),
}))

// Granular selectors: a row re-renders only when the people of its own diagram or project change.
export function useDiagramPresence(diagramId: string): PresenceUser[] {
  return useWorkspacePresenceStore((state) => state.byDiagram[diagramId]?.users ?? NOBODY)
}

export function useProjectPresence(projectId: string): PresenceUser[] {
  return useWorkspacePresenceStore((state) => state.byProject[projectId] ?? NOBODY)
}
