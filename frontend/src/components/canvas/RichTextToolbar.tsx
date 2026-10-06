import type {} from '@tiptap/extension-link'
import { ArrowLeft, Ban, Check, Highlighter, Unlink } from 'lucide-react'
import { useEffect, useState, type ReactNode } from 'react'
import {
  DefaultRichTextToolbar,
  DefaultRichTextToolbarContent,
  TldrawUiToolbarButton,
  useEditor,
  useValue,
  type TiptapEditor,
} from 'tldraw'

const TEXT_COLORS = ['#1e1e1e', '#868e96', '#e03131', '#f08c00', '#2f9e44', '#1971c2', '#6741d9', '#c2255c']
const HIGHLIGHT_COLORS = ['#fff3bf', '#ffe8cc', '#ffe3e3', '#f3d9fa', '#d0ebff', '#d3f9d8', '#e9ecef']

type Mode = 'default' | 'text-color' | 'highlight' | 'link'

// Mark attributes are untyped and tldraw's plain yellow highlight stores `color: null`.
function colorAttr(value: unknown): string | undefined {
  return typeof value === 'string' && value !== '' ? value : undefined
}

function ColorRow({
  colors,
  current,
  label,
  onPick,
  onClear,
  onBack,
}: {
  colors: string[]
  current: string | undefined
  label: string
  onPick: (hex: string) => void
  onClear: () => void
  onBack: () => void
}) {
  return (
    <div className="rt-colors" role="group" aria-label={label}>
      <TldrawUiToolbarButton type="icon" title="Back" onClick={onBack}>
        <ArrowLeft size={15} />
      </TldrawUiToolbarButton>
      <TldrawUiToolbarButton type="icon" title="Default" onClick={onClear}>
        <Ban size={15} />
      </TldrawUiToolbarButton>
      {colors.map((hex) => (
        // tldraw's toolbar button keeps focus (and the text selection) inside the editor.
        <TldrawUiToolbarButton key={hex} type="icon" title={hex} onClick={() => onPick(hex)}>
          <span className="rt-swatch" aria-pressed={current?.toLowerCase() === hex} style={{ background: hex }} />
        </TldrawUiToolbarButton>
      ))}
      <label className="rt-swatch rt-pick" title="Custom color" data-empty={current === undefined || colors.includes(current.toLowerCase())}>
        <input
          type="color"
          aria-label={`Custom ${label.toLowerCase()}`}
          value={current ?? '#1e1e1e'}
          onChange={(event) => onPick(event.target.value)}
        />
      </label>
    </div>
  )
}

function LinkRow({ textEditor, onDone }: { textEditor: TiptapEditor; onDone: () => void }) {
  const [href, setHref] = useState<string>(textEditor.getAttributes('link').href ?? '')

  function apply(): void {
    const value = href.trim()
    const chain = textEditor.chain().focus().extendMarkRange('link')
    if (value === '') {
      chain.unsetLink().run()
    } else {
      chain.setLink({ href: /^[a-z]+:/i.test(value) ? value : `https://${value}` }).run()
    }
    onDone()
  }

  return (
    <div className="rt-colors">
      <input
        className="tlui-rich-text__toolbar-link-input"
        autoFocus
        placeholder="example.com"
        value={href}
        onChange={(event) => setHref(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === 'Enter') {
            event.preventDefault()
            apply()
          }
          if (event.key === 'Escape') {
            event.preventDefault()
            onDone()
          }
        }}
      />
      <TldrawUiToolbarButton type="icon" title="Apply" onClick={apply}>
        <Check size={15} />
      </TldrawUiToolbarButton>
      <TldrawUiToolbarButton
        type="icon"
        title="Remove link"
        onClick={() => {
          textEditor.chain().focus().extendMarkRange('link').unsetLink().run()
          onDone()
        }}
      >
        <Unlink size={15} />
      </TldrawUiToolbarButton>
    </div>
  )
}

function ToolbarContent({ textEditor }: { textEditor: TiptapEditor }) {
  const [mode, setMode] = useState<Mode>('default')
  const [, forceUpdate] = useState(0)

  useEffect(() => {
    const update = () => forceUpdate((value) => value + 1)
    // Clicking into an existing link opens the link editor, like tldraw's own toolbar.
    const handleClick = () => setMode(textEditor.isActive('link') ? 'link' : 'default')
    textEditor.on('selectionUpdate', update)
    textEditor.on('update', update)
    textEditor.view.dom.addEventListener('click', handleClick)
    return () => {
      textEditor.off('selectionUpdate', update)
      textEditor.off('update', update)
      textEditor.view.dom.removeEventListener('click', handleClick)
    }
  }, [textEditor])

  const textColor = colorAttr(textEditor.getAttributes('textStyle').color)
  const highlightColor = colorAttr(textEditor.getAttributes('highlight').color)

  if (mode === 'link') {
    return <LinkRow textEditor={textEditor} onDone={() => setMode('default')} />
  }

  if (mode === 'text-color') {
    return (
      <ColorRow
        colors={TEXT_COLORS}
        current={textColor}
        label="Text color"
        onPick={(hex) => textEditor.chain().focus().setColor(hex).run()}
        onClear={() => textEditor.chain().focus().unsetColor().run()}
        onBack={() => setMode('default')}
      />
    )
  }

  if (mode === 'highlight') {
    return (
      <ColorRow
        colors={HIGHLIGHT_COLORS}
        current={highlightColor}
        label="Highlight color"
        onPick={(hex) => textEditor.chain().focus().setHighlight({ color: hex }).run()}
        onClear={() => textEditor.chain().focus().unsetHighlight().run()}
        onBack={() => setMode('default')}
      />
    )
  }

  const extra: ReactNode[] = [
    <TldrawUiToolbarButton
      key="text-color"
      type="icon"
      title="Text color"
      isActive={textColor !== undefined}
      onClick={() => setMode('text-color')}
    >
      <span className="rt-text-color">
        A
        <span style={{ background: textColor ?? 'currentColor' }} />
      </span>
    </TldrawUiToolbarButton>,
    <TldrawUiToolbarButton
      key="highlight-color"
      type="icon"
      title="Highlight color"
      isActive={highlightColor !== undefined}
      onClick={() => setMode('highlight')}
    >
      <span className="rt-text-color">
        <Highlighter size={14} />
        <span style={{ background: highlightColor ?? '#fff3bf' }} />
      </span>
    </TldrawUiToolbarButton>,
  ]

  return (
    <>
      <DefaultRichTextToolbarContent textEditor={textEditor} onEditLinkStart={() => setMode('link')} />
      {extra}
    </>
  )
}

export default function RichTextToolbar() {
  const editor = useEditor()
  const textEditor = useValue('text editor', () => editor.getRichTextEditor(), [editor])
  if (textEditor === null) {
    return <DefaultRichTextToolbar />
  }
  return (
    <DefaultRichTextToolbar>
      <ToolbarContent key={textEditor.view.dom.id || 'editor'} textEditor={textEditor} />
    </DefaultRichTextToolbar>
  )
}
