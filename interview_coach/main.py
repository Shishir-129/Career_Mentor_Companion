from fastapi import FastAPI
<<<<<<< HEAD
from database.connection import engine, Base
from routers import users 

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Interview Coach API")

app.include_router(users.router)
=======

from database.connection import Base, engine
from database.models import User
from routers.users import router as user_router
from routers.questions import router as question_router
Base.metadata.create_all(bind=engine)

app = FastAPI()


<<<<<<< Updated upstream
app.include_router(user_router)
>>>>>>> 3ca11a8d3755e93d1390b6f53855c9af039093fa
=======
app.include_router(user_router)
app.include_router(question_router)
>>>>>>> Stashed changes
