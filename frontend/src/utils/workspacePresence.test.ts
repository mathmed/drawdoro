import { describe, expect, it } from 'vitest'

import type { PresenceUser } from '../hooks/useRealtime'
import {
  applyPresence,
  EMPTY_PRESENCE_INDEX,
  othersThan,
  parseWorkspacePresenceMessage,
  sameUsers,
  type DiagramPresenceUpdate,
} from './workspacePresence'

const ANA: PresenceUser = { id: 'u-ana', name: 'Ana', kind: 'person', picture_url: 'https://example.com/ana.png' }
const BRUNO: PresenceUser = { id: 'u-bruno', name: 'Bruno', kind: 'person', picture_url: null }
const CARLA: PresenceUser = { id: 'u-carla', name: 'Carla', kind: 'person', picture_url: null }
const CLAUDE: PresenceUser = { id: 'agent:key:k1', name: 'Claude', kind: 'agent', owner_id: 'u-ana', owner_name: 'Ana', label: 'laptop' }

function update(diagramId: string, projectId: string, ...users: PresenceUser[]): DiagramPresenceUpdate {
  return { diagramId, projectId, users }
}

describe('parseWorkspacePresenceMessage', () => {
  const wireAna = { id: 'u-ana', name: 'Ana', kind: 'person', picture_url: 'https://example.com/ana.png' }
  const wireClaude = { id: 'agent:Claude', name: 'Claude', kind: 'agent' }

  it('should read a snapshot with people and agents', () => {
    const message = parseWorkspacePresenceMessage({
      type: 'presence_snapshot',
      you: 'u-bruno',
      diagrams: [{ diagram_id: 'd1', project_id: 'p1', users: [wireAna, wireClaude] }],
    })

    expect(message).toEqual({
      type: 'presence_snapshot',
      you: 'u-bruno',
      diagrams: [
        {
          diagramId: 'd1',
          projectId: 'p1',
          users: [
            { id: 'u-ana', name: 'Ana', kind: 'person', picture_url: 'https://example.com/ana.png' },
            { id: 'agent:Claude', name: 'Claude', kind: 'agent' },
          ],
        },
      ],
    })
  })

  it('should read a delta, including a diagram everyone left', () => {
    expect(
      parseWorkspacePresenceMessage({ type: 'presence_delta', diagrams: [{ diagram_id: 'd1', project_id: 'p1', users: [] }] }),
    ).toEqual({ type: 'presence_delta', diagrams: [{ diagramId: 'd1', projectId: 'p1', users: [] }] })
  })

  it('should read a snapshot for someone without an account', () => {
    expect(parseWorkspacePresenceMessage({ type: 'presence_snapshot', you: null, diagrams: [] })).toEqual({
      type: 'presence_snapshot',
      you: null,
      diagrams: [],
    })
  })

  it.each([
    ['not an object', 'presence_delta'],
    ['an unknown type', { type: 'presence_v2', diagrams: [] }],
    ['no diagrams', { type: 'presence_delta' }],
    ['a snapshot without you', { type: 'presence_snapshot', diagrams: [] }],
    ['a diagram without a project', { type: 'presence_delta', diagrams: [{ diagram_id: 'd1', users: [] }] }],
    ['a diagram without users', { type: 'presence_delta', diagrams: [{ diagram_id: 'd1', project_id: 'p1' }] }],
    ['a user without a name', { type: 'presence_delta', diagrams: [{ diagram_id: 'd1', project_id: 'p1', users: [{ id: 'x' }] }] }],
    ['an unknown kind', { type: 'presence_delta', diagrams: [{ diagram_id: 'd1', project_id: 'p1', users: [{ ...wireAna, kind: 'robot' }] }] }],
    ['a photo that is not a url', { type: 'presence_delta', diagrams: [{ diagram_id: 'd1', project_id: 'p1', users: [{ ...wireAna, picture_url: 1 }] }] }],
    ['an owner that is not text', { type: 'presence_delta', diagrams: [{ diagram_id: 'd1', project_id: 'p1', users: [{ ...wireClaude, owner_name: 2 }] }] }],
  ])('should ignore a message with %s', (_case, message) => {
    expect(parseWorkspacePresenceMessage(message)).toBeNull()
  })
})

