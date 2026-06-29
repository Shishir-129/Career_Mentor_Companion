from fastapi import FastAPI
from database.connection import engine, Base
from routers import users 

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Interview Coach API")

app.include_router(users.router)