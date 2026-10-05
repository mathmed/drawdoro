import { createContext } from 'react'

import type { RemoteCursorStore } from '../../utils/remoteCursors'

// tldraw renders the canvas overlay itself, so the canvas hands it the cursors through context.
export const RemoteCursorsContext = createContext<RemoteCursorStore | null>(null)
