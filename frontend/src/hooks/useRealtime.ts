import { useCallback, useEffect, useRef } from 'react'
import { loadSnapshot, type Editor, type TLStoreSnapshot } from 'tldraw'

import type { PushedDiagram } from '../api/types'
import { TAB_CLIENT_ID } from '../api/tabClientId'
import { authConfig } from '../auth/config'
import { getIdToken } from '../auth/session'

export interface PresenceUser {
  id: string
  name: string
  // Agents (the MCP server) have no socket; the server lists them while they are working.
  kind?: 'person' | 'agent'
}

export interface Presence {
  users: PresenceUser[]
  // Which entry is this browser tab; null until the server says so.
  you: string | null
}

interface RealtimeOptions {
  diagramId: string
  editor: Editor | null
  onPresenceChange: (presence: Presence) => void
  // Keeps the local copy of the diagram in sync; returns false when the push is stale.
  onDiagramPushed?: (diagram: PushedDiagram) => boolean
  // Guests reach a diagram through a share link instead of a signed-in session.
  shareToken?: string
  guestName?: string
}

interface RealtimeMessage {
  type: string
  users?: PresenceUser[]
  you?: string
  client_id?: string | null
  snapshot?: TLStoreSnapshot
  diagram?: PushedDiagram
}

const RECONNECT_DELAY_MS = 2000

export function useRealtime({
  diagramId,
  editor,
  onPresenceChange,
  onDiagramPushed,
  shareToken,
  guestName,
}: RealtimeOptions) {
  const wsRef = useRef<WebSocket | null>(null)
  const applyingRemote = useRef(false)
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  // Every (re)mount gets a new generation. Sockets and pending connects from an older one
  // are ignored, so a stale socket can never reconnect behind the current one and leave a
  // ghost session on the server.
  const generation = useRef(0)

  const connect = useCallback(
    async (connectionGeneration: number) => {
      // Browsers can't send headers on a WebSocket handshake, so the ID token goes in the URL.
      // Guests have no session; they authenticate the connection with their share token instead.
      const token = shareToken === undefined && authConfig.enabled ? await getIdToken() : null
      if (connectionGeneration !== generation.current) {
        return
      }
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const params = new URLSearchParams()
      if (shareToken !== undefined) {
        params.set('share', shareToken)
        if (guestName !== undefined && guestName !== '') {
          params.set('name', guestName)
        }
      } else if (token !== null) {
        params.set('token', token)
      }
      const query = params.toString() === '' ? '' : `?${params.toString()}`
      const ws = new WebSocket(`${protocol}//${window.location.host}/api/ws/diagrams/${diagramId}${query}`)

      function applyRemoteSnapshot(snapshot: TLStoreSnapshot) {
        if (editor === null) {
          return
        }
        const wasFocused = editor.getIsFocused()
        applyingRemote.current = true
        editor.store.mergeRemoteChanges(() => {
          loadSnapshot(editor.store, snapshot)
        })
        applyingRemote.current = false
        // A peer's edit must not steal keyboard focus from the local user.
        if (wasFocused && !editor.getIsFocused()) {
          editor.focus({ focusContainer: false })
        }
      }

      ws.onmessage = (event) => {
        const msg = JSON.parse(event.data) as RealtimeMessage

        if (msg.type === 'presence') {
          onPresenceChange({ users: msg.users ?? [], you: msg.you ?? null })
          return
        }

        if (msg.type === 'update' && msg.client_id !== TAB_CLIENT_ID && msg.snapshot !== undefined) {
          applyRemoteSnapshot(msg.snapshot)
          return
        }

        if (msg.type === 'diagram_updated' && msg.client_id !== TAB_CLIENT_ID && msg.diagram !== undefined) {
          const isNewest = onDiagramPushed?.(msg.diagram) ?? true
          // Editor tabs already sent their canvas over the socket; only saves made outside an
          // editor (the API, the MCP server) still have to be drawn here.
          if (isNewest && msg.client_id === null && msg.diagram.canvas_state !== null) {
            applyRemoteSnapshot(msg.diagram.canvas_state as unknown as TLStoreSnapshot)
          }
        }
      }

      ws.onclose = () => {
        if (connectionGeneration !== generation.current) {
          return
        }
        // Dropped unexpectedly (server restart, network): try again shortly.
        reconnectTimer.current = setTimeout(() => void connect(connectionGeneration), RECONNECT_DELAY_MS)
      }

      wsRef.current = ws
    },
    [diagramId, editor, onPresenceChange, onDiagramPushed, shareToken, guestName],
  )

  const sendUpdate = useCallback((snapshot: object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN && !applyingRemote.current) {
      wsRef.current.send(JSON.stringify({ type: 'update', client_id: TAB_CLIENT_ID, snapshot }))
    }
  }, [])

  useEffect(() => {
    generation.current += 1
    void connect(generation.current)
    return () => {
      generation.current += 1
      if (reconnectTimer.current !== null) {
        clearTimeout(reconnectTimer.current)
      }
      wsRef.current?.close()
      wsRef.current = null
    }
  }, [connect])

  return { sendUpdate }
}
