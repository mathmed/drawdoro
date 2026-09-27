import apiClient from './client'
import type { Workspace } from './types'

export async function listWorkspaces(): Promise<Workspace[]> {
  const { data } = await apiClient.get<Workspace[]>('/workspaces')
  return data
}

export async function createWorkspace(name: string, slug: string): Promise<Workspace> {
  const { data } = await apiClient.post<Workspace>('/workspaces', { name, slug })
  return data
}
