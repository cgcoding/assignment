from fastapi import APIRouter, HTTPException, Depends
import bcrypt
from models import User
from database import engine, Base, get_db
from sqlalchemy.orm import Session
from datetime import timedelta
from jwt_tokens import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from schemas import AuthRequest, AuthResponse


Base.metadata.create_all(bind=engine)

router = APIRouter()


# Dependency to get DB session


@router.post("/signup", response_model=AuthResponse)
def signup(data: AuthRequest, db: Session = Depends(get_db)):

    existing_user = db.query(User).filter_by(email=data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    hashed_pw = bcrypt.hashpw(data.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    user = User(email=data.email, hashed_password=hashed_pw)
    db.add(user)
    db.commit()
    db.refresh(user)

    # Create token with user ID as the subject
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires)

    return {"token": token, "user": {"id": user.id, "email": user.email}}


@router.post("/login", response_model=AuthResponse)
def login(data: AuthRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=data.email).first()
    if not user or not bcrypt.checkpw(
        data.password.encode("utf-8"), user.hashed_password.encode("utf-8")
    ):
        raise HTTPException(
            status_code=400, detail="Invalid email or password")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires)

    return {"token": token, "user": {"id": user.id, "email": user.email}}
