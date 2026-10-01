import { describe, expect, it } from 'vitest'

import { makeComment } from '../test/comments'
import { commentAuthor, commentResolver, openComments } from './comments'

const comment = makeComment

describe('commentAuthor', () => {
  it('should name people by their name', () => {
    expect(commentAuthor(comment())).toEqual({ name: 'Ana', isAgent: false, ownerId: 'u1', label: null })
  })

  it('should call anonymous comments anonymous', () => {
    expect(commentAuthor(comment({ author_id: null, author_name: null })).name).toBe('Anonymous')
  })

  it("should name agents after their owner, like the presence and the history", () => {
    const author = commentAuthor(comment({ origin: 'agent', agent_name: 'Claude', agent_label: 'laptop' }))
    expect(author).toEqual({ name: "Ana's Claude", isAgent: true, ownerId: 'u1', label: 'laptop' })
  })

  it('should name ownerless agents by the agent name alone', () => {
    const author = commentAuthor(comment({ origin: 'agent', author_id: null, author_name: null, agent_name: 'Claude' }))
    expect(author).toEqual({ name: 'Claude', isAgent: true, ownerId: null, label: null })
    expect(commentAuthor(comment({ origin: 'agent', author_name: null, agent_name: null })).name).toBe('AI agent')
  })
})

describe('commentResolver', () => {
  it('should have no resolver while open', () => {
    expect(commentResolver(comment())).toBeNull()
  })

  it('should name the agent that resolved it', () => {
    const resolved = comment({
      resolved: true,
      resolved_at: '2026-01-01T11:00:00Z',
      resolved_by_id: 'u2',
      resolved_by_name: 'Bruno',
      resolved_by_origin: 'agent',
      resolved_by_agent_name: 'Claude',
      resolved_by_agent_label: 'desk',
    })
    expect(commentResolver(resolved)).toEqual({ name: "Bruno's Claude", isAgent: true, ownerId: 'u2', label: 'desk' })
  })

  it('should name the person that resolved it', () => {
    const resolved = comment({ resolved: true, resolved_by_id: 'u2', resolved_by_name: 'Bruno', resolved_by_origin: 'human' })
    expect(commentResolver(resolved)).toEqual({ name: 'Bruno', isAgent: false, ownerId: 'u2', label: null })
    expect(commentResolver(comment({ resolved: true }))?.name).toBe('Someone')
  })
})

describe('openComments', () => {
  it('should keep only the open comments', () => {
    const open = comment({ id: 'open' })
    expect(openComments([open, comment({ id: 'done', resolved: true })])).toEqual([open])
  })
})
