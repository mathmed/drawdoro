import apiClient from './client'
import type { ApiKey, CreatedApiKey } from './types'

export async function listApiKeys(): Promise<ApiKey[]> {
  const { data } = await apiClient.get<ApiKey[]>('/me/api-keys')
  return data
}

export async function createApiKey(label: string): Promise<CreatedApiKey> {
  const { data } = await apiClient.post<CreatedApiKey>('/me/api-keys', { label })
  return data
}

export async function revokeApiKey(keyId: string): Promise<void> {
  await apiClient.delete(`/me/api-keys/${keyId}`)
}
