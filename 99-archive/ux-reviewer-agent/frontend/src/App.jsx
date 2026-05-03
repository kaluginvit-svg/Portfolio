import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import axios from 'axios'

const getApiBase = () => {
  if (import.meta.env.VITE_API_URL) return import.meta.env.VITE_API_URL
  if (typeof window !== 'undefined' && window.location.port === '3000') return 'http://localhost:8000'
  return ''
}
const API_BASE = getApiBase()
const ANALYZE_URL = API_BASE ? `${API_BASE}/llm/analyze-site` : '/api/llm/analyze-site'

const cardVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: (i) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.08, duration: 0.4 },
  }),
}

function Label({ children }) {
  return (
    <span className="block text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">
      {children}
    </span>
  )
}

function Card({ title, children, delay = 0 }) {
  return (
    <motion.div
      variants={cardVariants}
      custom={delay}
      initial="hidden"
      animate="visible"
      className="rounded-2xl bg-white p-5 sm:p-6 shadow-sm border border-slate-100 overflow-hidden"
    >
      <Label>{title}</Label>
      <div className="text-slate-700 leading-relaxed whitespace-pre-wrap">
        {children}
      </div>
    </motion.div>
  )
}

function ExampleCard({ children, delay = 0 }) {
  return (
    <motion.div
      variants={cardVariants}
      custom={delay}
      initial="hidden"
      animate="visible"
      className="rounded-xl bg-slate-50 p-4 border border-slate-200 text-slate-700 text-sm leading-relaxed whitespace-pre-wrap"
    >
      {children}
    </motion.div>
  )
}

function FinalAnalysisBlock({ data }) {
  if (!data || typeof data !== 'object') return null
  const entries = Object.entries(data)
  const hasExamples = (key) => /examples?/i.test(key)

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
      className="space-y-4"
    >
      {entries.map(([key, value], idx) => {
        const isExamples = hasExamples(key)
        const displayKey = key.replace(/_/g, ' ')

        if (isExamples && Array.isArray(value)) {
          return (
            <div key={key} className="space-y-3">
              <Label>{displayKey}</Label>
              <div className="grid gap-3 sm:grid-cols-1">
                {value.map((item, i) => (
                  <ExampleCard key={i} delay={idx + i * 0.05}>
                    {typeof item === 'string' ? item : JSON.stringify(item)}
                  </ExampleCard>
                ))}
              </div>
            </div>
          )
        }

        const text = typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)
        return (
          <Card key={key} title={displayKey} delay={idx}>
            {text}
          </Card>
        )
      })}
    </motion.div>
  )
}

export default function App() {
  const [url, setUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setResult(null)
    const trimmed = url.trim()
    if (!trimmed) {
      setError('Введите ссылку на сайт')
      return
    }
    setLoading(true)
    try {
      const { data } = await axios.post(ANALYZE_URL, { url: trimmed }, { timeout: 120000 })
      setResult(data)
    } catch (err) {
      const message = err.response?.data?.detail || err.message || 'Ошибка при анализе сайта'
      setError(Array.isArray(message) ? message.join(', ') : message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col">
      {/* Глобальный лоадер */}
      <AnimatePresence>
        {loading && (
          <motion.div
            key="global-loader"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-slate-900/80 backdrop-blur-sm"
          >
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ repeat: Infinity, duration: 1, ease: 'linear' }}
              className="w-14 h-14 rounded-full border-4 border-slate-500 border-t-emerald-400 mb-4"
            />
            <p className="text-lg font-medium text-white">Анализируем сайт...</p>
            <p className="text-sm text-slate-400 mt-1">Подождите, это может занять минуту</p>
          </motion.div>
        )}
      </AnimatePresence>

      <main className="flex-1 py-8 px-4 sm:px-6 flex justify-center">
        <div className="w-full max-w-[800px] mx-auto">
          <motion.h1
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="text-4xl sm:text-5xl font-bold text-slate-800 mb-2 tracking-tight"
          >
            UX-рецензент
          </motion.h1>
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.1 }}
            className="text-slate-500 mb-8 text-lg"
          >
            Анализ сайта и идеи для таргетированной рекламы
          </motion.p>

          <motion.form
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            onSubmit={handleSubmit}
            className="flex flex-col sm:flex-row gap-3 mb-8"
          >
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://example.com"
              className="flex-1 min-w-0 rounded-xl border border-slate-200 px-4 py-3 text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading}
              className="rounded-xl bg-emerald-600 px-6 py-3 font-medium text-white hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 disabled:opacity-60 disabled:cursor-not-allowed transition-colors shrink-0"
            >
              Отправить
            </button>
          </motion.form>

          <AnimatePresence mode="wait">
            {error && !loading && (
              <motion.div
                key="error"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="rounded-xl bg-red-50 border border-red-200 p-4 text-red-700 text-sm sm:text-base"
              >
                {error}
              </motion.div>
            )}

            {result && !loading && (
              <motion.div
                key="result"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="space-y-8"
              >
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="rounded-xl bg-slate-100 px-4 py-2 text-sm text-slate-600 truncate"
                  title={result.url}
                >
                  {result.url}
                </motion.div>

                {result.steps?.length > 0 && (
                  <div className="space-y-3">
                    <h2 className="text-lg font-semibold text-slate-800">Шаги анализа</h2>
                    <ul className="space-y-2">
                      {result.steps.map((step, i) => (
                        <motion.li
                          key={i}
                          variants={cardVariants}
                          custom={i}
                          initial="hidden"
                          animate="visible"
                          className="rounded-lg bg-white px-4 py-2 border border-slate-100 text-slate-700 text-sm"
                        >
                          {step}
                        </motion.li>
                      ))}
                    </ul>
                  </div>
                )}

                {result.intermediate_results?.length > 0 && (
                  <div className="space-y-3">
                    <h2 className="text-lg font-semibold text-slate-800">Промежуточные результаты</h2>
                    <div className="space-y-3">
                      {result.intermediate_results.map((text, i) => (
                        <Card key={i} title={`Шаг ${i + 1}`} delay={i}>
                          {text}
                        </Card>
                      ))}
                    </div>
                  </div>
                )}

                {result.final_analysis && (
                  <div className="space-y-4">
                    <h2 className="text-lg font-semibold text-slate-800">Итоговый анализ</h2>
                    <FinalAnalysisBlock data={result.final_analysis} />
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </main>
    </div>
  )
}
