import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { createApiKey, listApiKeys, revokeApiKey } from '../../api/apiKeys'
import type { ApiKey } from '../../api/types'
import { confirmDialog } from '../../store/useDialogStore'
import ApiKeysDialog from './ApiKeysDialog'

const authConfig = vi.hoisted(() => ({ enabled: true }))

vi.mock('../../auth/config', () => ({ authConfig }))
vi.mock('../../api/apiKeys')
vi.mock('../../store/useDialogStore', () => ({ confirmDialog: vi.fn() }))

const LAPTOP_KEY: ApiKey = {
  id: 'k1',
  label: 'Claude on my laptop',
  prefix: 'ddk_ab12',
  created_at: '2026-01-01T10:00:00Z',
  last_used_at: null,
}

beforeEach(() => {
  authConfig.enabled = true
  vi.mocked(listApiKeys).mockResolvedValue([LAPTOP_KEY])
})

describe('ApiKeysDialog', () => {
  it('should list the personal keys without their secret', async () => {
    render(<ApiKeysDialog onClose={vi.fn()} />)

    expect(await screen.findByText('Claude on my laptop')).toBeInTheDocument()
    expect(screen.getByText(/never used/)).toBeInTheDocument()
    expect(screen.getByText('ddk_ab12…')).toBeInTheDocument()
  })

  it('should show a new key once, right after creating it', async () => {
    vi.mocked(createApiKey).mockResolvedValue({ ...LAPTOP_KEY, id: 'k2', label: 'Desktop', secret: 'ddk_full_secret' })
    render(<ApiKeysDialog onClose={vi.fn()} />)
    await screen.findByText('Claude on my laptop')

    const input = screen.getByRole('textbox', { name: 'Key label' })
    await userEvent.clear(input)
    await userEvent.type(input, '  Desktop ')
    await userEvent.click(screen.getByRole('button', { name: /Generate key/ }))

    expect(createApiKey).toHaveBeenCalledWith('Desktop')
    const secret = await screen.findByRole('status')
    expect(within(secret).getByRole('textbox', { name: 'New API key' })).toHaveValue('ddk_full_secret')
    expect(screen.getByText('Desktop')).toBeInTheDocument()
  })

  it('should not create a key without a label', async () => {
    render(<ApiKeysDialog onClose={vi.fn()} />)
    await screen.findByText('Claude on my laptop')

    await userEvent.clear(screen.getByRole('textbox', { name: 'Key label' }))

    expect(screen.getByRole('button', { name: /Generate key/ })).toBeDisabled()
  })

  it('should revoke a key after confirmation', async () => {
    vi.mocked(confirmDialog).mockResolvedValue(true)
    vi.mocked(revokeApiKey).mockResolvedValue(undefined)
    render(<ApiKeysDialog onClose={vi.fn()} />)

    await userEvent.click(await screen.findByRole('button', { name: 'Revoke Claude on my laptop' }))

    await waitFor(() => expect(revokeApiKey).toHaveBeenCalledWith('k1'))
    expect(await screen.findByText('No personal keys yet')).toBeInTheDocument()
  })

  it('should keep the key when the revocation is dismissed', async () => {
    vi.mocked(confirmDialog).mockResolvedValue(false)
    render(<ApiKeysDialog onClose={vi.fn()} />)

    await userEvent.click(await screen.findByRole('button', { name: 'Revoke Claude on my laptop' }))

    expect(revokeApiKey).not.toHaveBeenCalled()
    expect(screen.getByText('Claude on my laptop')).toBeInTheDocument()
  })

  it('should explain that personal keys need sign-in when login is disabled', () => {
    authConfig.enabled = false

    render(<ApiKeysDialog onClose={vi.fn()} />)

    expect(screen.getByText(/Personal keys need sign-in/)).toBeInTheDocument()
    expect(listApiKeys).not.toHaveBeenCalled()
  })

  it('should close from the footer', async () => {
    const onClose = vi.fn()
    render(<ApiKeysDialog onClose={onClose} />)

    await userEvent.click(screen.getByRole('button', { name: 'Done' }))

    expect(onClose).toHaveBeenCalledOnce()
  })
})
