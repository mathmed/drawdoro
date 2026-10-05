import { useEffect } from 'react'

import { authConfig } from '../auth/config'
import { getIdToken } from '../auth/session'
import { useWorkspacePresenceStore } from '../store/useWorkspacePresenceStore'
import { parseWorkspacePresenceMessage } from '../utils/workspacePresence'

const RECONNECT_DELAY_MS = 2000
// Refused (signed out, no longer a member, too many tabs): try again much later, not in a loop.
const REFUSED_RETRY_MS = 30_000
const POLICY_VIOLATION = 1008

// One socket per open sidebar tells it who is in every diagram of the workspace, instead of one
// socket per diagram. Closed and forgotten when the workspace changes or the sidebar goes away.
export function useWorkspacePresence(workspaceId: string | null): void {
  useEffect(() => {
    if (workspaceId === null) {
      return undefined
    }
    const { applySnapshot, applyDelta, reset } = useWorkspacePresenceStore.getState()
    let socket: WebSocket | null = null
    let retry: ReturnType<typeof setTimeout> | null = null
    let stopped = false

    async function connect(): Promise<void> {
      // Browsers can't send headers on a WebSocket handshake, so the ID token goes in the URL.
      const token = authConfig.enabled ? await getIdToken() : null
      if (stopped) {
        return
      }
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const query = token === null ? '' : `?${new URLSearchParams({ token }).toString()}`
      const ws = new WebSocket(`${protocol}//${window.location.host}/api/ws/workspaces/${workspaceId}/presence${query}`)

      ws.onmessage = (event: MessageEvent<string>) => {
        let raw: unknown
        try {
          raw = JSON.parse(event.data)
        } catch {
          return
        }
        const message = parseWorkspacePresenceMessage(raw)
        if (message?.type === 'presence_snapshot') {
          applySnapshot(message.you, message.diagrams)
        } else if (message?.type === 'presence_delta') {
          applyDelta(message.diagrams)
        }
      }

      ws.onclose = (event: CloseEvent) => {
        if (stopped) {
          return
        }
        // Without the socket nobody's comings and goings arrive: show nobody rather than stale faces.
        reset()
        const delay = event.code === POLICY_VIOLATION ? REFUSED_RETRY_MS : RECONNECT_DELAY_MS
        retry = setTimeout(() => void connect(), delay)
      }

      socket = ws
    }

    void connect()
    return () => {
      stopped = true
      if (retry !== null) {
        clearTimeout(retry)
      }
      socket?.close()
      reset()
    }
  }, [workspaceId])
}
