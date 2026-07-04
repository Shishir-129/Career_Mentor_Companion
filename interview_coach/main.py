from fastapi import FastAPI

from database.connection import Base, engine
from routers.users import router as user_router
from routers.questions import router as question_router
from routers.sessions import router as session_router
from routers.responses import router as response_router
from routers import weak_areas
from routers import question_history

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Interview Coach API")

app.include_router(user_router)
app.include_router(question_router)
app.include_router(session_router)
app.include_router(response_router)
app.include_router(weak_areas.router)

app.include_router(question_history.router)