# Запрос к модели gpt-4o

- Файл промпта: `02_code_structure.json`
- Температура: `1.0`

## System message

Ты - senior software architect с 15+ годами опыта проектирования масштабируемых приложений. Ты специализируешься на создании архитектурных решений, структуры кода, определении модулей, API и паттернов проектирования. Ты понимаешь принципы SOLID, CLEAN architecture, domain-driven design и умеешь создавать структуру кода, которая легко расширяется, тестируется и поддерживается.

Контекст:
Разработчик или команда нуждаются в профессионально спроектированной структуре кода для нового проекта или рефакторинга существующего. Необходимо создать архитектуру, которая учитывает масштабируемость, поддерживаемость, тестируемость и следует современным практикам разработки.

Структура вывода: Детальная структура проекта
- Общая архитектура: Описание общей архитектуры проекта (монолит, микросервисы, модули и т.д.)
- Структура директорий: Полная файловая структура с описанием назначения каждой директории
- Основные модули и компоненты: Список ключевых модулей с их ответственностью и зависимостями
- Паттерны проектирования: Применяемые паттерны и их обоснование
- API структура: Структура API endpoints (если применимо)
- База данных структура: Схема БД, модели данных (если применимо)
- Конфигурация: Файлы конфигурации и переменные окружения
- Тесты: Структура тестов и организация тестового покрытия

