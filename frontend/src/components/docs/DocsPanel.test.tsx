import { act, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import type { Diagram } from '../../api/types'
import { useAppStore } from '../../store/useAppStore'
import { pastLoaderDelay, pastLoaderExit } from '../../test/timers'
import DocsPanel from './DocsPanel'

vi.mock('../../store/useThemeStore', () => ({
  useThemeStore: (select: (state: { resolved: string }) => unknown) => select({ resolved: 'light' }),
}))
vi.mock('@uiw/react-md-editor', () => {
  const Editor = ({ value }: { value: string }) => <textarea aria-label="Documentation" value={value} readOnly />
  Editor.Markdown = ({ source }: { source: string }) => <div>{source}</div>
  return { default: Editor, commands: {} }
})

const DIAGRAM: Diagram = { id: 'd1', project_id: 'p1', folder_id: null, name: 'Checkout', canvas_state: null, updated_at: '2026-01-01T10:00:00Z' }

describe('DocsPanel', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    useAppStore.setState(useAppStore.getInitialState(), true)
    useAppStore.setState({ activeDiagram: DIAGRAM })
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('should hide the editor behind a skeleton until the page arrives', async () => {
    useAppStore.setState({ isLoadingDiagramDetails: true })
    render(<DocsPanel />)
    expect(screen.queryByRole('textbox', { name: 'Documentation' })).not.toBeInTheDocument()

    await pastLoaderDelay()
    expect(screen.getByRole('status')).toHaveTextContent('Loading documentation')

    act(() =>
      useAppStore.setState({
        isLoadingDiagramDetails: false,
        documentation: { id: 'doc', diagram_id: 'd1', content: '# Checkout' } as never,
      }),
    )
    await pastLoaderExit()
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
    expect(screen.getByRole('textbox', { name: 'Documentation' })).toHaveValue('# Checkout')
  })

  it('should open the editor at once for a diagram without documentation', () => {
    render(<DocsPanel />)

    expect(screen.getByRole('textbox', { name: 'Documentation' })).toHaveValue('')
  })
})
