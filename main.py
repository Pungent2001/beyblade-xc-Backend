from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Annotated, Optional
import models
from database import SessionLocal, engine
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from models import Users, Parts, Lines, Combos, PartTypes, Stats, Ownerships
import auth
from auth import get_current_user, isUserAdmin
from fastapi.security import HTTPBearer
from fastapi.openapi.utils import get_openapi

app = FastAPI()
models.Base.metadata.create_all(bind=engine)
app.include_router(auth.router)


security_scheme = {
    "OAuth2PasswordBearer": {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT"
    }
}

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="BeybladeXC",
        version="0.0.1",
        description="API for BeybladeXC",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = security_scheme
    public_endpoints = ["/", "/login", "/register", "/docs", "/redoc", "/openapi.json", "/auth/login", "/auth/register"]
    
    for path_name, path_info in openapi_schema["paths"].items():
        if path_name in public_endpoints:
            continue
        
        for method in path_info.values():
            if isinstance(method, dict):
                method.setdefault("security", [{"Bearer": []}])
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

class UserLogin(BaseModel):
    email: str
    password: str

class UserRegister(BaseModel):
    username: str
    email: str
    password: str

class User_Out(BaseModel):
    id: int
    user_type: str
    username: str
    email: str
    class Config:
        from_attributes = True

class PartType_Out(BaseModel):
    id: int
    name: str
    class Config:
        from_attributes = True

class PartType_In(BaseModel):
    name: str

class Restriction_Out(BaseModel):
    id: int
    description: str
    class Config:
        from_attributes = True

class Restriction_Create(BaseModel):
    description: str

class Restriction_In(BaseModel):
    id: int

class Stat_Out(BaseModel):
    id: int
    minAtk: int
    maxAtk: int
    minDef: int
    maxDef: int
    minSta: int
    maxSta: int
    weight: int
    burst: int
    dash: int
    class Config:
        from_attributes = True

class Stat_In(BaseModel):
    minAtk: int
    maxAtk: int
    minDef: int
    maxDef: int
    minStam: int
    maxStam: int
    weight: int
    burst: int
    dash: int

class Part_Out(BaseModel):
    id: int
    name: str
    type: int
    stats: int
    restriction: int
    class Config:
        from_attributes = True

class Part_In(BaseModel):
    name: str
    type: PartType_In
    stats: Stat_In
    restriction: Optional[Restriction_In] = None

class Line_Out(BaseModel):
    id: int
    name: str
    class Config:
        from_attributes = True

class Line_In(BaseModel):   
    name: str

class Combo_Out(BaseModel):
    id: int
    isStock: bool
    line: Line_Out
    lockChip: Optional[Part_Out] = None
    blade: Part_Out
    assBlade: Optional[Part_Out] = None
    ratchet: Part_Out
    bit: Part_Out
    class Config:
        from_attributes = True

class Combo_In(BaseModel):
    isStock: bool
    line: Line_In
    lockChip: Optional[Part_In] = None
    blade: Part_In
    assBlade: Optional[Part_In] = None
    ratchet: Part_In
    bit: Part_In

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

@app.get("/me")
def get_me(current_user: Users = Depends(get_current_user)):
    return {"user": current_user, "user_type": current_user.user_type}

@app.get("/users/")
async def get_users(db: db_dependency, current_user: Users = Depends(get_current_user)):
    result = db.query(models.Users).all()
    if not result:
        raise HTTPException(status_code=404, detail="No users found")
    return result

@app.delete("/users/{user_id}")
async def delete_user(user_id:int, db: db_dependency, current_user: Users = Depends(get_current_user)):
    if current_user.user_type != 1: # type: ignore
        raise HTTPException(status_code=403, detail="Operation forbidden: Admins only")
    user = db.query(models.Users).filter(models.Users.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}

@app.post("/add-type")
def add_type(type: PartType_In, db: db_dependency, current_user: Users = Depends(get_current_user)):
    new_type = models.PartTypes(
        name=type.name
    )
    db.add(new_type)
    db.commit()
    db.refresh(new_type)
    return {"message": "Type added successfully", "type": new_type.name}

@app.get("/types", response_model=List[PartType_Out])
def get_types(db: db_dependency, current_user: Users = Depends(get_current_user)):
    result = db.query(models.PartTypes).all()
    if not result:
        raise HTTPException(status_code=404, detail="No types found")
    return result

@app.delete("/delete-type/{type_id}")
def delete_type(type_id: int, db: db_dependency, current_user: Users = Depends(get_current_user)):
    type = db.query(models.PartTypes).filter(models.PartTypes.id == type_id).first()
    if not type:
        raise HTTPException(status_code=404, detail="Type not found")
    db.delete(type)
    db.commit()
    return {"message": "Type deleted successfully"}

