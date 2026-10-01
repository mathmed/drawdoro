import type { Comment } from '../api/types'

export function makeComment(overrides: Partial<Comment> = {}): Comment {
  return {
    id: 'c1',
    diagram_id: 'd1',
    element_id: 'shape:a',
    content: 'Missing the queue',
    author_id: 'u1',
    author_name: 'Ana',
    origin: 'human',
    agent_name: null,
    agent_label: null,
    created_at: '2026-01-01T10:00:00Z',
    resolved: false,
    resolved_at: null,
    resolved_by_id: null,
    resolved_by_name: null,
    resolved_by_origin: null,
    resolved_by_agent_name: null,
    resolved_by_agent_label: null,
    created_by_you: false,
    ...overrides,
  }
}
