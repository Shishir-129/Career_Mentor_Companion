from sqlalchemy.orm import Session
from pwdlib import PasswordHash

from database.models import User
from schemas.user import UserCreate

password_hash = PasswordHash.recommended()

    

from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

def create_user(db, user):
    hashed_password = password_hash.hash(user.password)
    db_user = User(
        fullname=user.fullname,
        email=user.email,
        password=hashed_password,
        target_role=user.target_role,
    )
    db.add(db_user)
    try:
        db.commit()
        db.refresh(db_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email already registered")
    return db_user


    
        
def get_users(db: Session):
    return db.query(User).all()

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def delete_user(db: Session, user_id: int):
    user = get_user(db, user_id)
    if not user:
        return None
    db.delete(user)
    db.commit()
    return user