import type { Comment } from '../api/types'
import { agentDisplayName } from './agents'

export interface CommentActorView {
  name: string
  isAgent: boolean
  // The person an agent works for, so its avatar gets the same ring colour as in the presence.
  ownerId: string | null
  label: string | null
}

// "Ana's Claude" for an agent with a personal key, the agent name alone on the shared service key.
export function commentAuthor(comment: Comment): CommentActorView {
  if (comment.origin === 'agent') {
    return {
      name: agentDisplayName({ name: comment.agent_name ?? 'AI agent', ownerName: comment.author_name }),
      isAgent: true,
      ownerId: comment.author_id,
      label: comment.agent_label,
    }
  }
  return { name: comment.author_name ?? 'Anonymous', isAgent: false, ownerId: comment.author_id, label: null }
}

export function commentResolver(comment: Comment): CommentActorView | null {
  if (!comment.resolved) {
    return null
  }
  if (comment.resolved_by_origin === 'agent') {
    return {
      name: agentDisplayName({ name: comment.resolved_by_agent_name ?? 'AI agent', ownerName: comment.resolved_by_name }),
      isAgent: true,
      ownerId: comment.resolved_by_id,
      label: comment.resolved_by_agent_label,
    }
  }
  return { name: comment.resolved_by_name ?? 'Someone', isAgent: false, ownerId: comment.resolved_by_id, label: null }
}

export function openComments(comments: Comment[]): Comment[] {
  return comments.filter((comment) => !comment.resolved)
}
