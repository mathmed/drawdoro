import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { getRevision, listRevisions, restoreRevision } from '../../api/revisions'
import type { Diagram, DiagramRevision } from '../../api/types'
import { useAppStore } from '../../store/useAppStore'
import { confirmDialog } from '../../store/useDialogStore'
import HistoryPanel from './HistoryPanel'

vi.mock('tldraw', () => ({
  TldrawImage: () => <div data-testid="revision-preview" />,
  loadSnapshot: vi.fn(),
}))
vi.mock('../canvas/shapeUtils', () => ({ shapeUtils: [] }))
vi.mock('../../api/revisions')
vi.mock('../../store/useDialogStore', () => ({ confirmDialog: vi.fn() }))
vi.mock('../../store/useToastStore', () => ({ toast: vi.fn() }))

const DIAGRAM: Diagram = {
  id: 'd1',
  project_id: 'p1',
  folder_id: null,
  name: 'Checkout',
  canvas_state: { shapes: 1 },
  updated_at: '2026-01-01T12:00:00Z',
}

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

const AGENT_CHANGE = revision({
  id: 'r2',
  origin: 'agent',
  agent_name: 'Claude',
  agent_label: 'laptop',
  summary: 'Added the payments queue',
  updated_at: '2026-01-01T11:00:00Z',
})
const PERSON_EDIT = revision({ id: 'r1', author_picture_url: 'https://example.com/ana.png' })

beforeEach(() => {
  useAppStore.setState(useAppStore.getInitialState(), true)
  useAppStore.setState({ activeDiagram: DIAGRAM, myRole: 'editor' })
  vi.mocked(listRevisions).mockResolvedValue([AGENT_CHANGE, PERSON_EDIT])
})

describe('HistoryPanel', () => {
  it("should list agent changes as the owner's Claude with the key label", async () => {
    render(<HistoryPanel />)

    expect(await screen.findByText("Ana's Claude")).toBeInTheDocument()
    expect(screen.getByText('laptop')).toBeInTheDocument()
    expect(screen.getByText('Added the payments queue')).toBeInTheDocument()
    expect(listRevisions).toHaveBeenCalledWith('d1')
  })

  it("should show the person's profile photo next to their edit", async () => {
    const { container } = render(<HistoryPanel />)

    await screen.findByText('Edited the diagram')
    expect(container.querySelector('img.revision-avatar')).toHaveAttribute('src', 'https://example.com/ana.png')
  })

  it('should explain the empty history', async () => {
    vi.mocked(listRevisions).mockResolvedValue([])

    render(<HistoryPanel />)

    expect(await screen.findByText('No history yet')).toBeInTheDocument()
  })

  it('should preview a version and restore it after confirmation', async () => {
    vi.mocked(getRevision).mockResolvedValue({ ...PERSON_EDIT, name: 'Checkout', canvas_state: { shapes: 0 }, semantic_metadata: null })
    vi.mocked(confirmDialog).mockResolvedValue(true)
    vi.mocked(restoreRevision).mockResolvedValue({ ...DIAGRAM, canvas_state: { shapes: 0 }, updated_at: '2026-01-01T13:00:00Z' })
    render(<HistoryPanel />)

    await userEvent.click(await screen.findByRole('button', { name: /Edited the diagram/ }))
    expect(await screen.findByTestId('revision-preview')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: /Restore this version/ }))

    await waitFor(() => expect(restoreRevision).toHaveBeenCalledWith('d1', 'r1'))
    expect(getRevision).toHaveBeenCalledWith('d1', 'r1')
    expect(useAppStore.getState().activeDiagram?.updated_at).toBe('2026-01-01T13:00:00Z')
  })

  it('should not restore when the confirmation is dismissed', async () => {
    vi.mocked(getRevision).mockResolvedValue({ ...PERSON_EDIT, name: 'Checkout', canvas_state: null, semantic_metadata: null })
    vi.mocked(confirmDialog).mockResolvedValue(false)
    render(<HistoryPanel />)

    await userEvent.click(await screen.findByRole('button', { name: /Edited the diagram/ }))
    expect(await screen.findByText('Empty canvas')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: /Restore this version/ }))

    expect(confirmDialog).toHaveBeenCalledOnce()
    expect(restoreRevision).not.toHaveBeenCalled()
  })

  it('should not offer restore to viewers nor for the current version', async () => {
    useAppStore.setState({ myRole: 'viewer' })
    vi.mocked(getRevision).mockResolvedValue({ ...PERSON_EDIT, name: 'Checkout', canvas_state: null, semantic_metadata: null })
    render(<HistoryPanel />)

    await userEvent.click(await screen.findByRole('button', { name: /Edited the diagram/ }))

    expect(screen.getByText("Viewers can't restore versions.")).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Restore this version/ })).not.toBeInTheDocument()
  })
})
