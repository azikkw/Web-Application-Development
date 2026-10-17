import os
from contextlib import asynccontextmanager
from typing import Literal
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import psycopg2
from psycopg2.extras import RealDictCursor

def get_connection():
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        port=os.environ["DB_PORT"],
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
    )

def init_db():
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS books (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                pages INTEGER NOT NULL CHECK (pages > 0),
                status TEXT NOT NULL DEFAULT 'planned',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )

@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield

app = FastAPI(title=os.environ.get("APP_NAME", "Book Tracker API"), lifespan=lifespan)

class BookIn(BaseModel):
    title: str = Field(min_length=3)
    author: str = Field(min_length=3)
    pages: int = Field(gt=0)
    status: Literal["planned", "reading", "threw", "finished"] = "planned"

class BookUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3)
    author: str | None = Field(default=None, min_length=3)
    pages: int | None = Field(default=None, gt=0)
    status: Literal["planned", "reading", "threw", "finished"] | None = None

@app.get("/books")
def list_books():
    with get_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            "SELECT id, title, author, pages, status, created_at FROM books ORDER BY id"
        )
        return cur.fetchall()

@app.get("/stats")
def reading_stats():
    with get_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT
                COUNT(*) AS total_books,
                COUNT(*) FILTER (WHERE status = 'finished') AS finished_books,
                COALESCE(SUM(pages) FILTER (WHERE status = 'finished'), 0) AS pages_read
            FROM books
            """
        )
        return cur.fetchone()

@app.post("/books", status_code=201)
def add_book(book: BookIn):
    with get_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            INSERT INTO books (title, author, pages, status)
            VALUES (%s, %s, %s, %s)
            RETURNING id, title, author, pages, status, created_at
            """,
            (book.title, book.author, book.pages, book.status),
        )
        return cur.fetchone()

@app.patch("/books/{book_id}")
def patch_book(book_id: int, book: BookUpdate):
    with get_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            UPDATE books
            SET title = COALESCE(%s, title),
                author = COALESCE(%s, author),
                pages = COALESCE(%s, pages),
                status = COALESCE(%s, status)
            WHERE id = %s
            RETURNING id, title, author, pages, status, created_at
            """,
            (book.title, book.author, book.pages, book.status, book_id),
        )
        updated = cur.fetchone()
        if updated is None:
            raise HTTPException(status_code=404, detail="Book not found")
        return updated

@app.delete("/books/{book_id}", status_code=204)
def delete_book(book_id: int):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM books WHERE id = %s", (book_id,))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Book not found")
