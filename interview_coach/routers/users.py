from fastapi import APIRouter, Depends, HTTPException
from schemas.user import UserCreate, UserLogin, UserResponse
from sqlalchemy.orm import Session
from crud.users import create_user as create_user_db, get_users, get_user, delete_user, authenticate_user
from database.connection import get_db

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    return create_user_db(db, user)


@router.post("/login", response_model=UserResponse)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, credentials.email, credentials.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return user

@router.get("/", response_model=list[UserResponse])
def read_users(db: Session = Depends(get_db)):
    return get_users(db)

@router.get("/{user_id}", response_model=UserResponse)
def read_user(user_id: int, db: Session = Depends(get_db)):
    return get_user(db, user_id)

@router.delete("/{user_id}", response_model=UserResponse)
def remove_user(user_id: int, db: Session = Depends(get_db)):
    return delete_user(db, user_id)