@app.post("/add-restriction")
def add_restriction(restriction: Restriction_Create, db: db_dependency, current_user: Users = Depends(get_current_user)):
    new_restriction = models.Restrictions(
        description=restriction.description
    )
    db.add(new_restriction)
    db.commit()
    db.refresh(new_restriction)
    return {"message": "Restriction added successfully", "restriction": new_restriction.description}

@app.get("/restrictions", response_model=List[Restriction_Out])
def get_restrictions(db: db_dependency, current_user: Users = Depends(get_current_user)):
    result = db.query(models.Restrictions).all()
    if not result:
        raise HTTPException(status_code=404, detail="No restrictions found")
    return result

@app.delete("/delete-restriction/{restriction_id}")
def delete_restriction(restriction_id: int, db: db_dependency, current_user: Users = Depends(get_current_user)):
    restriction = db.query(models.Restrictions).filter(models.Restrictions.id == restriction_id).first()
    if not restriction:
        raise HTTPException(status_code=404, detail="Restriction not found")
    db.delete(restriction)
    db.commit()
    return {"message": "Restriction deleted successfully"}

@app.post("/add-line")
def add_line(line: Line_In, db: db_dependency, current_user: Users = Depends(get_current_user)):
    new_line = models.Lines(
        name=line.name
    )
    db.add(new_line)
    db.commit()
    db.refresh(new_line)
    return {"message": "Line added successfully", "line": new_line.name}

@app.get("/lines", response_model=List[Line_Out])
def get_lines(db: db_dependency, current_user: Users = Depends(get_current_user)):
    result = db.query(models.Lines).all()
    if not result:
        raise HTTPException(status_code=404, detail="No lines found")
    return result

@app.delete("/delete-line/{line_id}")
def delete_line(line_id: int, db: db_dependency, current_user: Users = Depends(get_current_user)):
    line = db.query(models.Lines).filter(models.Lines.id == line_id).first()
    if not line:
        raise HTTPException(status_code=404, detail="Line not found")
    db.delete(line)
    db.commit()
    return {"message": "Line deleted successfully"}
#--------------------------------------------------------------------------------------------------------------------------
@app.post("/add-part")
def add_part(part: Part_In, db: db_dependency, current_user: Users = Depends(get_current_user)):
    found_restriction= None
    
    if part.restriction:
        found_restriction = db.query(models.Restrictions).filter(models.Restrictions.id == part.restriction.id).first()
        if not found_restriction:
            raise HTTPException(status_code=404, detail=f"Restriction with ID {part.restriction.id} not found")
 
    found_type = None
    found_type = db.query(models.PartTypes).filter(models.PartTypes.name == part.type.name).first()
    if not found_type:
        raise HTTPException(status_code=404, detail=f"Type with name '{part.type.name}' not found")
    
    stats = models.Stats(
        minAtk=part.stats.minAtk,
        maxAtk=part.stats.maxAtk,
        minDef=part.stats.minDef,
        maxDef=part.stats.maxDef,
        minStamina=part.stats.minStam,
        maxStamina=part.stats.maxStam,
        weight=part.stats.weight,
        burst=part.stats.burst,
        dash=part.stats.dash
    )
    db.add(stats)
    db.commit()
    db.refresh(stats)

    new_part = models.Parts(
        name=part.name,
        type=found_type.id,
        restriction=found_restriction.id if found_restriction else None
    )
    db.add(new_part)
    db.commit()
    db.refresh(new_part)
    return {"message": "Part added successfully", "part": new_part.name}

#--------------------------------------------------------------------------------------------------------------------------
@app.get("/parts", response_model=List[Part_Out])
def get_parts(db: db_dependency, current_user: Users = Depends(get_current_user)):
    result = db.query(models.Parts).all()
    if not result:
        raise HTTPException(status_code=404, detail="No parts found")
    return result

@app.patch("/update-part/{part_id}")
def update_part(part_id: int, part: Part_In, db: db_dependency, current_user: Users = Depends(get_current_user)):
    existing_part = db.query(models.Parts).filter(models.Parts.id == part_id).first()
    restriction_id = db.query(models.Restrictions).filter(models.Restrictions.id == part.restriction).first()
    type_id = db.query(models.PartTypes).filter(models.PartTypes.name == part.type).first()
    if not existing_part:
        raise HTTPException(status_code=404, detail="Part not found")
    setattr(existing_part, 'name', part.name)
    setattr(existing_part, 'type', type_id)
    setattr(existing_part, 'restriction', restriction_id)
    db.commit()
    db.refresh(existing_part)
    return {"message": "Part updated successfully", "part": existing_part.name}