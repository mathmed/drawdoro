import axios from 'axios'

import apiClient from './client'
import type { DocumentationPage } from './types'

// Returns null when the diagram has no documentation page yet (backend answers 404).
export async function getDocumentation(diagramId: string): Promise<DocumentationPage | null> {
  try {
    const { data } = await apiClient.get<DocumentationPage>(
      `/diagrams/${diagramId}/documentation`,
    )
    return data
  } catch (error) {
    if (axios.isAxiosError(error) && error.response?.status === 404) {
      return null
    }
    throw error
  }
}

export async function upsertDocumentation(
  diagramId: string,
  content: string,
): Promise<DocumentationPage> {
  const { data } = await apiClient.put<DocumentationPage>(
    `/diagrams/${diagramId}/documentation`,
    { content },
  )
  return data
}
