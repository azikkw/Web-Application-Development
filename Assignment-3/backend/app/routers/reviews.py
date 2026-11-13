from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Review
from ..schemas import ReviewOut, ReviewUpdate

router = APIRouter(prefix="/api/reviews", tags=["Reviews"])

def get_review_or_404(review_id: int, db: Session) -> Review:
    review = db.get(Review, review_id)

    if review is None:
        raise HTTPException(status_code=404, detail="Review not found")

    return review

@router.get("/{review_id}", response_model=ReviewOut)
def get_review(review_id: int, db: Session = Depends(get_db)):
    return get_review_or_404(review_id, db)

@router.patch("/{review_id}", response_model=ReviewOut)
def update_review(review_id: int, data: ReviewUpdate, db: Session = Depends(get_db)):
    review = get_review_or_404(review_id, db)

    for key, value in data.model_dump(exclude_none=True).items():
        setattr(review, key, value)

    db.commit()
    db.refresh(review)

    return review

@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(review_id: int, db: Session = Depends(get_db)):
    review = get_review_or_404(review_id, db)

    db.delete(review)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
