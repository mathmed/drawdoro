import { useCallback, useEffect, useRef } from 'react'
import type { Editor, TLStoreSnapshot } from 'tldraw'

interface RealtimeOptions {
  diagramId: string
  editor: Editor | null
  onPeersChange: (count: number) => void
}

interface RealtimeMessage {
  type: string
  peers?: number
  client_id?: string
  snapshot?: TLStoreSnapshot
}

export function useRealtime({ diagramId, editor, onPeersChange }: RealtimeOptions) {
  const wsRef = useRef<WebSocket | null>(null)
  const clientId = useRef(crypto.randomUUID())
  const applyingRemote = useRef(false)
  const closedByUs = useRef(false)
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  const connect = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const ws = new WebSocket(
      `${protocol}//${window.location.host}/api/ws/diagrams/${diagramId}`,
    )

    ws.onopen = () => console.log('[realtime] conectado')

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data) as RealtimeMessage

      if (msg.type === 'peers' || msg.type === 'peer_joined' || msg.type === 'peer_left') {
        onPeersChange(msg.peers ?? 1)
        return
      }

      if (
        msg.type === 'update' &&
        msg.client_id !== clientId.current &&
        msg.snapshot !== undefined &&
        editor !== null
      ) {
        const snapshot = msg.snapshot
        applyingRemote.current = true
        editor.store.mergeRemoteChanges(() => {
          editor.store.loadSnapshot(snapshot)
        })
        applyingRemote.current = false
      }
    }

    ws.onclose = () => {
      if (closedByUs.current) {
        return
      }
      // Reconectar apos 2s se nao for fechamento intencional
      reconnectTimer.current = setTimeout(connect, 2000)
    }

    wsRef.current = ws
  }, [diagramId, editor, onPeersChange])

  // Enviar update quando o canvas muda
  const sendUpdate = useCallback((snapshot: object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN && !applyingRemote.current) {
      wsRef.current.send(
        JSON.stringify({
          type: 'update',
          client_id: clientId.current,
          snapshot,
        }),
      )
    }
  }, [])

  useEffect(() => {
    closedByUs.current = false
    connect()
    return () => {
      closedByUs.current = true
      if (reconnectTimer.current !== null) {
        clearTimeout(reconnectTimer.current)
      }
      wsRef.current?.close()
    }
  }, [connect])

  return { sendUpdate }
}