Требования:
- Использование принципов DRY (Don't Repeat Yourself)
- Разделение ответственности (Separation of Concerns)
- Dependency Injection где это уместно
- Следование SOLID принципам
- Поддержка модульного тестирования
- Читаемость и понятность кода
- Возможность легкого рефакторинга

## User message

Создай структуру проекта для веб-приложения электронной коммерции на Python (FastAPI) и React (TypeScript). Требования: REST API, PostgreSQL база данных, JWT аутентификация, файловое хранилище для изображений, система обработки заказов, панель администратора, система уведомлений по email, платежная интеграция, система отзывов и рейтингов.

## Model response

Вот подробная структура проекта для веб-приложения электронной коммерции, использующего Python (FastAPI) для backend и React (TypeScript) для frontend.

---

### Общая архитектура:
Проект будет построен на архитектуре на основе service-ориентированного подхода (Service-Oriented Architecture) внутри монолитного приложения, чтобы упростить начальную разработку, но с возможностью разделения логики сервиса на микросервисы в будущем. Используется FastAPI для backend REST API, PostgreSQL для базы данных, и S3-совместимое файловое хранилище (например, AWS S3).

---

### Структура директорий:
#### Backend:
```
backend/
│
├── app/  # Основное приложение FastAPI
│   ├── __init__.py
│   ├── main.py  # Точка входа, создающая приложение FastAPI
│   ├── api/  # REST API эндпоинты
│   │   ├── __init__.py
│   │   ├── v1/
│   │       ├── __init__.py
│   │       ├── auth.py  # Эндпоинты для аутентификации и авторизации
│   │       ├── products.py  # CRUD для товаров
│   │       ├── orders.py  # CRUD для заказов
│   │       ├── users.py  # CRUD для пользователей
│   │       ├── reviews.py  # CRUD для отзывов и рейтингов
│   │       ├── payments.py  # Интеграция с платежной системой
│   │       ├── notifications.py  # Email уведомления
│   │       └── admin.py  # Логика панели администратора
│   ├── core/  # Основные настройки и конфигурации
│   │   ├── __init__.py
│   │   ├── config.py  # Переменные окружения и настройки приложения
│   │   ├── security.py  # Логика для JWT
│   │   └── dependencies.py  # Зависимости FastAPI (например, DI для сервисов)
│   ├── db/  # Работа с базой данных
│   │   ├── __init__.py
│   │   ├── base.py  # base class для SQLAlchemy
│   │   ├── session.py  # SQLAlchemy сессия
│   │   └── migrations/  # Alembic миграции
│   ├── models/  # Модели ORM
│   │   ├── __init__.py
│   │   ├── user.py  # Модель пользователя
│   │   ├── product.py  # Модель товара
│   │   ├── order.py  # Модель заказа
│   │   ├── review.py  # Модель отзыва
│   │   ├── payment.py  # Модель платежа
│   │   └── notification.py  # Модель уведомления
│   ├── schemas/  # Pydantic схемы
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── product.py
│   │   ├── order.py
│   │   ├── review.py
│   │   ├── payment.py
│   │   └── notification.py
│   ├── services/  # Бизнес-логика
│   │   ├── __init__.py
│   │   ├── auth.py  # Логика регистрации/логина
│   │   ├── product.py
│   │   ├── order.py
│   │   ├── review.py
│   │   ├── payment.py
│   │   └── notification.py  # Логика email уведомлений
│   ├── utils/  # Вспомогательные инструменты
│   │   ├── __init__.py
│   │   ├── file_handler.py  # Загрузка/удаление файлов
│   │   ├── email_sender.py  # Отправка email
│   │   └── pagination.py
│   ├── tests/  # Тесты
│       ├── __init__.py
│       ├── test_auth.py  # Тесты для аутентификации
│       ├── test_products.py
│       ├── test_orders.py
│       └── test_payments.py
│
└── Dockerfile  # Docker образ
```

#### Frontend:
```
frontend/
│
├── public/  # Публичные статические файлы
│   ├── index.html
│   └── favicon.ico
├── src/
│   ├── components/  # React компоненты
│   │   ├── Header.tsx
│   │   ├── Footer.tsx
│   │   ├── ProductCard.tsx
│   │   └── ...
│   ├── pages/  # Страницы приложения
│   │   ├── HomePage.tsx
│   │   ├── ProductPage.tsx
│   │   ├── CartPage.tsx
│   │   ├── CheckoutPage.tsx
│   │   ├── AdminDashboardPage.tsx
│   │   └── ...
│   ├── contexts/  # Context API
│   │   ├── AuthContext.tsx
│   │   └── NotificationContext.tsx
│   ├── hooks/  # Пользовательские хуки
│   │   ├── useAuth.ts
│   │   └── useFetch.ts
│   ├── services/  # Работа с API
│   │   ├── api.ts
│   │   ├── authService.ts
│   │   ├── productService.ts
│   │   ├── orderService.ts
│   │   └── ...
│   ├── styles/  # CSS, SASS/SCSS стили
│   │   ├── main.scss
│   │   ├── variables.scss
│   │   └── ...
│   ├── utils/  # Утилиты
│   │   ├── formatCurrency.ts
│   │   └── validateForm.ts
│   ├── App.tsx  # Точка входа приложения
│   └── index.tsx  # Точка входа React
├── tsconfig.json  # Типизация TypeScript
└── package.json  # Зависимости проекта
```

---

### Основные модули и компоненты:
1. **Auth Service**: Регистрация/аутентификация, JWT токены.
2. **Product Service**: CRUD для работы с товарами.
3. **Order Service**: Логика для создания/обработки заказов.
4. **Payment Service**: Интеграция внешней платежной системы (например, Stripe).
5. **Notification Service**: Email уведомления (например, с использованием FastAPI-background tasks).
6. **Review Service**: CRUD для отзывов и рейтингов.
7. **Admin Panel**: API и интерфейс для работы с административными функциями.
8. **File Management**: Загрузка и управление изображениями товаров.

---

### Паттерны проектирования:
1. **Repository Pattern**: Четкое разделение бизнес-логики и операций с базой данных.
2. **Dependency Injection**: Для сервисов в FastAPI.
3. **Factory Pattern**: Для создания API-сервисов/зависимостей.
4. **CQRS (Command Query Responsibility Segregation)**: Разделение команд (изменений) и запросов данных в некоторых модулях.

---

### API структура:
- **GET /api/v1/products**: Получение списка товаров.
- **POST /api/v1/auth/login**: Вход в систему.
- **POST /api/v1/orders**: Размещение нового заказа.
- **GET /api/v1/reviews/{product_id}**: Получение отзывов для конкретного товара.
- **POST /api/v1/payments**: Отправка данных для обработки платежа.

---

### База данных структура:
Основные таблицы:
- **users** (id, email, password_hash, role).
- **products** (id, name, description, price, image_url).
- **orders** (id, user_id, total_price, status).
- **order_items** (id, order_id, product_id, quantity).
- **reviews** (id, product_id, user_id, rating, comment).
- **notifications** (id, user_id, message, sent_at).
- **payments** (id, order_id, status, transaction_id).

---

### Конфигурация:
Используйте файл `.env`:
```
DATABASE_URL=postgresql://user:password@localhost:5432/ecommerce
SECRET_KEY=mysecretkey
JWT_ALGORITHM=HS256
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USER=example@example.com
EMAIL_PASSWORD=examplepassword
AWS_S3_BUCKET_NAME=example-bucket
```

---

### Тесты:
1. **Unit-tests**: Модули `services`, `utils`.
2. **Integration-tests**: Проверка взаимодействия API и базы данных.
3. **E2E-tests**: Используйте Cypress для тестирования frontend.
Test Coverage:
- Тесты аутентификации.
- CRUD операции.
- Логика заказов и платежей.

---

Такой проект организован с упором на модульность, поддержку и масштабируемость.

## Usage

- prompt_tokens: 488
- completion_tokens: 2137
- total_tokens: 2625
