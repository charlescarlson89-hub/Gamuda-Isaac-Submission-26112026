from fastapi.middleware.cors import CORSMiddleware
from datetime import date
from pydantic import BaseModel, Field
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Book

app = FastAPI(title="Books Learning API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type"],
)


# Give each request a database session.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def home():
    return {"message": "Books API is running"}


# Read all books from PostgreSQL.
@app.get("/books")
def read_books(db: Session = Depends(get_db)):
    return db.query(Book).order_by(Book.id).all()

# Check the data received from the user.
class BookCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    author: str = Field(min_length=3, max_length=100)
    published_year: int = Field(
        ge=1800,
        le=date.today().year,
        strict=True,
    )


@app.post("/books", status_code=201)
def create_book(book: BookCreate, db: Session = Depends(get_db)):
    new_book = Book(
        title=book.title,
        author=book.author,
        published_year=book.published_year,
    )

    db.add(new_book)
    db.commit()
    db.refresh(new_book)

    return new_book

@app.put("/books/{book_id}")
def update_book(
    book_id: int,
    book: BookCreate,
    db: Session = Depends(get_db),
):
    existing_book = db.get(Book, book_id)

    if existing_book is None:
        raise HTTPException(
            status_code=404,
            detail="Book not found",
        )

    existing_book.title = book.title
    existing_book.author = book.author
    existing_book.published_year = book.published_year

    db.commit()
    db.refresh(existing_book)

    return existing_book

@app.delete("/books/{book_id}")
def delete_book(
    book_id: int,
    db: Session = Depends(get_db),
):
    existing_book = db.get(Book, book_id)

    if existing_book is None:
        raise HTTPException(
            status_code=404,
            detail="Book not found",
        )

    db.delete(existing_book)
    db.commit()

    return {
        "message": "Book deleted successfully",
        "deleted_id": book_id,
    }