describe('applyPresence', () => {
  it('should index a snapshot per diagram and gather each project once per person', () => {
    const index = applyPresence(
      EMPTY_PRESENCE_INDEX,
      [update('d1', 'p1', CLAUDE, BRUNO), update('d2', 'p1', ANA, BRUNO), update('d3', 'p2', CARLA)],
      true,
    )

    expect(index.byDiagram.d1.users).toEqual([CLAUDE, BRUNO])
    expect(index.byProject).toEqual({ p1: [ANA, BRUNO, CLAUDE], p2: [CARLA] })
  })

  it('should keep the entries of diagrams and projects that did not change', () => {
    const before = applyPresence(EMPTY_PRESENCE_INDEX, [update('d1', 'p1', ANA), update('d3', 'p2', CARLA)], true)

    const after = applyPresence(before, [update('d1', 'p1', { ...ANA }), update('d2', 'p1', ANA)], false)

    expect(after.byDiagram.d1).toBe(before.byDiagram.d1)
    expect(after.byDiagram.d3).toBe(before.byDiagram.d3)
    expect(after.byProject.p1).toBe(before.byProject.p1)
    expect(after.byProject.p2).toBe(before.byProject.p2)
  })

  it('should drop a diagram everyone left and the project once nobody is in it', () => {
    const before = applyPresence(EMPTY_PRESENCE_INDEX, [update('d1', 'p1', ANA), update('d2', 'p1', BRUNO)], true)

    const partly = applyPresence(before, [update('d1', 'p1')], false)
    expect(partly.byDiagram.d1).toBeUndefined()
    expect(partly.byProject.p1).toEqual([BRUNO])

    const empty = applyPresence(partly, [update('d2', 'p1')], false)
    expect(empty).toEqual(EMPTY_PRESENCE_INDEX)
  })

  it('should move people with a diagram that changed project', () => {
    const before = applyPresence(EMPTY_PRESENCE_INDEX, [update('d1', 'p1', ANA)], true)

    const after = applyPresence(before, [update('d1', 'p2', ANA)], false)

    expect(after.byDiagram.d1).toEqual({ projectId: 'p2', users: [ANA] })
    expect(after.byProject).toEqual({ p2: [ANA] })
  })

  it('should forget what a new snapshot no longer lists', () => {
    const before = applyPresence(EMPTY_PRESENCE_INDEX, [update('d1', 'p1', ANA), update('d3', 'p2', CARLA)], true)

    const after = applyPresence(before, [update('d3', 'p2', CARLA)], true)

    expect(after.byDiagram).toEqual({ d3: before.byDiagram.d3 })
    expect(after.byProject).toEqual({ p2: [CARLA] })
    expect(after.byProject.p2).toBe(before.byProject.p2)
  })

  it('should notice a new photo or name', () => {
    const before = applyPresence(EMPTY_PRESENCE_INDEX, [update('d1', 'p1', BRUNO)], true)
    const withPhoto = { ...BRUNO, picture_url: 'https://example.com/bruno.png' }

    const after = applyPresence(before, [update('d1', 'p1', withPhoto)], false)

    expect(after.byProject.p1).toEqual([withPhoto])
    expect(sameUsers([BRUNO], [{ ...BRUNO, name: 'Bruno S.' }])).toBe(false)
    expect(sameUsers([BRUNO], [{ ...BRUNO, picture_url: undefined }])).toBe(true)
    expect(sameUsers(undefined, [])).toBe(false)
  })
})

describe('othersThan', () => {
  it('should leave out this person and this tab', () => {
    expect(othersThan([ANA, BRUNO, CARLA], ['u-ana', null, 'u-carla'])).toEqual([BRUNO])
  })
})
