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
import type { Client, Deal, Paginated, ReportExport } from '../types'

export default function DealsPage() {
  const [rows, setRows] = useState<Deal[]>([])
  const [total, setTotal] = useState(0)
  const [clients, setClients] = useState<Client[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [q, setQ] = useState('')
  const [stage, setStage] = useState('')
  const [paginationModel, setPaginationModel] = useState<GridPaginationModel>({
    page: 0,
    pageSize: 20,
  })

  const [dialogOpen, setDialogOpen] = useState(false)
  const [editing, setEditing] = useState<Deal | null>(null)
  const [form, setForm] = useState({
    title: '',
    amount: '0',
    currency: 'RUB',
    stage: 'lead',
    client_id: '' as number | '',
    opened_at: '',
    expected_close: '',
  })

  const [deleteId, setDeleteId] = useState<number | null>(null)
  const [exportOpen, setExportOpen] = useState(false)
  const [exportRes, setExportRes] = useState<ReportExport | null>(null)

  const loadClients = useCallback(async () => {
    try {
      const r = await api.get<Paginated<Client>>('/clients', { params: { limit: 500, skip: 0 } })
      setClients(r.data.items)
    } catch {
      setClients([])
    }
  }, [])

  useEffect(() => {
    queueMicrotask(() => {
      void loadClients()
    })
  }, [loadClients])

  const fetchList = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const skip = paginationModel.page * paginationModel.pageSize
      const r = await api.get<Paginated<Deal>>('/deals', {
        params: {
          skip,
          limit: paginationModel.pageSize,
          q: q || undefined,
          stage: stage || undefined,
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
  }, [paginationModel, q, stage])

  useEffect(() => {
    queueMicrotask(() => {
      void fetchList()
    })
  }, [fetchList])

  const openCreate = () => {
    setEditing(null)
    setForm({
      title: '',
      amount: '0',
      currency: 'RUB',
      stage: 'lead',
      client_id: '',
      opened_at: '',
      expected_close: '',
    })
    setDialogOpen(true)
  }

  const openEdit = (d: Deal) => {
    setEditing(d)
    setForm({
      title: d.title,
      amount: String(d.amount),
      currency: d.currency,
      stage: d.stage,
      client_id: d.client_id ?? '',
      opened_at: d.opened_at ?? '',
      expected_close: d.expected_close ?? '',
    })
    setDialogOpen(true)
  }

  const submitForm = async () => {
    setError(null)
    try {
      const payload = {
        title: form.title,
        amount: Number(form.amount),
        currency: form.currency,
        stage: form.stage,
        client_id: form.client_id === '' ? null : form.client_id,
        opened_at: form.opened_at || null,
        expected_close: form.expected_close || null,
      }
      if (editing) {
        await api.patch(`/deals/${editing.id}`, payload)
      } else {
        await api.post('/deals', payload)
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
      await api.delete(`/deals/${deleteId}`)
      setDeleteId(null)
      await fetchList()
    } catch (e) {
      setError(apiErrorMessage(e))
    }
  }

  const exportReport = async () => {
    setError(null)
    try {
      const r = await api.post<ReportExport>('/reports/export/deals')
      setExportRes(r.data)
      setExportOpen(true)
    } catch (e) {
      setError(apiErrorMessage(e))
    }
  }

  const columns: GridColDef<Deal>[] = [
    { field: 'id', headerName: 'ID', width: 70 },
    { field: 'title', headerName: 'Сделка', flex: 1, minWidth: 180 },
    {
      field: 'amount',
      headerName: 'Сумма',
      width: 120,
      valueGetter: (_, row) =>
        `${row.amount} ${row.currency}`,
    },
    { field: 'stage', headerName: 'Стадия', width: 110 },
    { field: 'client_id', headerName: 'Клиент_ID', width: 100 },
    {
      field: 'actions',
      headerName: '',
      sortable: false,
      width: 110,
      renderCell: (p) => (
        <Box sx={{ display: 'flex', flexDirection: 'row', gap: 0.5 }}>
          <Button size="small" onClick={() => openEdit(p.row)}>
            <EditIcon fontSize="small" />
          </Button>
          <Button size="small" color="error" onClick={() => setDeleteId(p.row.id)}>
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
          Сделки
        </Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={openCreate}>
          Новая сделка
        </Button>
        <Button variant="outlined" startIcon={<FileDownloadIcon />} onClick={() => void exportReport()}>
          Выгрузить отчёт
        </Button>
      </Box>

      {error && <Alert severity="error">{error}</Alert>}

      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, alignItems: 'center' }}>
        <TextField
          label="Поиск по названию"
          value={q}
          size="small"
          onChange={(e) => {
            setQ(e.target.value)
            setPaginationModel((p) => ({ ...p, page: 0 }))
          }}
        />
        <FormControl size="small" sx={{ minWidth: 160 }}>
          <InputLabel>Стадия</InputLabel>
          <Select label="Стадия" value={stage} onChange={(e) => { setStage(e.target.value); setPaginationModel((p) => ({ ...p, page: 0 })) }}>
            <MenuItem value="">Все</MenuItem>
            {['lead', 'qualified', 'proposal', 'won', 'lost'].map((s) => (
              <MenuItem key={s} value={s}>{s}</MenuItem>
            ))}
          </Select>
        </FormControl>
        <Button variant="text" onClick={() => void fetchList()} disabled={loading}>
          Обновить
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
        <DialogTitle>{editing ? 'Сделка' : 'Новая сделка'}</DialogTitle>
        <DialogContent sx={{ pt: 1 }}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <TextField label="Название" required value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
          <TextField label="Сумма" type="number" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} />
          <TextField label="Валюта" value={form.currency} onChange={(e) => setForm({ ...form, currency: e.target.value })} />
          <FormControl>
            <InputLabel>Стадия</InputLabel>
            <Select label="Стадия" value={form.stage} onChange={(e) => setForm({ ...form, stage: String(e.target.value) })}>
              {['lead', 'qualified', 'proposal', 'won', 'lost'].map((s) => (
                <MenuItem key={s} value={s}>{s}</MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormControl>
            <InputLabel>Клиент</InputLabel>
            <Select label="Клиент" value={form.client_id === '' ? '' : String(form.client_id)} onChange={(e) => {
              const v = e.target.value
              setForm({ ...form, client_id: v === '' ? '' : Number(v) })
            }}>
              <MenuItem value="">— нет —</MenuItem>
              {clients.map((c) => (
                <MenuItem key={c.id} value={String(c.id)}>{c.name}</MenuItem>
              ))}
            </Select>
          </FormControl>
          <TextField label="Открыта (YYYY-MM-DD)" value={form.opened_at} onChange={(e) => setForm({ ...form, opened_at: e.target.value })} />
          <TextField label="Ожид. закрытие (YYYY-MM-DD)" value={form.expected_close} onChange={(e) => setForm({ ...form, expected_close: e.target.value })} />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Отмена</Button>
          <Button variant="contained" onClick={() => void submitForm()} disabled={!form.title.trim()}>
            Сохранить
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={deleteId !== null} onClose={() => setDeleteId(null)}>
        <DialogTitle>Удалить сделку?</DialogTitle>
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
