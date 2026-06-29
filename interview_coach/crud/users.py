from sqlalchemy.orm import Session
from pwdlib import PasswordHash

from database.models import User
from schemas.user import UserCreate

password_hash = PasswordHash.recommended()

def create_user(db: Session, user: UserCreate):
    db_user = User(
        fullname=user.fullname,
        email=user.email,
        password=password_hash.hash(user.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
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