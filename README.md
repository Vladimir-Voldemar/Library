# Library API

REST API для каталога книг с выдачами. Пользователи добавляют книги с авторами и жанрами, берут их «на руках» и возвращают.

## Стек

- Python 3.12
- FastAPI
- SQLAlchemy 2.0
- PostgreSQL 18
- Alembic (миграции)
- Docker + docker-compose

## Возможности

- CRUD для книг, авторов, жанров
- Many-to-many: книга ↔ авторы, книга ↔ жанры
- Выдачи книг: взять / сдать, проверка «книга на руках»
- Автодокументация Swagger на `/docs`

## Запуск

### Локально

```bash
pip install -r requirements.txt
# создай базу library в PostgreSQL
alembic upgrade head
python main.py
Через Docker
bash
cp .env.example .env   # впиши свой пароль
docker compose up --build
docker compose exec app alembic upgrade head
Приложение: http://localhost:8000/docs

Эндпоинты
Книги
GET /books — все книги

GET /books/{id} — одна книга с авторами и жанрами

POST /books — создать

Авторы
GET /authors — все

GET /authors/{id} — один с его книгами

POST /authors — создать

Жанры
GET /genres — все

POST /genres — создать

Пользователи
GET /users/{id} — юзер и его книги

POST /users — создать

Выдачи
POST /borrowings/took — взять книгу

POST /borrowings/returned — сдать

Структура
text
library/
├── main.py           # приложение, модели, эндпоинты
├── alembic/          # миграции
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env.example