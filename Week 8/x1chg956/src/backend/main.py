
from fastapi import FastAPI
from sqlalchemy import text
from models import User
from database import engine, Base
from auth.auth import router as auth_router
from habit.habit import router as habit_router
from fastapi.middleware.cors import CORSMiddleware
Base.metadata.create_all(bind=engine)


def _ensure_habit_completion_date_column() -> None:
    with engine.connect() as connection:
        columns = connection.execute(text("PRAGMA table_info(habit_completions)")).fetchall()
        column_names = [column[1] for column in columns]
        if "completion_date" not in column_names:
            connection.execute(text("ALTER TABLE habit_completions ADD COLUMN completion_date DATE"))
            connection.commit()


_ensure_habit_completion_date_column()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  
    allow_credentials=True, 
    allow_methods=["*"], 
    allow_headers=["*"], 
)

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(habit_router, prefix="/api/habit", tags=["habit"])
@app.get("/")
def read_root():
    return {"message": "Backend is running"}

