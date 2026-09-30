import { describe, expect, it } from 'vitest'

import cjsSource from '../../../node_modules/tldraw/dist-cjs/lib/ui/components/ContextMenu/DefaultContextMenu.js?raw'
import esmSource from '../../../node_modules/tldraw/dist-esm/lib/ui/components/ContextMenu/DefaultContextMenu.mjs?raw'

// tldraw's menu click capture closes menus through the editor only. With an uncontrolled Radix root
// the context menu opened once and then ignored every right-click until a reload, so
// patches/tldraw+*.patch makes the root follow the editor state. This guards a tldraw upgrade or a
// patch that no longer applies.
describe('tldraw context menu patch', () => {
  it.each([
    ['esm', esmSource],
    ['cjs', cjsSource],
  ])('should keep the %s context menu root controlled by the editor menu state', (_build, source) => {
    expect(source).toMatch(/ContextMenu\.Root, \{ dir: "ltr", open: isOpen, onOpenChange: handleOpenChange/)
  })
})
