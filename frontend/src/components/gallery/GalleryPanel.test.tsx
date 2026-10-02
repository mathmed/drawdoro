import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { listGalleryItems, updateGalleryItem } from '../../api/gallery'
import { useGalleryStore } from '../../store/useGalleryStore'
import { galleryItem } from '../../test/gallery'
import GalleryPanel from './GalleryPanel'

vi.mock('../../api/gallery')

const LOGO = galleryItem({
  id: 'logo',
  name: 'Kubernetes',
  kind: 'image',
  tags: ['k8s', 'logo', 'cncf', 'orchestration'],
  description: 'The wheel',
})
const QUEUE = galleryItem({ id: 'queue', name: 'Queue <b>bold</b>', tags: ['messaging'] })

beforeEach(() => {
  useGalleryStore.setState({ items: [], status: 'idle', loadedItems: {} })
  vi.mocked(listGalleryItems).mockResolvedValue([LOGO, QUEUE])
})

function tiles(): string[] {
  return screen.queryAllByRole('button', { name: /^Edit / }).map((button) => button.getAttribute('aria-label') ?? '')
}

describe('GalleryPanel', () => {
  it('should show names and tags as plain text', async () => {
    render(<GalleryPanel />)

    expect(await screen.findByText('Queue <b>bold</b>')).toBeInTheDocument()
    expect(document.querySelector('b')).toBeNull()
    expect(screen.getByRole('button', { name: 'k8s' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'orchestration' })).toBeNull()
    expect(screen.getByText('+1')).toHaveAttribute('title', 'orchestration')
  })

  it('should search names, tags and descriptions', async () => {
    render(<GalleryPanel />)
    await screen.findByText('Kubernetes')
    const search = screen.getByRole('textbox', { name: 'Search gallery' })

    await userEvent.type(search, 'messaging')
    expect(tiles()).toEqual(['Edit Queue <b>bold</b>'])

    await userEvent.clear(search)
    await userEvent.type(search, 'wheel')
    expect(tiles()).toEqual(['Edit Kubernetes'])

    await userEvent.type(search, ' kafka')
    expect(screen.getByText('No items match wheel kafka')).toBeInTheDocument()
  })

  it('should filter by a tag clicked on a tile until the filter is cleared', async () => {
    render(<GalleryPanel />)
    await userEvent.click(await screen.findByRole('button', { name: 'messaging' }))

    expect(tiles()).toEqual(['Edit Queue <b>bold</b>'])

    await userEvent.click(screen.getByRole('button', { name: 'Stop filtering by messaging' }))
    expect(tiles()).toHaveLength(2)
  })

  it('should edit the name, tags and description of an item', async () => {
    vi.mocked(updateGalleryItem).mockResolvedValue({ ...QUEUE, tags: ['aws', 'sqs'], description: 'FIFO' })
    render(<GalleryPanel />)
    await userEvent.click(await screen.findByRole('button', { name: 'Edit Queue <b>bold</b>' }))
    const dialog = screen.getByRole('dialog', { name: 'Edit gallery item' })

    await userEvent.clear(within(dialog).getByLabelText('Tags'))
    await userEvent.type(within(dialog).getByLabelText('Tags'), 'AWS, sqs, aws')
    expect(within(dialog).getByLabelText('Tags preview')).toHaveTextContent('awssqs')
    await userEvent.type(within(dialog).getByLabelText('Description'), '  FIFO ')
    await userEvent.click(within(dialog).getByRole('button', { name: 'Save' }))

    expect(updateGalleryItem).toHaveBeenCalledWith('queue', { tags: ['aws', 'sqs'], description: 'FIFO' })
    expect(screen.queryByRole('dialog')).toBeNull()
    expect(await screen.findByRole('button', { name: 'sqs' })).toBeInTheDocument()
  })

  it('should not save invalid or unchanged details', async () => {
    render(<GalleryPanel />)
    await userEvent.click(await screen.findByRole('button', { name: 'Edit Kubernetes' }))
    const dialog = screen.getByRole('dialog', { name: 'Edit gallery item' })
    const save = within(dialog).getByRole('button', { name: 'Save' })

    expect(save).toBeDisabled()
    await userEvent.type(within(dialog).getByLabelText('Tags'), ', <script>')
    expect(within(dialog).getByRole('alert')).toHaveTextContent('unsupported characters')
    expect(save).toBeDisabled()
    await userEvent.clear(within(dialog).getByLabelText('Name'))
    expect(within(dialog).getByRole('alert')).toHaveTextContent('The name is required.')

    await userEvent.click(within(dialog).getByRole('button', { name: 'Cancel' }))
    expect(updateGalleryItem).not.toHaveBeenCalled()
  })

  it('should keep the dialog open when saving fails', async () => {
    vi.mocked(updateGalleryItem).mockRejectedValue(new Error('offline'))
    render(<GalleryPanel />)
    await userEvent.click(await screen.findByRole('button', { name: 'Edit Kubernetes' }))
    const dialog = screen.getByRole('dialog', { name: 'Edit gallery item' })

    await userEvent.type(within(dialog).getByLabelText('Name'), ' logo')
    await userEvent.click(within(dialog).getByRole('button', { name: 'Save' }))

    expect(updateGalleryItem).toHaveBeenCalledWith('logo', { name: 'Kubernetes logo' })
    expect(screen.getByRole('dialog', { name: 'Edit gallery item' })).toBeInTheDocument()
  })
})
