import { Tldraw } from 'tldraw'
import 'tldraw/tldraw.css'

interface DrawingCanvasProps {
  diagramId: string
}

export default function DrawingCanvas({ diagramId }: DrawingCanvasProps) {
  return (
    <div style={{ position: 'fixed', inset: 0 }}>
      <Tldraw
        persistenceKey={diagramId || 'drawdoro-default'}
      />
    </div>
  )
}
