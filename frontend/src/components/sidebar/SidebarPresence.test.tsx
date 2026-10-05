import { act, render, screen, within } from '@testing-library/react'
import { Profiler } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { PresenceUser } from '../../hooks/useRealtime'
import { useAppStore } from '../../store/useAppStore'
import { useWorkspacePresenceStore } from '../../store/useWorkspacePresenceStore'
import type { DiagramPresenceUpdate } from '../../utils/workspacePresence'
import { DiagramPresence, ProjectPresence } from './SidebarPresence'

const ANA: PresenceUser = { id: 'u-ana', name: 'Ana', kind: 'person', picture_url: 'https://example.com/ana.png' }
const BRUNO: PresenceUser = { id: 'u-bruno', name: 'Bruno', kind: 'person', picture_url: null }
const CARLA: PresenceUser = { id: 'u-carla', name: 'Carla', kind: 'person', picture_url: null }
const DAVI: PresenceUser = { id: 'u-davi', name: 'Davi', kind: 'person', picture_url: null }
const EVA: PresenceUser = { id: 'u-eva', name: 'Eva', kind: 'person', picture_url: null }
const CLAUDE: PresenceUser = { id: 'agent:key:k1', name: 'Claude', kind: 'agent', owner_id: 'u-ana', owner_name: 'Ana', label: 'laptop' }

function update(diagramId: string, projectId: string, ...users: PresenceUser[]): DiagramPresenceUpdate {
  return { diagramId, projectId, users }
}

function snapshot(you: string | null, ...diagrams: DiagramPresenceUpdate[]): void {
  act(() => useWorkspacePresenceStore.getState().applySnapshot(you, diagrams))
}

beforeEach(() => {
  useAppStore.setState(useAppStore.getInitialState(), true)
  useWorkspacePresenceStore.getState().reset()
})

describe('DiagramPresence', () => {
  it("should show the other people's photos, initials and agents with their names", () => {
    snapshot('u-me', update('d1', 'p1', ANA, BRUNO, CLAUDE))
    const { container } = render(<DiagramPresence diagramId="d1" />)

    expect(screen.getByRole('group')).toHaveAccessibleName("In this diagram now: Ana, Bruno, Ana's Claude (AI agent · laptop)")
    expect(container.querySelector('img.presence-avatar-face')).toHaveAttribute('src', 'https://example.com/ana.png')
    expect(screen.getByLabelText('Bruno')).toHaveTextContent('B')
    expect(screen.getByLabelText('Bruno')).toHaveAttribute('data-tooltip', 'Bruno')
    expect(screen.getByLabelText("Ana's Claude (AI agent · laptop)")).toHaveClass('presence-agent')
  })

  it('should fall back to the initial when the photo does not load', () => {
    snapshot(null, update('d1', 'p1', ANA))
    const { container } = render(<DiagramPresence diagramId="d1" />)

    act(() => {
      container.querySelector('img')?.dispatchEvent(new Event('error'))
    })

    expect(container.querySelector('img')).toBeNull()
    expect(screen.getByLabelText('Ana')).toHaveTextContent('A')
  })

  it('should stack three faces and count the rest, naming them in the tooltip', () => {
    snapshot(null, update('d1', 'p1', ANA, BRUNO, CARLA, DAVI, EVA))
    render(<DiagramPresence diagramId="d1" />)

    const group = screen.getByRole('group')
    expect(within(group).getAllByLabelText(/^(Ana|Bruno|Carla)$/)).toHaveLength(3)
    const more = within(group).getByText('+2')
    expect(more).toHaveAttribute('data-tooltip', 'Davi, Eva')
    expect(more).toHaveAccessibleName('2 more: Davi, Eva')
  })

  it('should leave this person out, by account and by tab', () => {
    useAppStore.setState({ presence: { users: [], you: 'tab-1' } })
    snapshot('u-ana', update('d1', 'p1', ANA, { ...BRUNO, id: 'tab-1' }, CARLA))
    render(<DiagramPresence diagramId="d1" />)

    expect(screen.getByRole('group')).toHaveAccessibleName('In this diagram now: Carla')
  })

  it('should render nothing when nobody else is there', () => {
    snapshot('u-ana', update('d1', 'p1', ANA))
    const { container } = render(<DiagramPresence diagramId="d1" />)

    expect(container).toBeEmptyDOMElement()
  })

  it('should follow people coming and going', () => {
    render(<DiagramPresence diagramId="d1" />)
    expect(screen.queryByRole('group')).not.toBeInTheDocument()

    act(() => useWorkspacePresenceStore.getState().applyDelta([update('d1', 'p1', BRUNO)]))
    expect(screen.getByRole('group')).toHaveAccessibleName('In this diagram now: Bruno')

    act(() => useWorkspacePresenceStore.getState().applyDelta([update('d1', 'p1')]))
    expect(screen.queryByRole('group')).not.toBeInTheDocument()
  })

  it('should not render a row again when only another diagram changed', () => {
    snapshot(null, update('d1', 'p1', ANA), update('d2', 'p1', BRUNO))
    const renders = vi.fn()
    render(
      <Profiler id="d2" onRender={renders}>
        <DiagramPresence diagramId="d2" />
      </Profiler>,
    )
    renders.mockClear()

    act(() => useWorkspacePresenceStore.getState().applyDelta([update('d1', 'p1', ANA, CARLA)]))

    expect(renders).not.toHaveBeenCalled()
  })
})

describe('ProjectPresence', () => {
  it('should show everyone in any diagram of the project once', () => {
    snapshot('u-me', update('d1', 'p1', BRUNO, CLAUDE), update('d2', 'p1', ANA, BRUNO), update('d3', 'p2', CARLA))
    render(<ProjectPresence projectId="p1" />)

    expect(screen.getByRole('group')).toHaveAccessibleName("In this project now: Ana, Bruno, Ana's Claude (AI agent · laptop)")
  })

  it('should leave this person out of the project too', () => {
    snapshot('u-ana', update('d1', 'p1', ANA), update('d2', 'p1', ANA))
    const { container } = render(<ProjectPresence projectId="p1" />)

    expect(container).toBeEmptyDOMElement()
  })
})
