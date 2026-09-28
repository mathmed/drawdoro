import { useEffect, useRef, useState, type ReactNode } from 'react'

export interface MenuItem {
  kind?: 'item'
  label: string
  icon?: ReactNode
  hint?: string
  danger?: boolean
  checked?: boolean
  onSelect: () => void
}

export type MenuEntry = MenuItem | { kind: 'label'; label: string } | { kind: 'separator' }

interface MenuProps {
  trigger: (props: { open: boolean; toggle: () => void }) => ReactNode
  items: MenuEntry[]
  align?: 'start' | 'end'
  side?: 'top' | 'bottom'
  className?: string
}

export default function Menu({ trigger, items, align = 'start', side = 'bottom', className }: MenuProps) {
  const [open, setOpen] = useState(false)
  const anchorRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) {
      return
    }
    function handlePointerDown(event: MouseEvent): void {
      if (anchorRef.current !== null && !anchorRef.current.contains(event.target as Node)) {
        setOpen(false)
      }
    }
    function handleKeyDown(event: KeyboardEvent): void {
      if (event.key === 'Escape') {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handlePointerDown)
    document.addEventListener('keydown', handleKeyDown)
    return () => {
      document.removeEventListener('mousedown', handlePointerDown)
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [open])

  return (
    <div ref={anchorRef} className={className ?? 'menu-anchor'}>
      {trigger({ open, toggle: () => setOpen((value) => !value) })}
      {open ? (
        <div className="menu" role="menu" data-align={align} data-side={side}>
          {items.map((entry, index) => {
            if (entry.kind === 'separator') {
              return <div key={`separator-${index}`} className="menu-separator" />
            }
            if (entry.kind === 'label') {
              return (
                <div key={`label-${index}`} className="menu-label">
                  {entry.label}
                </div>
              )
            }
            return (
              <button
                key={`${entry.label}-${index}`}
                type="button"
                role={entry.checked === undefined ? 'menuitem' : 'menuitemradio'}
                aria-checked={entry.checked}
                className="menu-item"
                data-danger={entry.danger === true}
                onClick={(event) => {
                  event.stopPropagation()
                  setOpen(false)
                  entry.onSelect()
                }}
              >
                {entry.icon}
                <span>{entry.label}</span>
                {entry.hint !== undefined ? <span className="menu-item-hint">{entry.hint}</span> : null}
              </button>
            )
          })}
        </div>
      ) : null}
    </div>
  )
}
