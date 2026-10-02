import { act, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { shareDiagram } from '../../api/diagrams'
import { pastLoaderDelay, pastLoaderExit } from '../../test/timers'
import ShareDialog from './ShareDialog'

vi.mock('../../api/diagrams', () => ({ shareDiagram: vi.fn() }))

describe('ShareDialog', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('should keep the room of the link, show a placeholder row, then the link', async () => {
    let resolve!: (token: string) => void
    vi.mocked(shareDiagram).mockReturnValue(new Promise((done) => (resolve = done)))
    render(<ShareDialog diagramId="d1" onClose={vi.fn()} />)
    expect(document.querySelector('.share-link-placeholder')).not.toBeNull()

    await pastLoaderDelay()
    expect(screen.getByRole('status')).toHaveTextContent('Generating link')

    await act(async () => resolve('token-1'))
    await pastLoaderExit()
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
    expect(screen.getByRole('textbox')).toHaveValue(`${window.location.origin}/share/token-1`)
  })
})
