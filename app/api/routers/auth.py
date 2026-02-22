from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_password_hash, verify_password, create_access_token
from app.db.models import User
from app.api.endpoints.common import UserCreate, UserLogin, AuthResponse, MessageResponse

router = APIRouter()

@router.post("/register", response_model=AuthResponse, tags=["auth"], summary="Register a new user", description="Create a new account by providing a name, email, and password.")
def register(user: UserCreate, db: Session = Depends(get_db)):
    try:
        print(f"REGISTRATION START: email={user.email}")
        
        print("DEBUG: Checking for existing user")
        db_user = db.query(User).filter(User.email == user.email).first()
        if db_user:
            print(f"DEBUG: Email {user.email} already exists")
            raise HTTPException(status_code=400, detail="Email already registered")
        
        print(f"DEBUG: Hashing password (length: {len(user.password)}, starts with: '{user.password[:2]}...')")
        try:
            hashed_password = get_password_hash(user.password)
        except Exception as hash_err:
            print(f"DEBUG: Hashing failed: {hash_err}")
            raise
            
        print("DEBUG: Creating User model instance")
        new_user = User(name=user.name, email=user.email, password_hash=hashed_password)
        
        print("DEBUG: Adding user to session")
        db.add(new_user)
        
        print("DEBUG: Committing session")
        db.commit()
        
        print("DEBUG: Refreshing user instance")
        db.refresh(new_user)
        
        print(f"DEBUG: Success! User ID={new_user.id}")
        token = create_access_token(data={"id": new_user.id, "email": new_user.email})
        return {"user": {"id": new_user.id, "name": new_user.name, "email": new_user.email}, "token": token}
    except Exception as e:
        print("-" * 50)
        print(f"REGISTRATION ERROR: {e}")
        import traceback
        traceback.print_exc()
        print("-" * 50)
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/login", response_model=AuthResponse, tags=["auth"], summary="User login", description="Authenticate with email and password to receive a JWT access token.")
def login(user: UserLogin, db: Session = Depends(get_db)):
    try:
        print(f"LOGIN START: email={user.email}")
        db_user = db.query(User).filter(User.email == user.email).first()
        if not db_user:
            print(f"DEBUG: Login failed - User {user.email} not found")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        print("DEBUG: Verifying password")
        if not verify_password(user.password, db_user.password_hash):
            print(f"DEBUG: Login failed - Incorrect password for {user.email}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        print("DEBUG: Password verified, generating token")
        token = create_access_token(data={"id": db_user.id, "email": db_user.email})
        return {"user": {"id": db_user.id, "name": db_user.name, "email": db_user.email}, "token": token}
    except Exception as e:
        print("-" * 50)
        print(f"LOGIN ERROR: {e}")
        import traceback
        traceback.print_exc()
        print("-" * 50)
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health", response_model=MessageResponse, tags=["auth"], summary="Health check", description="Verify if the authentication service is responsive.")
def health_check():
    return {"success": True, "status": "ok"}