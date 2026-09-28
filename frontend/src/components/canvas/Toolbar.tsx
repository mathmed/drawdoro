import {
  ArrowDownToolbarItem,
  ArrowLeftToolbarItem,
  ArrowRightToolbarItem,
  ArrowToolbarItem,
  ArrowUpToolbarItem,
  AssetToolbarItem,
  CheckBoxToolbarItem,
  CloudToolbarItem,
  DefaultToolbar,
  DiamondToolbarItem,
  DrawToolbarItem,
  EllipseToolbarItem,
  EraserToolbarItem,
  FrameToolbarItem,
  HandToolbarItem,
  HeartToolbarItem,
  HexagonToolbarItem,
  HighlightToolbarItem,
  LaserToolbarItem,
  LineToolbarItem,
  NoteToolbarItem,
  OvalToolbarItem,
  RectangleToolbarItem,
  RhombusToolbarItem,
  SelectToolbarItem,
  StarToolbarItem,
  TextToolbarItem,
  TrapezoidToolbarItem,
  TriangleToolbarItem,
  XBoxToolbarItem,
  type TLUiOverrides,
} from 'tldraw'

// Excalidraw-style numbering: the digit comes first so tldraw's tooltip shows it, and the
// original letter shortcut keeps working as the alternative key.
const TOOL_NUMBERS: Record<string, string> = {
  select: '1',
  hand: '2',
  text: '3',
  rectangle: '4',
  arrow: '5',
  line: '6',
  draw: '7',
  laser: '8',
}

export const toolOverrides: TLUiOverrides = {
  tools(_editor, tools) {
    for (const [id, digit] of Object.entries(TOOL_NUMBERS)) {
      const tool = tools[id]
      if (tool !== undefined) {
        tools[id] = { ...tool, kbd: tool.kbd === undefined ? digit : `${digit},${tool.kbd}` }
      }
    }
    return tools
  },
}

export default function Toolbar() {
  return (
    <DefaultToolbar>
      <SelectToolbarItem />
      <HandToolbarItem />
      <TextToolbarItem />
      <RectangleToolbarItem />
      <ArrowToolbarItem />
      <LineToolbarItem />
      <DrawToolbarItem />
      <LaserToolbarItem />
      <EraserToolbarItem />
      <NoteToolbarItem />
      <AssetToolbarItem />
      <EllipseToolbarItem />
      <DiamondToolbarItem />
      <TriangleToolbarItem />
      <HexagonToolbarItem />
      <CloudToolbarItem />
      <OvalToolbarItem />
      <RhombusToolbarItem />
      <TrapezoidToolbarItem />
      <StarToolbarItem />
      <HeartToolbarItem />
      <XBoxToolbarItem />
      <CheckBoxToolbarItem />
      <ArrowLeftToolbarItem />
      <ArrowUpToolbarItem />
      <ArrowDownToolbarItem />
      <ArrowRightToolbarItem />
      <HighlightToolbarItem />
      <FrameToolbarItem />
    </DefaultToolbar>
  )
}
