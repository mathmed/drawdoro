import type { Editor, TLShape } from 'tldraw'

import type { ShapeMetadata, ValidationResult } from '../api/types'

// A node of the architecture graph: a canvas shape plus the ids of the shapes it
// is connected to (through arrows). Connections are treated as undirected here,
// which is enough to detect forbidden adjacencies.
export interface ArchitectureShape {
  id: string
  label: string
  // Only geo shapes (boxes, ellipses, ...) stand for components; free text, frames,
  // notes and drawings are annotations and never need a component type.
  isComponent: boolean
  connections: string[]
}

interface ArrowBindingProps {
  terminal?: 'start' | 'end'
}

function describe(editor: Editor, shape: TLShape): string {
  const text = editor.getShapeUtil(shape).getText(shape)?.trim()
  if (text !== undefined && text !== '') {
    return text.length > 40 ? `${text.slice(0, 40)}…` : text
  }
  const geo = (shape.props as { geo?: string }).geo
  const kind = (geo ?? shape.type).replace(/-/g, ' ')
  return `Untitled ${kind}`
}

// Builds the architecture graph from the current tldraw page: every non-arrow
// shape becomes a node, and every arrow bound to two shapes becomes an edge.
export function buildArchitectureGraph(editor: Editor): ArchitectureShape[] {
  const shapes = editor.getCurrentPageShapes()
  const nodes = new Map<string, ArchitectureShape>()

  for (const shape of shapes) {
    if (shape.type !== 'arrow') {
      nodes.set(shape.id, {
        id: shape.id,
        label: describe(editor, shape),
        isComponent: shape.type === 'geo',
        connections: [],
      })
    }
  }

  for (const shape of shapes) {
    if (shape.type !== 'arrow') {
      continue
    }
    const bindings = editor.getBindingsFromShape(shape, 'arrow')
    let start: string | undefined
    let end: string | undefined
    for (const binding of bindings) {
      const terminal = (binding.props as ArrowBindingProps).terminal
      if (terminal === 'start') {
        start = binding.toId
      } else if (terminal === 'end') {
        end = binding.toId
      }
    }
    if (start !== undefined && end !== undefined) {
      nodes.get(start)?.connections.push(end)
      nodes.get(end)?.connections.push(start)
    }
  }

  return [...nodes.values()]
}

export function validateArchitecture(
  shapes: ArchitectureShape[],
  metadata: Record<string, ShapeMetadata>,
): ValidationResult[] {
  const results: ValidationResult[] = []
  const seenEdges = new Set<string>()
  const byId = new Map(shapes.map((shape) => [shape.id, shape]))

  function labelFor(id: string): string {
    const meta = metadata[id]
    if (meta?.label !== undefined && meta.label !== '') {
      return meta.label
    }
    return byId.get(id)?.label ?? 'Unknown shape'
  }

  for (const shape of shapes) {
    const meta = metadata[shape.id]

    // Rule: every component must have a semantic type defined.
    if (shape.isComponent && (meta === undefined || meta.type === undefined)) {
      results.push({
        severity: 'warning',
        message: `“${labelFor(shape.id)}” has no component type.`,
        shapeIds: [shape.id],
      })
    }

    for (const otherId of shape.connections) {
      const edgeKey = [shape.id, otherId].sort().join('::')
      if (seenEdges.has(edgeKey)) {
        continue
      }
      seenEdges.add(edgeKey)

      const fromType = metadata[shape.id]?.type
      const toType = metadata[otherId]?.type
      const pair = new Set([fromType, toType])
      const names = `“${labelFor(shape.id)}” and “${labelFor(otherId)}”`

      // Rule: client cannot connect directly to a database.
      if (pair.has('client') && pair.has('database')) {
        results.push({
          severity: 'error',
          message: `${names} connect a client directly to a database — route it through a service or gateway.`,
          shapeIds: [shape.id, otherId],
        })
      }

      // Rule: a database cannot connect to an external system.
      if (pair.has('database') && pair.has('external')) {
        results.push({
          severity: 'error',
          message: `${names} connect a database to an external system, which is not allowed.`,
          shapeIds: [shape.id, otherId],
        })
      }
    }
  }

  return results
}
