import axios from 'axios'

// In dev the app talks to the backend at http://localhost:8000. We default to the
// relative "/api" prefix which is proxied by Vite (see vite.config.ts) to that address,
// keeping the browser same-origin. Override with VITE_API_URL when needed.
const baseURL = import.meta.env.VITE_API_URL ?? '/api'

const apiClient = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export default apiClient
