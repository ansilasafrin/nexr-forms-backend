from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.deps import get_db, get_password_hash, verify_password, create_access_token
from app.db.models import User
from app.api.endpoints.common import UserCreate, UserLogin, AuthResponse, MessageResponse

router = APIRouter()

@router.post("/register", response_model=AuthResponse, tags=["auth"], summary="Register a new user")
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        # Check for existing user
        result = await db.execute(select(User).filter(User.email == user.email))
        db_user = result.scalars().first()
        if db_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        hashed_password = get_password_hash(user.password)
        new_user = User(name=user.name, email=user.email, password_hash=hashed_password)
        
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        token = create_access_token(data={"id": new_user.id, "email": new_user.email})
        return {"user": {"id": new_user.id, "name": new_user.name, "email": new_user.email}, "token": token}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/login", response_model=AuthResponse, tags=["auth"], summary="User login")
async def login(user: UserLogin, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(User).filter(User.email == user.email))
        db_user = result.scalars().first()
        if not db_user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        if not verify_password(user.password, db_user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        token = create_access_token(data={"id": db_user.id, "email": db_user.email})
        return {"user": {"id": db_user.id, "name": db_user.name, "email": db_user.email}, "token": token}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health", response_model=MessageResponse, tags=["auth"], summary="Health check")
async def health_check():
    return {"success": True, "status": "ok"}
