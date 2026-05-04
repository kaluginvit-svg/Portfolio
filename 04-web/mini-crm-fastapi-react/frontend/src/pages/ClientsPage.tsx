import AddIcon from '@mui/icons-material/Add'
import DeleteIcon from '@mui/icons-material/Delete'
import EditIcon from '@mui/icons-material/Edit'
import FileDownloadIcon from '@mui/icons-material/FileDownload'
import ContentCopyIcon from '@mui/icons-material/ContentCopy'
import OpenInNewIcon from '@mui/icons-material/OpenInNew'
import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  TextField,
  Typography,
} from '@mui/material'
import { DataGrid, type GridColDef, type GridPaginationModel } from '@mui/x-data-grid'
import { useCallback, useEffect, useState } from 'react'
import { api, apiErrorMessage } from '../api/client'
import type { Client, Paginated, ReportExport } from '../types'

const emptyClient = {
  name: '',
  email: '',
  phone: '',
  company: '',
  status: 'active' as const,
}

export default function ClientsPage() {
  const [rows, setRows] = useState<Client[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [q, setQ] = useState('')
  const [status, setStatus] = useState<string>('')
  const [paginationModel, setPaginationModel] = useState<GridPaginationModel>({
    page: 0,
    pageSize: 20,
  })

  const [dialogOpen, setDialogOpen] = useState(false)
  const [editing, setEditing] = useState<Client | null>(null)
  const [form, setForm] = useState(emptyClient)

  const [deleteId, setDeleteId] = useState<number | null>(null)

  const [exportOpen, setExportOpen] = useState(false)
  const [exportRes, setExportRes] = useState<ReportExport | null>(null)

  const fetchList = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const skip = paginationModel.page * paginationModel.pageSize
      const r = await api.get<Paginated<Client>>('/clients', {
        params: {
          skip,
          limit: paginationModel.pageSize,
          q: q || undefined,
          status: status || undefined,
        },
      })
      setRows(r.data.items)
      setTotal(r.data.total)
    } catch (e) {
      setError(apiErrorMessage(e))
      setRows([])
    } finally {
      setLoading(false)
    }
  }, [paginationModel, q, status])

  useEffect(() => {
    queueMicrotask(() => {
      void fetchList()
    })
  }, [fetchList])

  const openCreate = () => {
    setEditing(null)
    setForm(emptyClient)
    setDialogOpen(true)
  }

  const openEdit = (c: Client) => {
    setEditing(c)
    setForm({
      name: c.name,
      email: c.email || '',
      phone: c.phone || '',
      company: c.company || '',
      status: c.status as typeof emptyClient.status,
    })
    setDialogOpen(true)
  }

  const submitForm = async () => {
    setError(null)
    try {
      if (editing) {
        await api.patch(`/clients/${editing.id}`, {
          ...form,
          email: form.email || null,
          phone: form.phone || null,
          company: form.company || null,
        })
      } else {
        await api.post('/clients', {
          ...form,
          email: form.email || null,
          phone: form.phone || null,
          company: form.company || null,
        })
      }
      setDialogOpen(false)
      await fetchList()
    } catch (e) {
      setError(apiErrorMessage(e))
    }
  }

  const confirmDelete = async () => {
    if (deleteId == null) return
    setError(null)
    try {
      await api.delete(`/clients/${deleteId}`)
      setDeleteId(null)
      await fetchList()
    } catch (e) {
      setError(apiErrorMessage(e))
    }
  }

  const exportReport = async () => {
    setError(null)
    try {
      const r = await api.post<ReportExport>('/reports/export/clients')
      setExportRes(r.data)
      setExportOpen(true)
    } catch (e) {
      setError(apiErrorMessage(e))
    }
  }

  const columns: GridColDef<Client>[] = [
    { field: 'id', headerName: 'ID', width: 70 },
    { field: 'name', headerName: 'Имя', flex: 1, minWidth: 160 },
    { field: 'email', headerName: 'Email', flex: 1, minWidth: 180 },
    { field: 'phone', headerName: 'Телефон', width: 130 },
    { field: 'company', headerName: 'Компания', flex: 1, minWidth: 140 },
    { field: 'status', headerName: 'Статус', width: 100 },
    {
      field: 'actions',
      headerName: '',
      sortable: false,
      filterable: false,
      width: 120,
      renderCell: (params) => (
        <Box sx={{ display: 'flex', flexDirection: 'row', gap: 0.5 }}>
          <Button size="small" onClick={() => openEdit(params.row)}>
            <EditIcon fontSize="small" />
          </Button>
          <Button size="small" color="error" onClick={() => setDeleteId(params.row.id)}>
            <DeleteIcon fontSize="small" />
          </Button>
        </Box>
      ),
    },
  ]

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, alignItems: 'center' }}>
        <Typography variant="h5" sx={{ flexGrow: 1, minWidth: 200 }}>
          Клиенты
        </Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={openCreate}>
          Новый клиент
        </Button>
        <Button variant="outlined" startIcon={<FileDownloadIcon />} onClick={() => void exportReport()}>
          Выгрузить отчёт
        </Button>
      </Box>

      {error && <Alert severity="error">{error}</Alert>}

      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, alignItems: 'center' }}>
        <TextField
          label="Поиск"
          value={q}
          onChange={(e) => {
            setQ(e.target.value)
            setPaginationModel((p) => ({ ...p, page: 0 }))
          }}
          size="small"
        />
        <FormControl size="small" sx={{ minWidth: 160 }}>
          <InputLabel>Статус</InputLabel>
          <Select
            label="Статус"
            value={status}
            onChange={(e) => {
              setStatus(e.target.value)
              setPaginationModel((p) => ({ ...p, page: 0 }))
            }}
          >
            <MenuItem value="">Все</MenuItem>
            <MenuItem value="active">Активные</MenuItem>
            <MenuItem value="archived">Архив</MenuItem>
          </Select>
        </FormControl>
        <Button variant="text" onClick={() => void fetchList()} disabled={loading}>
          Применить
        </Button>
      </Box>

      <Box sx={{ width: '100%', minHeight: 420 }}>
        <DataGrid
          rows={rows}
          columns={columns}
          loading={loading}
          rowCount={total}
          pageSizeOptions={[10, 20, 50]}
          paginationModel={paginationModel}
          paginationMode="server"
          onPaginationModelChange={setPaginationModel}
          disableRowSelectionOnClick
        />
      </Box>

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>{editing ? 'Редактирование клиента' : 'Новый клиент'}</DialogTitle>
        <DialogContent sx={{ pt: 1 }}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <TextField label="Имя" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
          <TextField label="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} type="email" />
          <TextField label="Телефон" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
          <TextField label="Компания" value={form.company} onChange={(e) => setForm({ ...form, company: e.target.value })} />
          <FormControl>
            <InputLabel>Статус</InputLabel>
            <Select
              label="Статус"
              value={form.status}
              onChange={(e) => setForm({ ...form, status: e.target.value as typeof form.status })}
            >
              <MenuItem value="active">active</MenuItem>
              <MenuItem value="archived">archived</MenuItem>
            </Select>
          </FormControl>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Отмена</Button>
          <Button variant="contained" onClick={() => void submitForm()} disabled={!form.name.trim()}>
            Сохранить
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={deleteId !== null} onClose={() => setDeleteId(null)}>
        <DialogTitle>Удалить клиента?</DialogTitle>
        <DialogActions>
          <Button onClick={() => setDeleteId(null)}>Отмена</Button>
          <Button color="error" variant="contained" onClick={() => void confirmDelete()}>
            Удалить
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={exportOpen} onClose={() => setExportOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>Отчёт создан</DialogTitle>
        <DialogContent>
          <Typography gutterBottom variant="body2">
            Файл: {exportRes?.title}
          </Typography>
          <Button
            component="a"
            href={exportRes?.url}
            target="_blank"
            rel="noopener noreferrer"
            startIcon={<OpenInNewIcon />}
          >
            Открыть в Google Sheets
          </Button>
        </DialogContent>
        <DialogActions>
          <Button
            startIcon={<ContentCopyIcon />}
            onClick={() => exportRes && void navigator.clipboard.writeText(exportRes.url)}
          >
            Копировать ссылку
          </Button>
          <Button onClick={() => setExportOpen(false)}>Закрыть</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
