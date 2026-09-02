"""
Хранилище SQLite для заметок, задач Kanban и графа связей.
"""

from datetime import datetime
import sqlite3
from typing import Any, Dict, List, Optional
from noteflow.config import DB_PATH


class NoteFlowDB:
    def __init__(self, db_path=DB_PATH):
        self.db_path = str(db_path)
        self.init_schema()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_schema(self):
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    folder TEXT NOT NULL DEFAULT 'Inbox',
                    word_count INTEGER DEFAULT 0,
                    reading_time_min INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'TODO', -- TODO, IN_PROGRESS, REVIEW, DONE
                    priority TEXT NOT NULL DEFAULT 'MEDIUM', -- LOW, MEDIUM, HIGH, URGENT
                    due_date TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS backlinks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_doc_id INTEGER NOT NULL,
                    target_title TEXT NOT NULL,
                    FOREIGN KEY (source_doc_id) REFERENCES documents(id)
                )
            """)
            conn.commit()

        self._seed_default_data()

    def _seed_default_data(self):
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM documents")
            if c.fetchone()[0] == 0:
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                docs = [
                    (
                        "Архитектурный манифест v2.0",
                        "# Архитектурный манифест\n\nМодульная архитектура сервисов базируется на принципах Domain-Driven Design.\n\n## Ключевые требования:\n- Локальная изолированность компонентов\n- Связи через [[Интеграция API]]\n- Минимизация внешних зависимостей\n\nСмотри также [[План релиза Q4]].",
                        "Архитектура", 68, 1, now, now
                    ),
                    (
                        "Интеграция API",
                        "# Спецификация REST & GraphQL API\n\nЭндпоинты для обмена событиями в реальном времени.\n\n- GET `/v1/sync`\n- POST `/v1/events`\n\nОписано в [[Архитектурный манифест v2.0]].",
                        "Бэкенд", 42, 1, now, now
                    ),
                    (
                        "План релиза Q4",
                        "# Roadmap Q4\n\nПлан выкатки релизов и миграции базы данных.\n\n- [x] Проектирование схемы\n- [ ] Нагрузочное тестирование\n- [ ] Деплой на staging",
                        "Продукт", 34, 1, now, now
                    ),
                ]
                c.executemany("""
                    INSERT INTO documents (title, content, folder, word_count, reading_time_min, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, docs)

                tasks = [
                    ("Настроить CI/CD пайплайн сборки", "IN_PROGRESS", "HIGH", "2026-11-15", now),
                    ("Рефакторинг слоя кеширования Redis", "TODO", "MEDIUM", "2026-11-20", now),
                    ("Security-аудит эндпоинтов авторизации", "REVIEW", "URGENT", "2026-11-10", now),
                    ("Подготовка технической документации OpenAPI", "DONE", "LOW", "2026-11-04", now),
                ]
                c.executemany("""
                    INSERT INTO tasks (title, status, priority, due_date, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, tasks)
                conn.commit()

    # CRUD документов
    def get_documents(self, folder: Optional[str] = None, search: str = "") -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            c = conn.cursor()
            q = "SELECT * FROM documents WHERE 1=1"
            params = []
            if folder and folder != "Все":
                q += " AND folder = ?"
                params.append(folder)
            if search:
                q += " AND (title LIKE ? OR content LIKE ?)"
                params.append(f"%{search}%")
                params.append(f"%{search}%")
            q += " ORDER BY updated_at DESC"
            c.execute(q, params)
            return [dict(r) for r in c.fetchall()]

    def save_document(self, doc_id: Optional[int], title: str, content: str, folder: str = "Inbox") -> int:
        words = len(content.split())
        read_time = max(1, words // 180)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with self.get_connection() as conn:
            c = conn.cursor()
            if doc_id:
                c.execute("""
                    UPDATE documents SET title = ?, content = ?, folder = ?, word_count = ?, reading_time_min = ?, updated_at = ?
                    WHERE id = ?
                """, (title, content, folder, words, read_time, now, doc_id))
                return doc_id
            else:
                c.execute("""
                    INSERT INTO documents (title, content, folder, word_count, reading_time_min, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (title, content, folder, words, read_time, now, now))
                return c.lastrowid

    # CRUD задач Kanban
    def get_tasks(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM tasks ORDER BY id DESC")
            return [dict(r) for r in c.fetchall()]

    def update_task_status(self, task_id: int, new_status: str):
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute("UPDATE tasks SET status = ? WHERE id = ?", (new_status, task_id))
            conn.commit()

    def add_task(self, title: str, status: str = "TODO", priority: str = "MEDIUM"):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute("INSERT INTO tasks (title, status, priority, created_at) VALUES (?, ?, ?, ?)", (title, status, priority, now))
            conn.commit()

