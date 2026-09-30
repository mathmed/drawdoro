import type { Editor, TLShape } from 'tldraw'
import { describe, expect, it } from 'vitest'

import type { ShapeMetadata } from '../api/types'
import { buildArchitectureGraph, validateArchitecture, type ArchitectureShape } from './validateArchitecture'

function node(id: string, connections: string[] = [], isComponent = true): ArchitectureShape {
  return { id, label: id.toUpperCase(), isComponent, connections }
}

describe('validateArchitecture', () => {
  it('should accept a typed client → service → database chain', () => {
    const shapes = [node('a', ['b']), node('b', ['a', 'c']), node('c', ['b'])]
    const metadata: Record<string, ShapeMetadata> = { a: { type: 'client' }, b: { type: 'service' }, c: { type: 'database' } }

    expect(validateArchitecture(shapes, metadata)).toEqual([])
  })

  it('should warn about components without a type but not about annotations', () => {
    const shapes = [node('a'), node('note', [], false)]

    expect(validateArchitecture(shapes, {})).toEqual([
      { severity: 'warning', message: '“A” has no component type.', shapeIds: ['a'] },
    ])
  })

  it('should prefer the semantic label over the canvas text', () => {
    const results = validateArchitecture([node('a')], { a: { label: 'Orders API' } })

    expect(results[0].message).toBe('“Orders API” has no component type.')
  })

  it('should flag a client connected straight to a database only once per edge', () => {
    const shapes = [node('web', ['db']), node('db', ['web'])]
    const metadata: Record<string, ShapeMetadata> = { web: { type: 'client' }, db: { type: 'database' } }

    const results = validateArchitecture(shapes, metadata)

    expect(results).toHaveLength(1)
    expect(results[0]).toMatchObject({ severity: 'error', shapeIds: ['web', 'db'] })
    expect(results[0].message).toContain('connect a client directly to a database')
  })

  it('should flag a database connected to an external system', () => {
    const shapes = [node('db', ['stripe']), node('stripe', ['db'])]
    const metadata: Record<string, ShapeMetadata> = { db: { type: 'database' }, stripe: { type: 'external' } }

    const results = validateArchitecture(shapes, metadata)

    expect(results).toHaveLength(1)
    expect(results[0].message).toContain('connect a database to an external system')
  })

  it('should name connections to shapes missing from the graph', () => {
    const results = validateArchitecture([node('web', ['ghost'])], { web: { type: 'client' }, ghost: { type: 'database' } })

    expect(results[0].message).toContain('“Unknown shape”')
  })
})

describe('buildArchitectureGraph', () => {
  type FakeShape = Pick<TLShape, 'id' | 'type'> & { props: Record<string, unknown>; text?: string }
  type FakeBinding = { toId: string; props: { terminal: 'start' | 'end' } }

  function fakeEditor(shapes: FakeShape[], bindings: Record<string, FakeBinding[]>): Editor {
    return {
      getCurrentPageShapes: () => shapes,
      getShapeUtil: () => ({ getText: (shape: FakeShape) => shape.text }),
      getBindingsFromShape: (shape: FakeShape) => bindings[shape.id] ?? [],
    } as unknown as Editor
  }

  function shape(id: string, type: string, extra: Partial<FakeShape> = {}): FakeShape {
    return { id: id as TLShape['id'], type, props: {}, ...extra }
  }

  it('should turn shapes into nodes and fully bound arrows into undirected edges', () => {
    const editor = fakeEditor(
      [
        shape('shape:a', 'geo', { text: '  Web app ', props: { geo: 'rectangle' } }),
        shape('shape:b', 'geo', { props: { geo: 'ellipse' } }),
        shape('shape:t', 'text', { text: 'x'.repeat(45) }),
        shape('shape:arrow', 'arrow'),
        shape('shape:dangling', 'arrow'),
      ],
      {
        'shape:arrow': [
          { toId: 'shape:a', props: { terminal: 'start' } },
          { toId: 'shape:b', props: { terminal: 'end' } },
        ],
        'shape:dangling': [{ toId: 'shape:a', props: { terminal: 'start' } }],
      },
    )

    expect(buildArchitectureGraph(editor)).toEqual([
      { id: 'shape:a', label: 'Web app', isComponent: true, connections: ['shape:b'] },
      { id: 'shape:b', label: 'Untitled ellipse', isComponent: true, connections: ['shape:a'] },
      { id: 'shape:t', label: `${'x'.repeat(40)}…`, isComponent: false, connections: [] },
    ])
  })
})
