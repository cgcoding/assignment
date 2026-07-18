
from fastapi import FastAPI
from models import User
from database import engine, Base
from auth.auth import router as auth_router
from habit.habit import router as habit_router
from fastapi.middleware.cors import CORSMiddleware
Base.metadata.create_all(bind=engine)
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

