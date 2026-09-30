import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it } from 'vitest'

import { useAppStore } from '../../store/useAppStore'
import PresenceAvatars from './PresenceAvatars'

beforeEach(() => {
  useAppStore.setState(useAppStore.getInitialState(), true)
})

describe('PresenceAvatars', () => {
  it("should show people with their photo and agents as their owner's Claude", () => {
    useAppStore.setState({
      presence: {
        you: 'u-bruno',
        users: [
          { id: 'u-ana', name: 'Ana', kind: 'person', picture_url: 'https://example.com/ana.png' },
          { id: 'u-bruno', name: 'Bruno', kind: 'person', picture_url: null },
          { id: 'agent:key:k1', name: 'Claude', kind: 'agent', owner_id: 'u-ana', owner_name: 'Ana', label: 'laptop' },
          { id: 'agent:Claude', name: 'Claude', kind: 'agent' },
        ],
      },
    })

    const { container } = render(<PresenceAvatars />)

    expect(screen.getByRole('group')).toHaveAccessibleName(
      "In this diagram: Bruno (you), Ana, Ana's Claude (AI agent · laptop), Claude (AI agent)",
    )
    expect(container.querySelector('img.presence-avatar-face')).toHaveAttribute('src', 'https://example.com/ana.png')
    expect(screen.getByLabelText("Ana's Claude (AI agent · laptop)")).toHaveClass('presence-agent')
    expect(screen.getByLabelText('Bruno (you)')).toHaveTextContent('B')
  })

  it('should render nothing when nobody is in the diagram', () => {
    const { container } = render(<PresenceAvatars />)

    expect(container).toBeEmptyDOMElement()
  })
})
