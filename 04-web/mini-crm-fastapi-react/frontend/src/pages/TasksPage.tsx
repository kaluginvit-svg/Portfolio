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
  FormControlLabel,
  InputLabel,
  MenuItem,
  Select,
  Switch,
  TextField,
  Typography,
} from '@mui/material'
import { DataGrid, type GridColDef, type GridPaginationModel } from '@mui/x-data-grid'
import { useCallback, useEffect, useState } from 'react'
import { api, apiErrorMessage } from '../api/client'
import type { Client, Deal, Paginated, ReportExport, Task } from '../types'

export default function TasksPage() {
  const [rows, setRows] = useState<Task[]>([])
  const [total, setTotal] = useState(0)
  const [clients, setClients] = useState<Client[]>([])
  const [deals, setDeals] = useState<Deal[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [q, setQ] = useState('')
  const [priority, setPriority] = useState('')
  const [doneFilter, setDoneFilter] = useState<'all' | 'yes' | 'no'>('all')
  const [paginationModel, setPaginationModel] = useState<GridPaginationModel>({
    page: 0,
    pageSize: 20,
  })

  const [dialogOpen, setDialogOpen] = useState(false)
  const [editing, setEditing] = useState<Task | null>(null)
  const [form, setForm] = useState({
    title: '',
    description: '',
    due_date: '',
    priority: 'medium',
    done: false,
    client_id: '' as number | '',
    deal_id: '' as number | '',
  })

  const [deleteId, setDeleteId] = useState<number | null>(null)
  const [exportOpen, setExportOpen] = useState(false)
  const [exportRes, setExportRes] = useState<ReportExport | null>(null)

  const loadRefs = useCallback(async () => {
    try {
      const [c, d] = await Promise.all([
        api.get<Paginated<Client>>('/clients', { params: { limit: 500, skip: 0 } }),
        api.get<Paginated<Deal>>('/deals', { params: { limit: 500, skip: 0 } }),
      ])
      setClients(c.data.items)
      setDeals(d.data.items)
    } catch {
      setClients([])
      setDeals([])
    }
  }, [])

  useEffect(() => {
    queueMicrotask(() => {
      void loadRefs()
    })
  }, [loadRefs])

  const fetchList = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const skip = paginationModel.page * paginationModel.pageSize
      const r = await api.get<Paginated<Task>>('/tasks', {
        params: {
          skip,
          limit: paginationModel.pageSize,
          q: q || undefined,
          priority: priority || undefined,
          done:
            doneFilter === 'all' ? undefined : doneFilter === 'yes',
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
  }, [paginationModel, q, priority, doneFilter])

  useEffect(() => {
    queueMicrotask(() => {
      void fetchList()
    })
  }, [fetchList])

  const openCreate = () => {
    setEditing(null)
    setForm({
      title: '',
      description: '',
      due_date: '',
      priority: 'medium',
      done: false,
      client_id: '',
      deal_id: '',
    })
    setDialogOpen(true)
  }

  const openEdit = (t: Task) => {
    setEditing(t)
    setForm({
      title: t.title,
      description: t.description || '',
      due_date: t.due_date || '',
      priority: t.priority,
      done: t.done,
      client_id: t.client_id ?? '',
      deal_id: t.deal_id ?? '',
    })
    setDialogOpen(true)
  }

  const submitForm = async () => {
    setError(null)
    try {
      const payload = {
        title: form.title,
        description: form.description || null,
        due_date: form.due_date || null,
        priority: form.priority,
        done: form.done,
        client_id: form.client_id === '' ? null : form.client_id,
        deal_id: form.deal_id === '' ? null : form.deal_id,
      }
      if (editing) {
        await api.patch(`/tasks/${editing.id}`, payload)
      } else {
        await api.post('/tasks', payload)
      }
      setDialogOpen(false)
      await fetchList()
    } catch (e) {
      setError(apiErrorMessage(e))
    }
  }

  const confirmDelete = async () => {
    if (deleteId == null) return
    try {
      await api.delete(`/tasks/${deleteId}`)
      setDeleteId(null)
      await fetchList()
    } catch (e) {
      setError(apiErrorMessage(e))
    }
  }

  const exportReport = async () => {
    setError(null)
    try {
      const r = await api.post<ReportExport>('/reports/export/tasks')
      setExportRes(r.data)
      setExportOpen(true)
    } catch (e) {
      setError(apiErrorMessage(e))
    }
  }

  const columns: GridColDef<Task>[] = [
    { field: 'id', headerName: 'ID', width: 70 },
    { field: 'title', headerName: 'Задача', flex: 1, minWidth: 160 },
    { field: 'due_date', headerName: 'Срок', width: 110 },
    { field: 'priority', headerName: 'Приоритет', width: 100 },
    { field: 'done', headerName: 'Готово', width: 90, valueGetter: (_, r) => (r.done ? 'да' : 'нет') },
    { field: 'client_id', headerName: 'Клиент_ID', width: 90 },
    { field: 'deal_id', headerName: 'Сделка_ID', width: 90 },
    {
      field: 'actions',
      headerName: '',
      sortable: false,
      width: 110,
      renderCell: (p) => (
        <Box sx={{ display: 'flex', gap: 0.5 }}>
          <Button size="small" onClick={() => openEdit(p.row)}><EditIcon fontSize="small" /></Button>
          <Button size="small" color="error" onClick={() => setDeleteId(p.row.id)}><DeleteIcon fontSize="small" /></Button>
        </Box>
      ),
    },
  ]

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, alignItems: 'center' }}>
        <Typography variant="h5" sx={{ flexGrow: 1, minWidth: 180 }}>Задачи</Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={openCreate}>Новая задача</Button>
        <Button variant="outlined" startIcon={<FileDownloadIcon />} onClick={() => void exportReport()}>Выгрузить отчёт</Button>
      </Box>

      {error && <Alert severity="error">{error}</Alert>}

      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, alignItems: 'center' }}>
        <TextField label="Поиск" size="small" value={q} onChange={(e) => { setQ(e.target.value); setPaginationModel((p) => ({ ...p, page: 0 })) }} />
        <FormControl size="small" sx={{ minWidth: 140 }}>
          <InputLabel>Приоритет</InputLabel>
          <Select label="Приоритет" value={priority} onChange={(e) => { setPriority(String(e.target.value)); setPaginationModel((p) => ({ ...p, page: 0 })) }}>
            <MenuItem value="">Все</MenuItem>
            <MenuItem value="low">low</MenuItem>
            <MenuItem value="medium">medium</MenuItem>
            <MenuItem value="high">high</MenuItem>
          </Select>
        </FormControl>
        <FormControl size="small" sx={{ minWidth: 140 }}>
          <InputLabel>Выполнено</InputLabel>
          <Select label="Выполнено" value={doneFilter} onChange={(e) => {
            setDoneFilter(e.target.value as 'all' | 'yes' | 'no'); setPaginationModel((p) => ({ ...p, page: 0 }))
          }}>
            <MenuItem value="all">Все</MenuItem>
            <MenuItem value="no">Нет</MenuItem>
            <MenuItem value="yes">Да</MenuItem>
          </Select>
        </FormControl>
        <Button variant="text" onClick={() => void fetchList()} disabled={loading}>Обновить</Button>
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
        <DialogTitle>{editing ? 'Задача' : 'Новая задача'}</DialogTitle>
        <DialogContent sx={{ pt: 1 }}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <TextField label="Название" required value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
          <TextField label="Описание" multiline minRows={2} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
          <TextField label="Срок YYYY-MM-DD" value={form.due_date} onChange={(e) => setForm({ ...form, due_date: e.target.value })} />
          <FormControl>
            <InputLabel>Приоритет</InputLabel>
            <Select label="Приоритет" value={form.priority} onChange={(e) => setForm({ ...form, priority: String(e.target.value) })}>
              {['low', 'medium', 'high'].map((x) => <MenuItem key={x} value={x}>{x}</MenuItem>)}
            </Select>
          </FormControl>
          <FormControlLabel control={<Switch checked={form.done} onChange={(e) => setForm({ ...form, done: e.target.checked })} />} label="Выполнено" />
          <FormControl>
            <InputLabel>Клиент</InputLabel>
            <Select label="Клиент" value={form.client_id === '' ? '' : String(form.client_id)} onChange={(e) => {
              const v = e.target.value; setForm({ ...form, client_id: v === '' ? '' : Number(v) })
            }}>
              <MenuItem value="">—</MenuItem>
              {clients.map((c) => <MenuItem key={c.id} value={String(c.id)}>{c.name}</MenuItem>)}
            </Select>
          </FormControl>
          <FormControl>
            <InputLabel>Сделка</InputLabel>
            <Select label="Сделка" value={form.deal_id === '' ? '' : String(form.deal_id)} onChange={(e) => {
              const v = e.target.value; setForm({ ...form, deal_id: v === '' ? '' : Number(v) })
            }}>
              <MenuItem value="">—</MenuItem>
              {deals.map((d) => <MenuItem key={d.id} value={String(d.id)}>{d.title}</MenuItem>)}
            </Select>
          </FormControl>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Отмена</Button>
          <Button variant="contained" disabled={!form.title.trim()} onClick={() => void submitForm()}>Сохранить</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={deleteId !== null} onClose={() => setDeleteId(null)}>
        <DialogTitle>Удалить задачу?</DialogTitle>
        <DialogActions>
          <Button onClick={() => setDeleteId(null)}>Отмена</Button>
          <Button color="error" variant="contained" onClick={() => void confirmDelete()}>Удалить</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={exportOpen} onClose={() => setExportOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>Отчёт создан</DialogTitle>
        <DialogContent>
          <Typography variant="body2" gutterBottom>{exportRes?.title}</Typography>
          <Button component="a" href={exportRes?.url} target="_blank" rel="noopener noreferrer" startIcon={<OpenInNewIcon />}>Открыть</Button>
        </DialogContent>
        <DialogActions>
          <Button startIcon={<ContentCopyIcon />} onClick={() => exportRes && void navigator.clipboard.writeText(exportRes.url)}>Копировать ссылку</Button>
          <Button onClick={() => setExportOpen(false)}>Закрыть</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
