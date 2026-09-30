import type { DiagramSummary, Folder } from '../../api/types'

// Children grouped by parent once per tree change, instead of filtering the whole list
// for every folder on every render. The null key is the project root.
export interface TreeIndex {
  folders: Map<string | null, Folder[]>
  diagrams: Map<string | null, DiagramSummary[]>
}

function groupBy<T extends { name: string }>(items: T[], key: (item: T) => string | null): Map<string | null, T[]> {
  const groups = new Map<string | null, T[]>()
  for (const item of items) {
    const group = groups.get(key(item))
    if (group === undefined) {
      groups.set(key(item), [item])
    } else {
      group.push(item)
    }
  }
  for (const group of groups.values()) {
    group.sort((a, b) => a.name.localeCompare(b.name))
  }
  return groups
}

export function buildTreeIndex(folders: Folder[], diagrams: DiagramSummary[]): TreeIndex {
  return {
    folders: groupBy(folders, (folder) => folder.parent_folder_id),
    diagrams: groupBy(diagrams, (diagram) => diagram.folder_id),
  }
}

export function folderAncestors(folders: Folder[], folderId: string | null): string[] {
  const byId = new Map(folders.map((folder) => [folder.id, folder]))
  const ancestors: string[] = []
  let current = folderId === null ? undefined : byId.get(folderId)
  // The visited check guards against a cycle in bad data.
  while (current !== undefined && !ancestors.includes(current.id)) {
    ancestors.push(current.id)
    current = current.parent_folder_id === null ? undefined : byId.get(current.parent_folder_id)
  }
  return ancestors
}
