# Умный текст-помощник

Консольный ассистент с поддержкой OpenAI-совместимых моделей и Claude (через ProxyAPI). История диалога сохраняется в файл, режимы переключаются командами.

## Установка

1. **Виртуальное окружение** (в папке проекта):
   ```bash
   python -m venv venv
   ```

2. **Активация**:
   - Windows (PowerShell): `.\venv\Scripts\Activate.ps1`
   - Windows (cmd): `venv\Scripts\activate.bat`
   - Linux/macOS: `source venv/bin/activate`

3. **Зависимости**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Настройка** — создайте файл `.env` в корне проекта:
   ```
   OPENAI_API_KEY=ваш-ключ
   OPENAI_BASE_URL=https://api.proxyapi.ru/openai/v1
   DEFAULT_MODEL=gpt-4o-mini
   REQUEST_TIMEOUT=30
   LOG_LEVEL=INFO
   ```
   Модель по умолчанию — `gpt-4o-mini` (подходит для ProxyAPI). Для Grok или другого провайдера задайте в .env свой `DEFAULT_MODEL`.

   Для режима Claude (опционально):
   ```
   ANTHROPIC_API_KEY=ключ
   ANTHROPIC_BASE_URL=https://api.proxyapi.ru/openai/v1
   CLAUDE_MODEL=claude-3-5-sonnet-20241022
   ```
   Если `ANTHROPIC_API_KEY` не задан, используется `OPENAI_API_KEY`.

## Запуск

```bash
python test_agent.py
```

Запускается консольный ассистент. История загружается из `history.json` (если есть) и сохраняется при выходе.

### Команды (введите номер)

| № | Действие |
|---|----------|
| 0 | В главное меню (показать меню выбора модели и команд, без выхода) |
| 1 | Выход из программы (история сохраняется) |
| 2 | Режим: обычная модель (OpenAI) |
| 3 | Режим: думающая модель (Claude); после выбора запрашивается уровень рассуждения (low / medium / high) |
| 4 | Очистить историю диалога |
| 5 | Показать меню команд |

Ввод, отличный от 0–5, считается сообщением ассистенту; ответ выдаётся с учётом контекста. В режиме Claude выводится блок `[Reasoning]` с метаданными (например, токены).

## Структура проекта

- **`text_agent.py`** — ядро: конфиг из .env, клиенты OpenAI/Claude, функции `generate_response` / `generate_response_claude`, класс `TextAgent` (история, режимы, сохранение в JSON).
- **`test_agent.py`** — консольный интерфейс: цикл ввода, разбор команд, вывод ответа и reasoning.

## Использование в коде

**Класс TextAgent (история + режимы):**
```python
from text_agent import TextAgent

agent = TextAgent(mode="openai")
agent.load_history()

result = agent.generate_response("Привет!")
print(result["text"])       # ответ
print(result["reasoning"])  # None для openai, dict для claude

agent.set_mode("claude")
result = agent.generate_response("Объясни короче.")
agent.save_history()
```

**Функции без класса:**
```python
from text_agent import get_client, generate_response, generate_response_claude

# Один запрос (OpenAI)
messages = [{"role": "user", "content": "Привет!"}]
result = generate_response(messages)
print(result["text"], result["reasoning"])

# Claude с reasoning
result = generate_response_claude(messages, reasoning_effort="medium")
```

**Только текст ответа:**
```python
from text_agent import get_client, chat_completion

client = get_client()
messages = [{"role": "user", "content": "Привет!"}]
reply = chat_completion(client, messages)
```
