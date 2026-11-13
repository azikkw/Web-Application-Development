from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Author, Book
from ..schemas import AuthorIn, AuthorOut, BookOut

router = APIRouter(prefix="/api/authors", tags=["Authors"])

def get_author_or_404(author_id: int, db: Session) -> Author:
    author = db.get(Author, author_id)

    if author is None:
        raise HTTPException(status_code=404, detail="Author not found")

    return author

@router.get("", response_model=list[AuthorOut])
def list_authors(db: Session = Depends(get_db)):
    return db.scalars(select(Author).order_by(Author.id)).all()

@router.get("/{author_id}", response_model=AuthorOut)
def get_author(author_id: int, db: Session = Depends(get_db)):
    return get_author_or_404(author_id, db)

@router.post("", response_model=AuthorOut, status_code=status.HTTP_201_CREATED)
def create_author(data: AuthorIn, db: Session = Depends(get_db)):
    author = Author(**data.model_dump())

    db.add(author)
    db.commit()
    db.refresh(author)

    return author

@router.put("/{author_id}", response_model=AuthorOut)
def update_author(author_id: int, data: AuthorIn, db: Session = Depends(get_db)):
    author = get_author_or_404(author_id, db)

    for key, value in data.model_dump().items():
        setattr(author, key, value)

    db.commit()
    db.refresh(author)

    return author

@router.delete("/{author_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_author(author_id: int, db: Session = Depends(get_db)):
    author = get_author_or_404(author_id, db)

    db.delete(author)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.get("/{author_id}/books", response_model=list[BookOut])
def list_author_books(author_id: int, db: Session = Depends(get_db)):
    get_author_or_404(author_id, db)

    return db.scalars(select(Book).where(Book.author_id == author_id).order_by(Book.id)).all()
