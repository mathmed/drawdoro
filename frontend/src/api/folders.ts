import apiClient from './client'
import type { Folder } from './types'

export async function listFolders(projectId: string): Promise<Folder[]> {
  const { data } = await apiClient.get<Folder[]>(`/projects/${projectId}/folders`)
  return data
}

export async function createFolder(
  projectId: string,
  name: string,
  parentFolderId?: string,
): Promise<Folder> {
  const { data } = await apiClient.post<Folder>(`/projects/${projectId}/folders`, {
    name,
    parent_folder_id: parentFolderId ?? null,
  })
  return data
}

export async function updateFolder(
  projectId: string,
  folderId: string,
  name: string,
  parentFolderId: string | null,
): Promise<Folder> {
  const { data } = await apiClient.put<Folder>(`/projects/${projectId}/folders/${folderId}`, {
    name,
    parent_folder_id: parentFolderId,
  })
  return data
}

export async function deleteFolder(projectId: string, folderId: string): Promise<void> {
  await apiClient.delete(`/projects/${projectId}/folders/${folderId}`)
}
