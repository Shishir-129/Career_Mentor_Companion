
from sqlalchemy import Column, Integer, String, DateTime
from database.connection import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    fullname = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    target_role = Column(String,nullable= False)
    created_at = Column(DateTime,default = datetime.utcnow())
