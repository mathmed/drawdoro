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
} from 'tldraw'

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
