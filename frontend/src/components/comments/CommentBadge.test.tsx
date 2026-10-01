import { render, screen } from '@testing-library/react'
import type { Editor } from 'tldraw'
import { beforeEach, describe, expect, it } from 'vitest'

import { useAppStore } from '../../store/useAppStore'
import { makeComment } from '../../test/comments'
import CommentBadge from './CommentBadge'

const editor = {
  store: { listen: () => () => undefined },
  getShapePageBounds: () => ({ maxX: 100, minY: 10 }),
  pageToViewport: (point: { x: number; y: number }) => point,
} as unknown as Editor

beforeEach(() => {
  useAppStore.setState(useAppStore.getInitialState(), true)
})

describe('CommentBadge', () => {
  it('should count only the open comments of each shape', () => {
    useAppStore.setState({
      editor,
      comments: [
        makeComment({ id: '1' }),
        makeComment({ id: '2' }),
        makeComment({ id: '3', resolved: true }),
        makeComment({ id: '4', element_id: null }),
      ],
    })
    render(<CommentBadge />)

    expect(screen.getByRole('button', { name: '2 open comments' })).toBeInTheDocument()
  })

  it('should drop the pin once every comment of the shape is resolved', () => {
    useAppStore.setState({ editor, comments: [makeComment({ resolved: true })] })
    render(<CommentBadge />)

    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })
})
