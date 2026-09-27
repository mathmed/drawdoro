import { useState } from 'react'

import type { Adr, CreateAdrData } from '../../api/types'
import { useAppStore } from '../../store/useAppStore'
import AdrForm from './AdrForm'
import AdrList from './AdrList'

type Mode = { kind: 'list' } | { kind: 'create' } | { kind: 'edit'; adr: Adr }

export default function AdrPanel() {
  const createAdr = useAppStore((state) => state.createAdr)
  const updateAdr = useAppStore((state) => state.updateAdr)
  const [mode, setMode] = useState<Mode>({ kind: 'list' })

  async function handleCreate(data: CreateAdrData): Promise<void> {
    await createAdr(data)
    setMode({ kind: 'list' })
  }

  async function handleUpdate(adrId: string, data: CreateAdrData): Promise<void> {
    await updateAdr(adrId, data)
    setMode({ kind: 'list' })
  }

  if (mode.kind === 'create') {
    return (
      <div style={{ flex: 1, overflow: 'auto' }}>
        <AdrForm onSubmit={handleCreate} onCancel={() => setMode({ kind: 'list' })} />
      </div>
    )
  }

  if (mode.kind === 'edit') {
    return (
      <div style={{ flex: 1, overflow: 'auto' }}>
        <AdrForm
          initial={mode.adr}
          onSubmit={(data) => handleUpdate(mode.adr.id, data)}
          onCancel={() => setMode({ kind: 'list' })}
        />
      </div>
    )
  }

  return (
    <div style={{ flex: 1, overflow: 'auto', display: 'flex', flexDirection: 'column' }}>
      <div style={{ padding: 12, borderBottom: '1px solid #30363d' }}>
        <button
          type="button"
          onClick={() => setMode({ kind: 'create' })}
          style={{
            background: '#2f81f7',
            color: '#e6edf3',
            border: '1px solid #30363d',
            borderRadius: 6,
            padding: '6px 12px',
            fontSize: 13,
            cursor: 'pointer',
            width: '100%',
          }}
        >
          + New ADR
        </button>
      </div>
      <AdrList onEdit={(adr) => setMode({ kind: 'edit', adr })} />
    </div>
  )
}
