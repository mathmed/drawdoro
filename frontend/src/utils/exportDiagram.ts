import type { Editor } from 'tldraw'

import type { Diagram } from '../api/types'
import { toast } from '../store/useToastStore'

export type ExportFormat = 'png' | 'svg' | 'json'

function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  anchor.click()
  URL.revokeObjectURL(url)
}

export async function exportDiagram(
  format: ExportFormat,
  diagram: Diagram,
  editor: Editor | null,
): Promise<void> {
  const name = diagram.name.trim() === '' ? 'diagram' : diagram.name

  if (format === 'png' || format === 'svg') {
    if (editor === null) {
      return
    }
    const shapeIds = [...editor.getCurrentPageShapeIds()]
    if (shapeIds.length === 0) {
      toast('The canvas is empty — draw something before exporting.', 'info')
      return
    }
    const { blob } = await editor.toImage(shapeIds, { format, background: true, pixelRatio: 2 })
    downloadBlob(blob, `${name}.${format}`)
    return
  }

  const state = diagram.canvas_state ?? {}
  downloadBlob(
    new Blob([JSON.stringify(state, null, 2)], { type: 'application/json;charset=utf-8' }),
    `${name}.json`,
  )
}
