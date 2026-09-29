// Server timestamps order concurrent saves; a missing one never counts as older.
export function isOlder(candidate: string | undefined, current: string | undefined): boolean {
  if (candidate === undefined || current === undefined) {
    return false
  }
  return Date.parse(candidate) < Date.parse(current)
}
