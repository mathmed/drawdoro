import type { Editor } from 'tldraw'

import type { ShapeMetadata, ValidationResult } from '../api/types'

// A node of the architecture graph: a canvas shape plus the ids of the shapes it
// is connected to (through arrows). Connections are treated as undirected here,
// which is enough to detect forbidden adjacencies.
export interface ArchitectureShape {
  id: string
  connections: string[]
}

interface ArrowBindingProps {
  terminal?: 'start' | 'end'
}

// Builds the architecture graph from the current tldraw page: every non-arrow
// shape becomes a node, and every arrow bound to two shapes becomes an edge.
export function buildArchitectureGraph(editor: Editor): ArchitectureShape[] {
  const shapes = editor.getCurrentPageShapes()
  const adjacency = new Map<string, Set<string>>()

  for (const shape of shapes) {
    if (shape.type !== 'arrow') {
      adjacency.set(shape.id, new Set())
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
      adjacency.get(start)?.add(end)
      adjacency.get(end)?.add(start)
    }
  }

  return [...adjacency.entries()].map(([id, connections]) => ({
    id,
    connections: [...connections],
  }))
}

export function validateArchitecture(
  shapes: ArchitectureShape[],
  metadata: Record<string, ShapeMetadata>,
): ValidationResult[] {
  const results: ValidationResult[] = []
  const seenEdges = new Set<string>()

  function labelFor(id: string): string {
    const meta = metadata[id]
    if (meta?.label !== undefined && meta.label !== '') {
      return meta.label
    }
    return id
  }

  for (const shape of shapes) {
    const meta = metadata[shape.id]

    // Rule: a service must have a semantic type defined.
    if (meta === undefined || meta.type === undefined) {
      results.push({
        severity: 'warning',
        message: `Element "${labelFor(shape.id)}" has no semantic type defined.`,
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

      // Rule: client cannot connect directly to a database.
      if (pair.has('client') && pair.has('database')) {
        results.push({
          severity: 'error',
          message: `"${labelFor(shape.id)}" (client/database) connects directly — a client must go through a service or gateway.`,
        })
      }

      // Rule: a database cannot connect to an external system.
      if (pair.has('database') && pair.has('external')) {
        results.push({
          severity: 'error',
          message: `"${labelFor(shape.id)}" connects a database to an external system, which is not allowed.`,
        })
      }
    }
  }

  return results
}
