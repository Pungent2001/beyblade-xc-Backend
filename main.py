from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Annotated
import models
from database import SessionLocal, engine
from sqlalchemy.orm import Session
from datetime import datetime

app = FastAPI()
models.Base.metadata.create_all(bind=engine)

class User(BaseModel):
    username: str
    email: str

class Ownership(BaseModel):
    owner: User
    part: int

class Stats(BaseModel):
    attack: int
    defense: int
    stamina: int
    weight: int
    burst: int
    dash: int

class Part(BaseModel):
    name: str
    type: str
    line: str
    stats: Stats
    description: str

class Combo(BaseModel):
    owner: int
    lock_chip: Part
    main_blade: Part
    assis_blade: Part
    ratchet: Part
    bit: Part
    combo_type: str
    description: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/createuser/")
async def create_user(username: str,email: str, password: str, db: db_dependency):
    db_user = models.User(username=username, email=email, password=password, created_date=datetime.now())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

@app.get("/users/")
async def get_users(db: db_dependency):
    result = db.query(models.User).all()
    if not result:
        raise HTTPException(status_code=404, detail="No users found")
    return result