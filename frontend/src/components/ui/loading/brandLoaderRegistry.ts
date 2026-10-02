// A loader that replaces another one within this window takes over at once, without its own appear
// delay, so a hand-off (e.g. the stage loader giving way to the canvas's font loading) looks seamless.
export const BRAND_LOADER_HANDOFF_MS = 400

let mountedCount = 0
let lastUnmountedAt = Number.NEGATIVE_INFINITY

export function registerBrandLoader(): () => void {
  mountedCount += 1
  return () => {
    mountedCount -= 1
    lastUnmountedAt = Date.now()
  }
}

export function isBrandLoaderOnScreen(): boolean {
  return mountedCount > 0 || Date.now() - lastUnmountedAt < BRAND_LOADER_HANDOFF_MS
}
