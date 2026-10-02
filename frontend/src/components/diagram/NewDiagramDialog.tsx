import { FilePlus2 } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'

import { useAppStore } from '../../store/useAppStore'
import Spinner from '../ui/loading/Spinner'
import Modal from '../ui/Modal'

export default function NewDiagramDialog({ initialFolderId }: { initialFolderId?: string }) {
  const navigate = useNavigate()
  const folders = useAppStore((state) => state.folders)
  const createDiagram = useAppStore((state) => state.createDiagram)
  const setActiveDiagram = useAppStore((state) => state.setActiveDiagram)
  const closeNewDiagram = useAppStore((state) => state.closeNewDiagram)

  const [name, setName] = useState('')
  const [folderId, setFolderId] = useState(initialFolderId ?? '')
  const [isCreating, setIsCreating] = useState(false)

  async function handleSubmit(event: FormEvent): Promise<void> {
    event.preventDefault()
    setIsCreating(true)
    try {
      const diagram = await createDiagram(name.trim() || 'Untitled diagram', folderId === '' ? undefined : folderId)
      if (diagram === null) {
        return
      }
      await setActiveDiagram(diagram)
      navigate(`/diagrams/${diagram.id}`)
      closeNewDiagram()
    } finally {
      setIsCreating(false)
    }
  }

  return (
    <Modal
      title="New diagram"
      onClose={closeNewDiagram}
      footer={
        <>
          <button type="button" className="btn btn-secondary" onClick={closeNewDiagram}>
            Cancel
          </button>
          <button type="submit" form="new-diagram-form" className="btn btn-primary" disabled={isCreating} aria-busy={isCreating}>
            {isCreating ? <Spinner size={15} /> : <FilePlus2 size={15} />} Create diagram
          </button>
        </>
      }
    >
      <form id="new-diagram-form" onSubmit={(event) => void handleSubmit(event)} style={{ display: 'contents' }}>
        <div className="field">
          <label className="field-label" htmlFor="new-diagram-name">
            Name
          </label>
          <input
            id="new-diagram-name"
            className="input"
            autoFocus
            value={name}
            placeholder="e.g. Checkout flow"
            onChange={(event) => setName(event.target.value)}
          />
        </div>
        {folders.length > 0 ? (
          <div className="field">
            <label className="field-label" htmlFor="new-diagram-folder">
              Folder
            </label>
            <select
              id="new-diagram-folder"
              className="select"
              value={folderId}
              onChange={(event) => setFolderId(event.target.value)}
            >
              <option value="">Project root</option>
              {folders.map((folder) => (
                <option key={folder.id} value={folder.id}>
                  {folder.name}
                </option>
              ))}
            </select>
          </div>
        ) : null}
      </form>
    </Modal>
  )
}
