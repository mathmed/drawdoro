import axios from 'axios'

import { authConfig } from '../auth/config'
import { getIdToken } from '../auth/session'
import { useAuthStore } from '../store/useAuthStore'
import { toast } from '../store/useToastStore'

// In dev the app talks to the backend at http://localhost:8000. We default to the
// relative "/api" prefix which is proxied by Vite (see vite.config.ts) to that address,
// keeping the browser same-origin. Override with VITE_API_URL when needed.
const baseURL = import.meta.env.VITE_API_URL ?? '/api'

declare module 'axios' {
  interface AxiosRequestConfig {
    // Background requests the user did not ask for (e.g. diagram previews) fail without a toast.
    silent?: boolean
  }
}

const apiClient = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
})

function describeError(error: unknown): string {
  if (!axios.isAxiosError(error)) {
    return 'Something went wrong.'
  }
  if (error.response === undefined) {
    return 'Could not reach the server. Check that the API is running.'
  }
  const detail: unknown = error.response.data?.detail
  if (typeof detail === 'string') {
    return detail
  }
  return `Request failed (${error.response.status}).`
}

apiClient.interceptors.request.use(async (config) => {
  if (authConfig.enabled) {
    const token = await getIdToken()
    if (token !== null) {
      config.headers.Authorization = `Bearer ${token}`
    }
  }
  return config
})

apiClient.interceptors.response.use(undefined, (error: unknown) => {
  // The session is gone (expired refresh token, user removed): send the user back to sign in.
  if (axios.isAxiosError(error) && error.response?.status === 401 && authConfig.enabled) {
    useAuthStore.getState().signOutLocally()
    return Promise.reject(error)
  }
  // A 404 on a read is an expected "not found yet" answer handled by the caller.
  const isExpectedMiss =
    axios.isAxiosError(error) && error.config?.method === 'get' && error.response?.status === 404
  const isSilent = axios.isAxiosError(error) && error.config?.silent === true
  if (!isExpectedMiss && !isSilent) {
    toast(describeError(error), 'error')
  }
  return Promise.reject(error)
})

export default apiClient
