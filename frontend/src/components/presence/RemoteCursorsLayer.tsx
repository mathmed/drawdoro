import { useContext } from 'react'
import { useEditor } from 'tldraw'

import RemoteCursors from './RemoteCursors'
import { RemoteCursorsContext } from './RemoteCursorsContext'

// Rendered by tldraw in front of the shapes and behind its menus, in editing and presentation alike.
export default function RemoteCursorsLayer() {
  const editor = useEditor()
  const cursors = useContext(RemoteCursorsContext)
  if (cursors === null) {
    return null
  }
  return <RemoteCursors editor={editor} cursors={cursors} />
}
