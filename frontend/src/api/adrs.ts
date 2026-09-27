import apiClient from './client'
import type { Adr, CreateAdrData } from './types'

export async function listAdrs(diagramId: string): Promise<Adr[]> {
  const { data } = await apiClient.get<Adr[]>(`/diagrams/${diagramId}/adrs`)
  return data
}

export async function createAdr(diagramId: string, input: CreateAdrData): Promise<Adr> {
  const { data } = await apiClient.post<Adr>(`/diagrams/${diagramId}/adrs`, input)
  return data
}

export async function updateAdr(
  diagramId: string,
  adrId: string,
  input: CreateAdrData,
): Promise<Adr> {
  const { data } = await apiClient.put<Adr>(`/diagrams/${diagramId}/adrs/${adrId}`, input)
  return data
}

export async function deleteAdr(diagramId: string, adrId: string): Promise<void> {
  await apiClient.delete(`/diagrams/${diagramId}/adrs/${adrId}`)
}
