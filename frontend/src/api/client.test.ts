import { AxiosError, type AxiosAdapter, type InternalAxiosRequestConfig } from 'axios'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useToastStore } from '../store/useToastStore'
import apiClient from './client'

vi.mock('../auth/config', () => ({ authConfig: { enabled: false } }))

function failing(status: number): AxiosAdapter {
  return async (config: InternalAxiosRequestConfig) => {
    throw new AxiosError('failed', 'ERR_BAD_RESPONSE', config, null, {
      status,
      statusText: 'Error',
      headers: {},
      config,
      data: { detail: 'This action requires the editor role' },
    })
  }
}

beforeEach(() => {
  useToastStore.setState({ toasts: [] })
})

describe('apiClient errors', () => {
  it('should tell the user when a request fails', async () => {
    await expect(apiClient.put('/diagrams/d1/thumbnail', {}, { adapter: failing(403) })).rejects.toThrow()

    expect(useToastStore.getState().toasts.map((toast) => toast.message)).toEqual([
      'This action requires the editor role',
    ])
  })

  it('should fail a silent background request without a toast', async () => {
    await expect(
      apiClient.put('/diagrams/d1/thumbnail', {}, { adapter: failing(403), silent: true }),
    ).rejects.toThrow()

    expect(useToastStore.getState().toasts).toEqual([])
  })
})
