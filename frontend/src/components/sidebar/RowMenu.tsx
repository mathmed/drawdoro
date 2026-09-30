import { MoreHorizontal, Plus } from 'lucide-react'

import Menu, { type MenuEntry } from '../ui/Menu'

export const INDENT = 14

export default function RowMenu({ items, label }: { items: MenuEntry[]; label: 'Add' | 'More' }) {
  return (
    <Menu
      align="end"
      items={items}
      trigger={({ toggle }) => (
        <button
          type="button"
          className="btn btn-ghost btn-icon btn-xs"
          aria-label={label}
          onClick={(event) => {
            event.stopPropagation()
            toggle()
          }}
        >
          {label === 'Add' ? <Plus size={14} /> : <MoreHorizontal size={14} />}
        </button>
      )}
    />
  )
}
