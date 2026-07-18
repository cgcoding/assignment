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

