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
    name: str
    frequency: str
    user_id: int

    class Config:
        from_attributes = True


class HabitCompletionIn(BaseModel):
    completed_on: date


class HabitCompletionOut(BaseModel):
    id: int
    habit_id: int
    user_id: int
    completed_on: date
    period_start: date

    class Config:
        from_attributes = True

