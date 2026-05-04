import axios from 'axios'

export const apiBase =
  import.meta.env.VITE_API_URL?.replace(/\/$/, '') || 'http://localhost:8000'

export const api = axios.create({
  baseURL: apiBase,
  headers: { 'Content-Type': 'application/json' },
})

export function apiErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err) && err.response?.data) {
    const d = err.response.data as { message?: string; detail?: unknown }
    if (d.message) return d.message
  }
  if (err instanceof Error) return err.message
  return 'Неизвестная ошибка'
}
