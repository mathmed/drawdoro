import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { ListSkeleton, Skeleton, SkeletonGroup } from './Skeleton'

describe('Skeleton', () => {
  it('should hide the placeholder blocks from assistive tech', () => {
    const { container } = render(<Skeleton width={40} height={12} radius="50%" className="extra" />)

    const block = container.querySelector('.skeleton')
    expect(block).toHaveAttribute('aria-hidden', 'true')
    expect(block).toHaveClass('extra')
    expect(block).toHaveStyle({ width: '40px', height: '12px', borderRadius: '50%' })
  })

  it('should announce what is loading instead of the blocks', () => {
    render(
      <SkeletonGroup label="Loading gallery">
        <Skeleton />
      </SkeletonGroup>,
    )

    const status = screen.getByRole('status')
    expect(status).toHaveTextContent('Loading gallery')
    expect(status.querySelector('.skeleton-group-body')).toHaveAttribute('aria-hidden', 'true')
  })

  it('should draw one row per item with the requested avatar and lines', () => {
    const { container } = render(<ListSkeleton label="Loading history" rows={3} lines={3} avatar="square" />)

    expect(screen.getByRole('status')).toHaveTextContent('Loading history')
    const rows = container.querySelectorAll('.list-skeleton-row')
    expect(rows).toHaveLength(3)
    expect(rows[0].querySelectorAll('.skeleton-line')).toHaveLength(3)
    expect(rows[0].querySelector('.list-skeleton-avatar')).toHaveStyle({ borderRadius: 'var(--radius-sm)' })
  })

  it('should leave the avatar out when asked', () => {
    const { container } = render(<ListSkeleton label="Loading" avatar="none" />)

    expect(container.querySelectorAll('.list-skeleton-row')).toHaveLength(4)
    expect(container.querySelector('.list-skeleton-avatar')).toBeNull()
  })
})
