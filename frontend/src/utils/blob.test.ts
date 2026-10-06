import { describe, expect, it, vi } from 'vitest'

import { blobToBase64 } from './blob'

function failingReader(error: DOMException | null): typeof FileReader {
  return class {
    error = error
    onerror: (() => void) | null = null
    readAsDataURL(): void {
      queueMicrotask(() => this.onerror?.())
    }
  } as unknown as typeof FileReader
}

describe('blobToBase64', () => {
  it('should return the base64 payload without the data URL prefix', async () => {
    await expect(blobToBase64(new Blob(['hello'], { type: 'text/plain' }))).resolves.toBe('aGVsbG8=')
  })

  it('should return nothing for an empty blob', async () => {
    await expect(blobToBase64(new Blob([]))).resolves.toBe('')
  })

  it('should reject with the reader error', async () => {
    const error = new DOMException('denied', 'NotReadableError')
    vi.stubGlobal('FileReader', failingReader(error))

    await expect(blobToBase64(new Blob(['x']))).rejects.toBe(error)
  })

  it('should reject with a generic error when the reader gives none', async () => {
    vi.stubGlobal('FileReader', failingReader(null))

    await expect(blobToBase64(new Blob(['x']))).rejects.toThrow('Could not read the file')
  })
})
