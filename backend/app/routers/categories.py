from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.models import Category
from app.schemas.catalog import CategoryOut

router = APIRouter(prefix="/api/v1/categories", tags=["categories"])


@router.get("", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    top_level = (
        db.query(Category)
        .filter(Category.parent_id.is_(None))
        .options(joinedload(Category.children))
        .order_by(Category.name)
        .all()
    )
    return top_level
