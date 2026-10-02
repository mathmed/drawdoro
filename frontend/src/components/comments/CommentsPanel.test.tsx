import { act, render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { listComments, setCommentResolved } from '../../api/comments'
import type { Comment, Diagram } from '../../api/types'
import { useAppStore } from '../../store/useAppStore'
import { makeComment } from '../../test/comments'
import { pastLoaderDelay, pastLoaderExit } from '../../test/timers'
import CommentsPanel from './CommentsPanel'

vi.mock('../../api/comments')

const DIAGRAM: Diagram = {
  id: 'd1',
  project_id: 'p1',
  folder_id: null,
  name: 'Checkout',
  canvas_state: null,
  updated_at: '2026-01-01T12:00:00Z',
}

const PERSONS = makeComment({ id: 'person', content: 'Missing the payments service' })
const AGENTS = makeComment({
  id: 'agent',
  content: 'Added the payments service',
  origin: 'agent',
  agent_name: 'Claude',
  agent_label: 'laptop',
})
const RESOLVED = makeComment({
  id: 'resolved',
  content: 'Rename the gateway',
  resolved: true,
  resolved_at: '2026-01-01T11:00:00Z',
  resolved_by_id: 'u1',
  resolved_by_name: 'Ana',
  resolved_by_origin: 'agent',
  resolved_by_agent_name: 'Claude',
  resolved_by_agent_label: 'laptop',
})

function showComments(comments: Comment[]): void {
  vi.mocked(listComments).mockResolvedValue(comments)
  useAppStore.setState({ comments })
}

beforeEach(() => {
  useAppStore.setState(useAppStore.getInitialState(), true)
  useAppStore.setState({ activeDiagram: DIAGRAM, myRole: 'editor' })
  showComments([PERSONS, AGENTS, RESOLVED])
})

describe('CommentsPanel', () => {
  it("should show agent comments as the owner's Claude with an agent mark", async () => {
    render(<CommentsPanel />)

    const comment = (await screen.findByText('Added the payments service')).closest('.comment') as HTMLElement
    expect(within(comment).getByText("Ana's Claude")).toBeInTheDocument()
    expect(within(comment).getByText('laptop')).toBeInTheDocument()
    expect(within(comment).getByLabelText("Ana's Claude (AI agent)")).toBeInTheDocument()
  })

  it('should hide resolved comments until asked', async () => {
    const user = userEvent.setup()
    render(<CommentsPanel />)

    await screen.findByText('Missing the payments service')
    expect(screen.queryByText('Rename the gateway')).not.toBeInTheDocument()
    expect(screen.getByText('2 open · 1 resolved')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Show resolved (1)' }))

    const resolved = screen.getByText('Rename the gateway').closest('.comment') as HTMLElement
    expect(resolved).toHaveClass('comment-resolved')
    expect(within(resolved).getByText(/Resolved by Ana's Claude/)).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Hide resolved' }))
    expect(screen.queryByText('Rename the gateway')).not.toBeInTheDocument()
  })

  it('should let editors resolve and reopen comments', async () => {
    const user = userEvent.setup()
    vi.mocked(setCommentResolved).mockResolvedValueOnce({ ...PERSONS, resolved: true, resolved_at: '2026-01-01T12:00:00Z' })
    render(<CommentsPanel />)

    const person = (await screen.findByText('Missing the payments service')).closest('.comment') as HTMLElement
    await user.click(within(person).getByRole('button', { name: 'Resolve' }))

    expect(setCommentResolved).toHaveBeenCalledWith('d1', 'person', true)
    expect(screen.queryByText('Missing the payments service')).not.toBeInTheDocument()

    vi.mocked(setCommentResolved).mockResolvedValueOnce({ ...RESOLVED, resolved: false, resolved_at: null })
    await user.click(screen.getByRole('button', { name: 'Show resolved (2)' }))
    const resolved = screen.getByText('Rename the gateway').closest('.comment') as HTMLElement
    await user.click(within(resolved).getByRole('button', { name: 'Reopen' }))
    expect(setCommentResolved).toHaveBeenLastCalledWith('d1', 'resolved', false)
  })

  it("should not offer viewers to resolve", async () => {
    useAppStore.setState({ myRole: 'viewer' })
    render(<CommentsPanel />)

    await screen.findByText('Missing the payments service')
    expect(screen.queryByRole('button', { name: 'Resolve' })).not.toBeInTheDocument()
  })

  it('should render markup in comments as plain text', async () => {
    showComments([makeComment({ content: '<img src=x onerror="alert(1)"><b>bold</b>' })])
    const { container } = render(<CommentsPanel />)

    expect(await screen.findByText('<img src=x onerror="alert(1)"><b>bold</b>')).toBeInTheDocument()
    expect(container.querySelector('.comment-text img')).toBeNull()
    expect(container.querySelector('.comment-text b')).toBeNull()
  })

  it('should mark comments on the whole diagram', async () => {
    showComments([makeComment({ element_id: null, content: 'Overall looks good' })])
    render(<CommentsPanel />)

    expect(await screen.findByText('on the diagram')).toBeInTheDocument()
  })

  it('should say when only resolved comments are left', async () => {
    showComments([RESOLVED])
    render(<CommentsPanel />)

    expect(await screen.findByText('No open comments')).toBeInTheDocument()
  })

  describe('while the comments load', () => {
    afterEach(() => {
      vi.useRealTimers()
    })

    it('should show placeholder comments instead of the empty state', async () => {
      vi.useFakeTimers()
      useAppStore.setState({ comments: [], isLoadingDiagramDetails: true })
      vi.mocked(listComments).mockReturnValue(new Promise(() => undefined))
      render(<CommentsPanel />)

      expect(screen.queryByText('No comments yet')).not.toBeInTheDocument()
      await pastLoaderDelay()
      expect(screen.getByRole('status')).toHaveTextContent('Loading comments')

      act(() => useAppStore.setState({ comments: [PERSONS], isLoadingDiagramDetails: false }))
      await pastLoaderExit()
      expect(screen.queryByRole('status')).not.toBeInTheDocument()
      expect(screen.getByText('Missing the payments service')).toBeInTheDocument()
    })
  })

  it('should show the send button as busy until the comment is saved', async () => {
    let finish!: () => void
    const addComment = vi.fn(() => new Promise<void>((done) => (finish = done)))
    useAppStore.setState({ activeElementId: 'shape:1', addComment })
    const user = userEvent.setup()
    render(<CommentsPanel />)

    await user.type(screen.getByRole('textbox'), 'Looks good')
    await user.click(screen.getByRole('button', { name: /Send/ }))

    const send = screen.getByRole('button', { name: /Send/ })
    expect(send).toHaveAttribute('aria-busy', 'true')
    expect(send).toBeDisabled()
    await act(async () => finish())
    expect(addComment).toHaveBeenCalledTimes(1)
    expect(screen.getByRole('button', { name: /Send/ })).toHaveAttribute('aria-busy', 'false')
    expect(screen.getByRole('textbox')).toHaveValue('')
  })
})
