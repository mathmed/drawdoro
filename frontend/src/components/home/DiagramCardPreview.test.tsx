import { act, render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useThemeStore } from '../../store/useThemeStore'
import { projectKey, useThumbnailStore } from '../../store/useThumbnailStore'
import DiagramCardPreview from './DiagramCardPreview'

// jsdom has no matchMedia, which the theme store reads when it loads.
vi.hoisted(() => {
  Object.defineProperty(window, 'matchMedia', {
    configurable: true,
    value: () => ({ matches: false, addEventListener: () => undefined }),
  })
})

const LIGHT = 'data:image/webp;base64,TElHSFQ='
const DARK = 'data:image/webp;base64,REFSSw=='

function renderSut(): HTMLElement {
  const { container } = render(<DiagramCardPreview projectId="p1" diagramId="d1" />)
  return container
}

beforeEach(() => {
  useThumbnailStore.setState(useThumbnailStore.getInitialState(), true)
  useThemeStore.setState({ resolved: 'light' })
})

describe('DiagramCardPreview', () => {
  it('should show the preview in the current theme', () => {
    useThumbnailStore.setState({
      byProject: {
        [projectKey('light', 'p1')]: { loaded: true, items: { d1: { src: LIGHT, version: 'v1' } } },
        [projectKey('dark', 'p1')]: { loaded: true, items: { d1: { src: DARK, version: 'v1' } } },
      },
    })
    const container = renderSut()

    expect(container.querySelector('img')).toHaveAttribute('src', LIGHT)

    act(() => useThemeStore.setState({ resolved: 'dark' }))
    expect(container.querySelector('img')).toHaveAttribute('src', DARK)
  })

  it('should show the placeholder icon for a diagram without a preview', () => {
    useThumbnailStore.setState({
      byProject: { [projectKey('light', 'p1')]: { loaded: true, items: { d1: { src: null, version: 'v1' } } } },
    })
    const container = renderSut()

    expect(container.querySelector('img')).toBeNull()
    expect(screen.getByTestId('diagram-card-placeholder').querySelector('svg')).not.toBeNull()
  })

  it('should keep the preview area empty while the previews load', () => {
    const container = renderSut()

    expect(container.querySelector('img')).toBeNull()
    expect(screen.getByTestId('diagram-card-placeholder')).toBeEmptyDOMElement()
  })
})
