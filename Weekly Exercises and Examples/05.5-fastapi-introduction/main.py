
from fastapi import FastAPI

app = FastAPI()

# =====================================
# OUR LIBRARY DATABASE
# =====================================

BOOKS = [
    {
        "title": "Fourth Wing",
        "author": "Rebecca Yarros",
        "published_year": 2023
    },
    {
        "title": "On Freedom",
        "author": "Timothy Snyder",
        "published_year": 2024
    },
    {
        "title": "It Starts with Us",
        "author": "Colleen Hoover",
        "published_year": 2022
    },
    {
        "title": "The Book of Bill",
        "author": "Alex Hirsch",
        "published_year": 2024
    },
    {
        "title": "On Tyranny",
        "author": "Timothy Snyder",
        "published_year": 2017
    }
]


# =====================================
# 1. ROOT ENDPOINT
# =====================================

@app.get("/")
async def read_root():
    return {"message": "Hello World"}


# =====================================
# 2. SMART BOOK SEARCH
# GET ALL BOOKS / TITLE / AUTHOR / YEAR
# =====================================

@app.get("/books")
async def search_books(
    title: str | None = None,
    author: str | None = None,
    year: int | None = None
):

    matching_books = BOOKS

    # SEARCH BY TITLE
    if title and title.strip():
        search_title = title.strip().casefold()

        matching_books = [
            book for book in matching_books
            if search_title in book["title"].casefold()
        ]

    # SEARCH BY AUTHOR
    if author and author.strip():
        search_author = author.strip().casefold()

        matching_books = [
            book for book in matching_books
            if search_author in book["author"].casefold()
        ]

    # SEARCH BY PUBLICATION YEAR
    if year is not None:

        matching_books = [
            book for book in matching_books
            if book["published_year"] == year
        ]

    # RETURN MATCHING BOOKS
    if matching_books:
        return matching_books

    # IF NOTHING MATCHES
    return {"message": "No matching books found"}
