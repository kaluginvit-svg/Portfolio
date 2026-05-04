import ContentPasteIcon from '@mui/icons-material/ContentPaste'
import OpenInNewIcon from '@mui/icons-material/OpenInNew'
import {
  Alert,
  Box,
  Button,
  TextField,
  Typography,
} from '@mui/material'
import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api, apiBase, apiErrorMessage } from '../api/client'
import type { GoogleSettings } from '../types'

export default function SettingsPage() {
  const [params] = useSearchParams()
  const google = params.get('google')

  const [data, setData] = useState<GoogleSettings | null>(null)
  const [secretPath, setSecretPath] = useState('')
  const [folderId, setFolderId] = useState('')
  const [tokenPath, setTokenPath] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [saved, setSaved] = useState(false)

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      const r = await api.get<GoogleSettings>('/settings/google')
      setData(r.data)
      setSecretPath(r.data.client_secret_path || '')
      setFolderId(r.data.parent_folder_id || '')
      setTokenPath(r.data.google_token_path || '')
    } catch (e) {
      setError(apiErrorMessage(e))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    queueMicrotask(() => {
      void load()
    })
  }, [])

  const save = async () => {
    setError(null)
    setSaved(false)
    try {
      await api.put('/settings/google', {
        client_secret_path: secretPath,
        parent_folder_id: folderId,
        google_token_path: tokenPath.trim() || null,
      })
      setSaved(true)
      await load()
    } catch (e) {
      setError(apiErrorMessage(e))
    }
  }

  const pasteFolder = async () => {
    try {
      const t = await navigator.clipboard.readText()
      setFolderId(t.trim())
    } catch {
      setError('Не удалось прочитать буфер — разрешите доступ или вставьте вручную')
    }
  }

  const openAuth = async () => {
    setError(null)
    try {
      const r = await api.get<{ authorization_url: string }>('/auth/google/url')
      window.open(r.data.authorization_url, '_blank', 'noopener,noreferrer')
    } catch (e) {
      setError(apiErrorMessage(e))
    }
  }

  return (
    <Box sx={{ maxWidth: 720, display: 'flex', flexDirection: 'column', gap: 2 }}>
      <Typography variant="h5">Настройки Google Drive</Typography>
      <Typography variant="body2" color="text.secondary">
        OAuth JSON (из Google Cloud) положите в проект локально и укажите путь относительно
        корня репозитория (папка с docker-compose.yml) или абсолютный путь. В GCP для redirect URI добавьте:{' '}
        <code>{apiBase}/auth/google/callback</code>
        {' '}(тип приложения OAuth — рекомендуется Web application).
      </Typography>

      {google === 'connected' && (
        <Alert severity="success">Google авторизация сохранена, можно закрыть вкладку.</Alert>
      )}
      {google === 'error' && (
        <Alert severity="error">Ошибка OAuth (см. параметры адреса или лог сервера).</Alert>
      )}

      {error && <Alert severity="error">{error}</Alert>}
      {saved && <Alert severity="success">Настройки сохранены</Alert>}

      {!loading && data && (
        <Alert severity={data.has_valid_token_guess ? 'success' : 'info'}>
          Токен: {data.has_valid_token_guess ? 'похоже, авторизация выполнена' : 'нет — нажмите «Войти через Google»'}
        </Alert>
      )}

      <TextField
        label="Путь к client_secret JSON"
        value={secretPath}
        onChange={(e) => setSecretPath(e.target.value)}
        fullWidth
        disabled={loading}
      />
      <TextField
        label="Путь к файлу OAuth-токена (pickle), опционально"
        helperText="Pickle или JSON (имя .json): пусто — data/google_token.pickle. Для JSON укажите путь, например data/google_token.json. Сохраняется в config/google_settings.json."
        value={tokenPath}
        onChange={(e) => setTokenPath(e.target.value)}
        fullWidth
        disabled={loading}
      />
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, alignItems: 'flex-start' }}>
        <TextField
          label="ID родительской папки Drive"
          value={folderId}
          onChange={(e) => setFolderId(e.target.value)}
          fullWidth
          disabled={loading}
          sx={{ flex: '1 1 240px' }}
        />
        <Button startIcon={<ContentPasteIcon />} variant="outlined" onClick={() => void pasteFolder()}>
          Вставить из буфера
        </Button>
      </Box>

      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
        <Button variant="contained" onClick={() => void save()} disabled={loading}>
          Сохранить настройки
        </Button>
        <Button variant="outlined" startIcon={<OpenInNewIcon />} onClick={() => void openAuth()}>
          Войти через Google
        </Button>
      </Box>
      <Box>
        <Button size="small" onClick={() => void load()} disabled={loading}>
          Обновить статус
        </Button>
      </Box>
    </Box>
  )
}
