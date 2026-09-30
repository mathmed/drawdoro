// Stable colour per person so the same collaborator always looks the same.
export function colorFor(id: string): string {
  let hash = 2166136261
  for (const char of id) {
    hash = Math.imul(hash ^ char.charCodeAt(0), 16777619) >>> 0
  }
  // The golden angle spreads hues apart even for near-identical ids.
  return `hsl(${Math.round((hash * 137.508) % 360)} 62% 50%)`
}
