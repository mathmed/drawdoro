import { describe, expect, it } from 'vitest'

import type { DiagramRevision } from '../api/types'
import { agentDescription, agentDisplayName } from './agents'
import { revisionAuthor, revisionDescription } from './revisions'

function revision(overrides: Partial<DiagramRevision> = {}): DiagramRevision {
  return {
    id: 'r1',
    diagram_id: 'd1',
    kind: 'edit',
    origin: 'human',
    author_id: 'u1',
    author_name: 'Ana',
    author_picture_url: null,
    agent_name: null,
    agent_label: null,
    summary: null,
    restored_from_id: null,
    created_at: '2026-01-01T10:00:00Z',
    updated_at: '2026-01-01T10:00:00Z',
    ...overrides,
  }
}

describe('agents', () => {
  it("should name an agent with a personal key after its owner", () => {
    expect(agentDisplayName({ name: 'Claude', ownerName: 'Ana' })).toBe("Ana's Claude")
  })

  it('should keep the plain name for an agent on the shared service key', () => {
    expect(agentDisplayName({ name: 'Claude', ownerName: null })).toBe('Claude')
  })

  it('should describe the agent with its key label when there is one', () => {
    expect(agentDescription({ name: 'Claude', ownerName: 'Ana', label: 'laptop' })).toBe("Ana's Claude (AI agent · laptop)")
    expect(agentDescription({ name: 'Claude' })).toBe('Claude (AI agent)')
  })
})

describe('revisionAuthor', () => {
  it('should show the person who edited', () => {
    expect(revisionAuthor(revision())).toBe('Ana')
    expect(revisionAuthor(revision({ author_name: null }))).toBe('Someone')
  })

  it("should show an agent change as the owner's agent", () => {
    expect(revisionAuthor(revision({ origin: 'agent', agent_name: 'Claude' }))).toBe("Ana's Claude")
    expect(revisionAuthor(revision({ origin: 'agent', agent_name: null, author_name: null }))).toBe('AI agent')
  })

  it('should label the baseline as an earlier version', () => {
    expect(revisionAuthor(revision({ kind: 'baseline' }))).toBe('Earlier version')
  })
})

describe('revisionDescription', () => {
  it('should prefer the summary the author gave', () => {
    expect(revisionDescription(revision({ summary: 'Added the queue' }))).toBe('Added the queue')
  })

  it('should fall back to a description of the kind of change', () => {
    expect(revisionDescription(revision())).toBe('Edited the diagram')
    expect(revisionDescription(revision({ origin: 'agent' }))).toBe('Changed the diagram')
    expect(revisionDescription(revision({ kind: 'restore' }))).toBe('Restored an earlier version')
    expect(revisionDescription(revision({ kind: 'baseline', summary: 'ignored' }))).toBe('State before the recorded changes')
  })
})
