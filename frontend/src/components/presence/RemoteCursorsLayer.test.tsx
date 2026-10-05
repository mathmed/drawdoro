import { render } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { RemoteCursorStore } from '../../utils/remoteCursors'
import RemoteCursorsLayer from './RemoteCursorsLayer'
import { RemoteCursorsContext } from './RemoteCursorsContext'

vi.mock('tldraw', () => ({
  useEditor: () => ({ getCurrentPageId: () => 'page:page', pageToViewport: (point: { x: number; y: number }) => point }),
  useValue: (_name: string, compute: () => unknown) => compute(),
}))

describe('RemoteCursorsLayer', () => {
  it('should draw the cursors the canvas hands it', () => {
    const cursors = new RemoteCursorStore()
    cursors.apply({ id: 'user-ana', name: 'Ana', point: { x: 1, y: 2 }, page: 'page:page' }, Date.now())

    const { container } = render(
      <RemoteCursorsContext.Provider value={cursors}>
        <RemoteCursorsLayer />
      </RemoteCursorsContext.Provider>,
    )

    expect(container.querySelector('[data-cursor-id="user-ana"]')).toHaveTextContent('Ana')
  })

  it('should draw nothing outside a canvas that shares cursors', () => {
    const { container } = render(<RemoteCursorsLayer />)

    expect(container).toBeEmptyDOMElement()
  })
})
