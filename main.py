from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import create_url
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
import models
from database import engine, SessionLocal
from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import BaseModel

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="OsD0S API")

# Security setup
SECRET_KEY = "SUPER_SECRET_KEY_OSDOS" # Ganti pas deploy!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 3000

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Pydantic models
class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    role: str
    status: str
    status_reason: Optional[str]
    locked_features: str
    is_online: bool

class Token(BaseModel):
    access_token: str
    token_type: str

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Auth Utilities
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# Routes
@app.post("/register", response_model=Token)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user_in.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # First user is Admin
    user_count = db.query(models.User).count()
    role = models.UserRole.ADMIN if user_count == 0 else models.UserRole.USER
    
    new_user = models.User(
        username=user_in.username,
        hashed_password=get_password_hash(user_in.password),
        role=role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    access_token = create_access_token(data={"sub": new_user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    user.is_online = True
    db.commit()
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/me", response_model=UserResponse)
def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user

# Admin Endpoints
@app.get("/admin/users", response_model=List[UserResponse])
def list_users(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return db.query(models.User).all()

@app.post("/admin/action")
def admin_action(user_id: int, action: str, reason: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    target = db.query(models.User).filter(models.User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    
    if action in ["banned", "kicked", "muted", "active"]:
        target.status = action
        target.status_reason = reason
        if action == "kicked":
            target.is_online = False # Logout effect
        db.commit()
        return {"msg": f"User {target.username} status updated to {action}"}
    
    raise HTTPException(status_code=400, detail="Invalid action")

@app.post("/admin/lock-feature")
def lock_feature(user_id: int, feature: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    target = db.query(models.User).filter(models.User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    
    target.locked_features = feature # overwrite or append
    db.commit()
    return {"msg": f"Feature {feature} locked for {target.username}"}
