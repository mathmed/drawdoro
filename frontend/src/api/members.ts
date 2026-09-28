import apiClient from './client'
import type { WorkspaceMember, WorkspaceRole } from './types'

export async function listMembers(workspaceId: string): Promise<WorkspaceMember[]> {
  const { data } = await apiClient.get<WorkspaceMember[]>(`/workspaces/${workspaceId}/members`)
  return data
}

export async function addMember(workspaceId: string, email: string, role: WorkspaceRole): Promise<WorkspaceMember> {
  const { data } = await apiClient.post<WorkspaceMember>(`/workspaces/${workspaceId}/members`, { email, role })
  return data
}

export async function updateMemberRole(workspaceId: string, userId: string, role: WorkspaceRole): Promise<void> {
  await apiClient.put(`/workspaces/${workspaceId}/members/${userId}`, { role })
}

export async function removeMember(workspaceId: string, userId: string): Promise<void> {
  await apiClient.delete(`/workspaces/${workspaceId}/members/${userId}`)
}
