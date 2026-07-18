from pydantic import BaseModel
from datetime import date

# Schemas

class AuthRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    token: str
    user: dict
    
# Schemas for habits and completions


class HabitCreate(BaseModel):
    name: str
    frequency: str


class HabitOut(BaseModel):
    id: int
    userId: int
    name: str
    frequency: str


class HabitCompletionIn(BaseModel):
    completion_date: date


class HabitStreakOut(BaseModel):
    habitId: int
    name: str
    frequency: str
    current_streak: int
    longest_streak: int
    last_completed_date: date | None

