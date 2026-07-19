from pydantic import BaseModel, Field, field_validator
from datetime import date
from typing import Literal

# Schemas

class AuthRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    token: str
    user: dict

# Schemas for habits and completions

class HabitCreate(BaseModel):
    name: str = Field(min_length=1)
    frequency: Literal["Daily", "Weekly"]

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("name must not be blank")
        return stripped


class HabitResponse(BaseModel):
    habitId: int
    name: str
    frequency: str
    completed: bool

    model_config = {"from_attributes": True}


class CompletionRequest(BaseModel):
    date: date


class CompletionResponse(BaseModel):
    id: int
    habitId: int
    period_start: date

    model_config = {"from_attributes": True}

