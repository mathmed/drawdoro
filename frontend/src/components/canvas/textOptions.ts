import Color from '@tiptap/extension-color'
import Highlight from '@tiptap/extension-highlight'
import TextStyle from '@tiptap/extension-text-style'
import { defaultAddFontsFromNode, tipTapDefaultExtensions, type TLTextOptions } from 'tldraw'

// tldraw's highlight is a single yellow mark; multicolor lets each highlight carry its own
// colour, and TextStyle + Color add a text colour mark. Both render as inline styles, so they
// survive saving, realtime sync and SVG/PNG export.
export const textOptions: TLTextOptions = {
  tipTapConfig: {
    extensions: [
      ...tipTapDefaultExtensions.filter((extension) => extension.name !== 'highlight'),
      Highlight.configure({ multicolor: true }),
      TextStyle,
      Color,
    ],
  },
  addFontsFromNode: defaultAddFontsFromNode,
}
