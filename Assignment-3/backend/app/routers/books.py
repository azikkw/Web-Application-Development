from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Author, Book, Review
from ..schemas import BookIn, BookOut, ReviewCreate, ReviewOut

router = APIRouter(prefix="/api/books", tags=["Books"])

def get_book_or_404(book_id: int, db: Session) -> Book:
    book = db.get(Book, book_id)

    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    return book

def ensure_author_exists(author_id: int, db: Session) -> None:
    if db.get(Author, author_id) is None:
        raise HTTPException(status_code=404, detail="Author not found")

@router.get("", response_model=list[BookOut])
def list_books(db: Session = Depends(get_db)):
    return db.scalars(select(Book).order_by(Book.id)).all()

@router.get("/{book_id}", response_model=BookOut)
def get_book(book_id: int, db: Session = Depends(get_db)):
    return get_book_or_404(book_id, db)

@router.post("", response_model=BookOut, status_code=status.HTTP_201_CREATED)
def create_book(data: BookIn, db: Session = Depends(get_db)):
    ensure_author_exists(data.author_id, db)
    book = Book(**data.model_dump())

    db.add(book)
    db.commit()
    db.refresh(book)

    return book

@router.put("/{book_id}", response_model=BookOut)
def update_book(book_id: int, data: BookIn, db: Session = Depends(get_db)):
    book = get_book_or_404(book_id, db)
    ensure_author_exists(data.author_id, db)

    for key, value in data.model_dump().items():
        setattr(book, key, value)

    db.commit()
    db.refresh(book)

    return book

@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(book_id: int, db: Session = Depends(get_db)):
    book = get_book_or_404(book_id, db)

    db.delete(book)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.get("/{book_id}/reviews", response_model=list[ReviewOut])
def list_book_reviews(book_id: int, db: Session = Depends(get_db)):
    get_book_or_404(book_id, db)

    return db.scalars(select(Review).where(Review.book_id == book_id).order_by(Review.id)).all()

@router.post("/{book_id}/reviews", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
def create_book_review(book_id: int, data: ReviewCreate, db: Session = Depends(get_db)):
    get_book_or_404(book_id, db)
    review = Review(book_id=book_id, **data.model_dump())

    db.add(review)
    db.commit()
    db.refresh(review)

    return review
