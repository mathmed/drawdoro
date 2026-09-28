const UNITS: [Intl.RelativeTimeFormatUnit, number][] = [
  ['year', 365 * 24 * 3600],
  ['month', 30 * 24 * 3600],
  ['week', 7 * 24 * 3600],
  ['day', 24 * 3600],
  ['hour', 3600],
  ['minute', 60],
]

const relativeFormatter = new Intl.RelativeTimeFormat('en', { numeric: 'auto' })

export function timeAgo(value: string | undefined): string {
  if (value === undefined) {
    return ''
  }
  // The API returns naive UTC timestamps; without a zone the browser would read them as local time.
  const hasZone = /(z|[+-]\d{2}:?\d{2})$/i.test(value)
  const seconds = (new Date(hasZone ? value : `${value}Z`).getTime() - Date.now()) / 1000
  for (const [unit, size] of UNITS) {
    if (Math.abs(seconds) >= size) {
      return relativeFormatter.format(Math.round(seconds / size), unit)
    }
  }
  return 'just now'
}

export function slugify(value: string): string {
  return value
    .toLowerCase()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .trim()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
}

export function initial(value: string | undefined): string {
  return (value ?? '?').trim().charAt(0).toUpperCase() || '?'
}

export const isMac = /mac|iphone|ipad/i.test(navigator.platform)

export const modKey = isMac ? '⌘' : 'Ctrl'
