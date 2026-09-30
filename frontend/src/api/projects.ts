import apiClient from './client'
import type { Project, ProjectTree } from './types'

export async function listProjects(workspaceId: string): Promise<Project[]> {
  const { data } = await apiClient.get<Project[]>(`/workspaces/${workspaceId}/projects`)
  return data
}

export async function createProject(workspaceId: string, name: string): Promise<Project> {
  const { data } = await apiClient.post<Project>(`/workspaces/${workspaceId}/projects`, { name })
  return data
}

export async function updateProject(
  workspaceId: string,
  projectId: string,
  name: string,
  description: string,
): Promise<Project> {
  const { data } = await apiClient.put<Project>(`/workspaces/${workspaceId}/projects/${projectId}`, {
    name,
    description,
  })
  return data
}

export async function deleteProject(workspaceId: string, projectId: string): Promise<void> {
  await apiClient.delete(`/workspaces/${workspaceId}/projects/${projectId}`)
}

// Folders and diagram summaries in one round trip, for the sidebar tree.
export async function getProjectTree(projectId: string): Promise<ProjectTree> {
  const { data } = await apiClient.get<ProjectTree>(`/projects/${projectId}/tree`)
  return data
}
