import type { Adr, AdrStatus } from '../../api/types'
import { useAppStore } from '../../store/useAppStore'
import { ADR_STATUS_COLORS, ADR_STATUSES } from './adrStatus'

interface AdrListProps {
  onEdit: (adr: Adr) => void
}

export default function AdrList({ onEdit }: AdrListProps) {
  const adrs = useAppStore((state) => state.adrs)
  const updateAdrStatus = useAppStore((state) => state.updateAdrStatus)
  const deleteAdr = useAppStore((state) => state.deleteAdr)

  if (adrs.length === 0) {
    return (
      <div style={{ padding: 16, color: '#8b949e', fontSize: 13 }}>No ADRs yet.</div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8, padding: 12 }}>
      {adrs.map((adr) => (
        <div
          key={adr.id}
          style={{
            background: '#0f1117',
            border: '1px solid #30363d',
            borderRadius: 8,
            padding: 10,
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: 8,
            }}
          >
            <span style={{ fontSize: 13, fontWeight: 600 }}>{adr.title}</span>
            <span
              style={{
                fontSize: 11,
                fontWeight: 600,
                color: '#0f1117',
                background: ADR_STATUS_COLORS[adr.status],
                borderRadius: 12,
                padding: '2px 8px',
                textTransform: 'capitalize',
              }}
            >
              {adr.status}
            </span>
          </div>
          {adr.context !== '' ? (
            <p style={{ fontSize: 12, color: '#8b949e', margin: '6px 0 0' }}>{adr.context}</p>
          ) : null}
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 8 }}>
            <select
              value={adr.status}
              onChange={(e) => void updateAdrStatus(adr.id, e.target.value as AdrStatus)}
              style={{
                background: '#161b22',
                color: '#e6edf3',
                border: '1px solid #30363d',
                borderRadius: 6,
                padding: '3px 6px',
                fontSize: 12,
              }}
            >
              {ADR_STATUSES.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
            <button
              type="button"
              onClick={() => onEdit(adr)}
              style={{
                background: '#21262d',
                color: '#e6edf3',
                border: '1px solid #30363d',
                borderRadius: 6,
                padding: '3px 10px',
                fontSize: 12,
                cursor: 'pointer',
              }}
            >
              Edit
            </button>
            <button
              type="button"
              onClick={() => void deleteAdr(adr.id)}
              style={{
                background: '#21262d',
                color: '#f85149',
                border: '1px solid #30363d',
                borderRadius: 6,
                padding: '3px 10px',
                fontSize: 12,
                cursor: 'pointer',
              }}
            >
              Delete
            </button>
          </div>
        </div>
      ))}
    </div>
  )
}
