import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models import Address, User
from app.schemas.address import AddressCreate, AddressOut
from app.schemas.auth import UserOut

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/me/addresses", response_model=list[AddressOut])
def list_addresses(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Address).filter(Address.user_id == current_user.id).all()


@router.post("/me/addresses", response_model=AddressOut, status_code=status.HTTP_201_CREATED)
def add_address(payload: AddressCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if payload.is_default:
        db.query(Address).filter(Address.user_id == current_user.id).update({"is_default": False})
    address = Address(user_id=current_user.id, **payload.model_dump())
    db.add(address)
    db.commit()
    db.refresh(address)
    return address


@router.patch("/me/addresses/{address_id}", response_model=AddressOut)
def update_address(address_id: uuid.UUID, payload: AddressCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    address = db.get(Address, address_id)
    if address is None or address.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Address not found")
    if payload.is_default:
        db.query(Address).filter(Address.user_id == current_user.id).update({"is_default": False})
    for field, value in payload.model_dump().items():
        setattr(address, field, value)
    db.commit()
    db.refresh(address)
    return address


@router.delete("/me/addresses/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_address(address_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    address = db.get(Address, address_id)
    if address is None or address.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Address not found")
    db.delete(address)
    db.commit()
    return None
