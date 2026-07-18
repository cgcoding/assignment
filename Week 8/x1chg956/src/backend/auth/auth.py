from fastapi import APIRouter, HTTPException, Depends
from models import User
from database import engine, Base, get_db
from sqlalchemy.orm import Session
from passlib.hash import pbkdf2_sha256
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

    hashed_pw = pbkdf2_sha256.hash(data.password)
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
    if not user or not pbkdf2_sha256.verify(data.password, user.hashed_password):
        raise HTTPException(
            status_code=400, detail="Invalid email or password")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires)

    return {"token": token, "user": {"id": user.id, "email": user.email}}
