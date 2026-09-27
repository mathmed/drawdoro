import type { AdrStatus } from '../../api/types'

export const ADR_STATUSES: AdrStatus[] = ['proposed', 'accepted', 'deprecated', 'superseded']

export const ADR_STATUS_COLORS: Record<AdrStatus, string> = {
  proposed: '#d29922',
  accepted: '#2ea043',
  deprecated: '#8b949e',
  superseded: '#db6d28',
}
