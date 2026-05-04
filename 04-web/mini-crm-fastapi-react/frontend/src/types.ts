export type Client = {
  id: number
  name: string
  email: string | null
  phone: string | null
  company: string | null
  status: string
  created_at: string
  updated_at: string
}

export type Deal = {
  id: number
  title: string
  amount: string | number
  currency: string
  stage: string
  client_id: number | null
  opened_at: string | null
  expected_close: string | null
  created_at: string
  updated_at: string
}

export type Task = {
  id: number
  title: string
  description: string | null
  due_date: string | null
  priority: string
  done: boolean
  client_id: number | null
  deal_id: number | null
  created_at: string
  updated_at: string
}

export type Paginated<T> = {
  total: number
  skip: number
  limit: number
  items: T[]
}

export type GoogleSettings = {
  client_secret_path: string | null
  parent_folder_id: string | null
  /** Если null — используется путь из переменной окружения / data/google_token.pickle */
  google_token_path: string | null
  has_valid_token_guess: boolean
}

export type ReportExport = {
  file_id: string
  url: string
  title: string
}
