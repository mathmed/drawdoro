import { useParams } from 'react-router-dom'
import DrawingCanvas from '../components/canvas/DrawingCanvas'

export default function DiagramPage() {
  const { id } = useParams<{ id: string }>()
  return <DrawingCanvas diagramId={id ?? ''} />
}
