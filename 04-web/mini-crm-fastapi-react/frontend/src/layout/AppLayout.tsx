import {
  AppBar,
  Box,
  Button,
  Container,
  Toolbar,
  Typography,
} from '@mui/material'
import { Link as RouterLink, Outlet } from 'react-router-dom'

const linkSx = { color: 'inherit', textDecoration: 'none', mx: 1 }

export default function AppLayout() {
  return (
    <Box sx={{ flexGrow: 1, minHeight: '100vh', bgcolor: 'grey.50' }}>
      <AppBar position="static" color="primary" enableColorOnDark>
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            Мини-CRM (учебный кейс)
          </Typography>
          <Button component={RouterLink} to="/clients" sx={linkSx}>
            Клиенты
          </Button>
          <Button component={RouterLink} to="/deals" sx={linkSx}>
            Сделки
          </Button>
          <Button component={RouterLink} to="/tasks" sx={linkSx}>
            Задачи
          </Button>
          <Button component={RouterLink} to="/settings" sx={linkSx}>
            Настройки Google
          </Button>
        </Toolbar>
      </AppBar>
      <Container maxWidth="xl" sx={{ py: 3 }}>
        <Outlet />
      </Container>
    </Box>
  )
}
