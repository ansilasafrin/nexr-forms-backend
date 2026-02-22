from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_password_hash, verify_password, create_access_token
from app.db.models import User
from app.api.endpoints.common import UserCreate, UserLogin

router = APIRouter()

@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    new_user = User(name=user.name, email=user.email, password_hash=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    token = create_access_token(data={"id": new_user.id, "email": new_user.email})
    return {"user": {"id": new_user.id, "name": new_user.name, "email": new_user.email}, "token": token}

@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token(data={"id": db_user.id, "email": db_user.email})
    return {"user": {"id": db_user.id, "name": db_user.name, "email": db_user.email}, "token": token}

@router.get("/health")
def health_check():
    return {"status": "ok"}