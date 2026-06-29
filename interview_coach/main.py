from fastapi import FastAPI

from database.connection import Base, engine
from database.models import User
from routers.users import router as user_router
Base.metadata.create_all(bind=engine)

app = FastAPI()


app.include_router(user_router)