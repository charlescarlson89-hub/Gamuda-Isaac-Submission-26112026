from datetime import date

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

import models
from database import engine, SessionLocal


app = FastAPI(title="Books CRUD API")

# Allow the lesson's React webpage to call this API in the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type"],
)


# Create the books table in books_db.
models.Base.metadata.create_all(bind=engine)


# Open a database session and close it after each request.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Validate the information sent to the API.
class BookRequest(BaseModel):
    title: str = Field(min_length=3, max_length=1000)
    author: str = Field(min_length=3, max_length=1000)
    published_year: int = Field(
        ge=1800, le=date.today().year, strict=True
    )


# Define the information returned by the API.
class BookResponse(BookRequest):
    id: int
    model_config = ConfigDict(from_attributes=True)


# READ: List all books.
@app.get("/books", response_model=list[BookResponse])
def read_all(db: Session = Depends(get_db)):
    return db.query(models.Books).all()


# READ: Find one book by its ID.
@app.get("/books/{book_id}", response_model=BookResponse)
def read_book(book_id: int, db: Session = Depends(get_db)):
    book = db.get(models.Books, book_id)

    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    return book


# CREATE: Add a new book.
@app.post("/books", response_model=BookResponse, status_code=201)
def create_book(
    book_request: BookRequest,
    db: Session = Depends(get_db),
):
    book = models.Books(**book_request.model_dump())

    db.add(book)
    db.commit()
    db.refresh(book)

    return book


# UPDATE: Change an existing book.
@app.put("/books/{book_id}", response_model=BookResponse)
def update_book(
    book_id: int,
    book_request: BookRequest,
    db: Session = Depends(get_db),
):
    book = db.get(models.Books, book_id)

    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    book.title = book_request.title
    book.author = book_request.author
    book.published_year = book_request.published_year

    db.commit()
    db.refresh(book)

    return book


# DELETE: Remove a book.
@app.delete("/books/{book_id}")
def delete_book(book_id: int, db: Session = Depends(get_db)):
    book = db.get(models.Books, book_id)

    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    db.delete(book)
    db.commit()

    return {"message": "Book successfully deleted"}