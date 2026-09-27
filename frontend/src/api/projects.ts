import apiClient from './client'
import type { Project } from './types'

export async function listProjects(workspaceId: string): Promise<Project[]> {
  const { data } = await apiClient.get<Project[]>(`/workspaces/${workspaceId}/projects`)
  return data
}

export async function createProject(workspaceId: string, name: string): Promise<Project> {
  const { data } = await apiClient.post<Project>(`/workspaces/${workspaceId}/projects`, { name })
  return data
}
