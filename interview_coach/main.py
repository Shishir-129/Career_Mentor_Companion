from fastapi import FastAPI

from database.connection import Base, engine
from routers.users import router as user_router
from routers.questions import router as question_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Interview Coach API")

app.include_router(user_router)
app.include_router(question_router)