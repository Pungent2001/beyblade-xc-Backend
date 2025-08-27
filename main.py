from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Annotated, Optional
import models
from database import SessionLocal, engine
from sqlalchemy.orm import Session
from models import Users
import auth
from auth import get_current_user
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
    minSta: int
    maxSta: int
    weight: int
    burst: int
    dash: int

class Part_Out(BaseModel):
    id: int
    name: str
    type: int
    stats: Stat_Out
    restriction: Optional[Restriction_Out] = None
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
    line: int
    lockChip: Optional[int] = None
    blade: int
    assBlade: Optional[int] = None
    ratchet: int
    bit: int
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

@app.get("/me", response_model= User_Out,tags=["Users"])
def get_me(db: db_dependency, current_user: Users = Depends(get_current_user)):
    user = db.query(models.Users).filter(models.Users.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    string_user_type = db.query(models.UserTypes).filter(models.UserTypes.id == user.user_type).first()
    user.user_type = string_user_type.name if string_user_type else "Unknown" # type: ignore
    return user

@app.get("/Users/", tags=["Users"])
async def get_users(db: db_dependency, current_user: Users = Depends(get_current_user)):
    if current_user.user_type != 1: # type: ignore
        raise HTTPException(status_code=403, detail="Operation forbidden: Admins only")
    result = db.query(models.Users).all()
    if not result:
        raise HTTPException(status_code=404, detail="No users found")
    return result

@app.delete("/Users/{user_id}", tags=["Users"])
async def delete_user(user_id:int, db: db_dependency, current_user: Users = Depends(get_current_user)):
    if current_user.user_type != 1: # type: ignore
        raise HTTPException(status_code=403, detail="Operation forbidden: Admins only")
    user = db.query(models.Users).filter(models.Users.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}

@app.post("/Ownership", tags=["Ownership"])
def add_ownership(part_id: int, db: db_dependency, current_user: Users = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=404, detail="Aw hell naw spunch bop")
    part = db.query(models.Parts).filter(models.Parts.id == part_id).first()
    if not part:
        raise HTTPException(status_code=404, detail="Part not found")
    ownership = models.Ownerships(
        owner = current_user.id,
        part = part.id
    )
    db.add(ownership)
    db.commit()
    db.refresh(ownership)
    return {"message": "Ownership added successfully", "ownership": ownership}

@app.get("/Ownership", response_model=List[Part_Out], tags=["Ownership"])
def get_ownership(db: db_dependency, current_user: Users = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=404, detail="Aw hell naw spunch bop")
    result = db.query(models.Ownerships).filter(models.Ownerships.owner == current_user.id).all()
    if not result:
        raise HTTPException(status_code=404, detail="No ownership found")
    return result

@app.delete("/Ownership/{part_id}", tags=["Ownership"])
def delete_ownership(part_id: int, db: db_dependency, current_user: Users = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=404, detail="Aw hell naw spunch bop")
    ownership = db.query(models.Ownerships).filter(models.Ownerships.part == part_id, models.Ownerships.owner == current_user.id).first()
    if not ownership:
        raise HTTPException(status_code=404, detail="Ownership not found")
    db.delete(ownership)
    db.commit()
    return {"message": "Ownership deleted successfully"}

@app.post("/Combos", tags=["Combos"])
def add_combo(combo: Combo_In, db: db_dependency, current_user: Users = Depends(get_current_user)):
    new_combo = models.Combos(
        name=combo.description
    )
    db.add(new_combo)
    db.commit()
    db.refresh(new_combo)
    return {"message": "Combo added successfully", "combo": new_combo.name}

@app.get("/Combos", response_model=List[Combo_Out], tags=["Combos"])
def get_combos(db: db_dependency, type: str, current_user: Users = Depends(get_current_user)):
    query = db.query(models.Combos)
    if type:
        query = query.filter(models.Combos.type == type)
        if not query.first():
            raise HTTPException(status_code=404, detail="No combos of type found")
    result = query.all()
    if not result:
        raise HTTPException(status_code=404, detail="No combos found")
    return result

@app.delete("/Combos/{combo_id}", tags=["Combos"])
def delete_combo(combo_id: int, db: db_dependency, current_user: Users = Depends(get_current_user)):
    if current_user.user_type != 1: # type: ignore
        raise HTTPException(status_code=403, detail="Operation forbidden: Admins only")
    combo = db.query(models.Combos).filter(models.Combos.id == combo_id).first()
    if not combo:
        raise HTTPException(status_code=404, detail="Combo not found")
    db.delete(combo)
    db.commit()
    return {"message": "Combo deleted successfully"}

@app.post("/Types", tags=["Types"])
def add_type(type: PartType_In, db: db_dependency, current_user: Users = Depends(get_current_user)):
    if current_user.user_type != 1: # type: ignore
        raise HTTPException(status_code=403, detail="Operation forbidden: Admins only")
    new_type = models.PartTypes(
        name=type.name
    )
    db.add(new_type)
    db.commit()
    db.refresh(new_type)
    return {"message": "Type added successfully", "type": new_type.name}

@app.get("/Types", response_model=List[PartType_Out], tags=["Types"])
def get_types(db: db_dependency, current_user: Users = Depends(get_current_user)):
    result = db.query(models.PartTypes).all()
    if not result:
        raise HTTPException(status_code=404, detail="No types found")
    return result

@app.delete("/Types/{type_id}", tags=["Types"])
def delete_type(type_id: int, db: db_dependency, current_user: Users = Depends(get_current_user)):
    if current_user.user_type != 1: # type: ignore
        raise HTTPException(status_code=403, detail="Operation forbidden: Admins only")
    type = db.query(models.PartTypes).filter(models.PartTypes.id == type_id).first()
    if not type:
        raise HTTPException(status_code=404, detail="Type not found")
    db.delete(type)
    db.commit()
    return {"message": "Type deleted successfully"}

@app.post("/Restrictions", tags=["Restrictions"])
def add_restriction(restriction: Restriction_Create, db: db_dependency, current_user: Users = Depends(get_current_user)):
    if current_user.user_type != 1: # type: ignore
        raise HTTPException(status_code=403, detail="Operation forbidden: Admins only")
    new_restriction = models.Restrictions(
        description=restriction.description
    )
    db.add(new_restriction)
    db.commit()
    db.refresh(new_restriction)
    return {"message": "Restriction added successfully", "restriction": new_restriction.description}

@app.get("/Restrictions", response_model=List[Restriction_Out], tags=["Restrictions"])
def get_restrictions(db: db_dependency, current_user: Users = Depends(get_current_user)):
    result = db.query(models.Restrictions).all()
    if not result:
        raise HTTPException(status_code=404, detail="No restrictions found")
    return result

@app.delete("/Restrictions/{restriction_id}", tags=["Restrictions"])
def delete_restriction(restriction_id: int, db: db_dependency, current_user: Users = Depends(get_current_user)):
    if current_user.user_type != 1: # type: ignore
        raise HTTPException(status_code=403, detail="Operation forbidden: Admins only")
    restriction = db.query(models.Restrictions).filter(models.Restrictions.id == restriction_id).first()
    if not restriction:
        raise HTTPException(status_code=404, detail="Restriction not found")
    db.delete(restriction)
    db.commit()
    return {"message": "Restriction deleted successfully"}

@app.post("/Lines", tags=["Lines"])
def add_line(line: Line_In, db: db_dependency, current_user: Users = Depends(get_current_user)):
    if current_user.user_type != 1: # type: ignore
        raise HTTPException(status_code=403, detail="Operation forbidden: Admins only")
    new_line = models.Lines(
        name=line.name
    )
    db.add(new_line)
    db.commit()
    db.refresh(new_line)
    return {"message": "Line added successfully", "line": new_line.name}

@app.get("/Lines", response_model=List[Line_Out], tags=["Lines"])
def get_lines(db: db_dependency, current_user: Users = Depends(get_current_user)):
    result = db.query(models.Lines).all()
    if not result:
        raise HTTPException(status_code=404, detail="No lines found")
    return result

@app.delete("/Lines/{line_id}", tags=["Lines"])
def delete_line(line_id: int, db: db_dependency, current_user: Users = Depends(get_current_user)):
    if current_user.user_type != 1: # type: ignore
        raise HTTPException(status_code=403, detail="Operation forbidden: Admins only")
    line = db.query(models.Lines).filter(models.Lines.id == line_id).first()
    if not line:
        raise HTTPException(status_code=404, detail="Line not found")
    db.delete(line)
    db.commit()
    return {"message": "Line deleted successfully"}
#--------------------------------------------------------------------------------------------------------------------------
@app.post("/Parts", tags=["Parts"])
def add_part(part: Part_In, db: db_dependency, current_user: Users = Depends(get_current_user)):
    if current_user.user_type != 1: # type: ignore
        raise HTTPException(status_code=403, detail="Operation forbidden: Admins only")
    found_restriction= None
    
    if part.restriction:
        found_restriction = db.query(models.Restrictions).filter(models.Restrictions.id == part.restriction.id).first()
        if not found_restriction:
            raise HTTPException(status_code=404, detail=f"Restriction with ID {part.restriction.id} not found")
 
    found_type = None
    found_type = db.query(models.PartTypes).filter(models.PartTypes.name == part.type.name).first()
    if not found_type:
        raise HTTPException(status_code=404, detail=f"Type with name '{part.type.name}' not found")
    new_part = models.Parts(
        name=part.name,
        type=found_type.id,
        restriction=found_restriction.id if found_restriction else None
    )
    db.add(new_part)
    db.commit()
    db.refresh(new_part)
    created_part = db.query(models.Parts).filter(models.Parts.name == part.name).first()
    if not created_part:
        raise HTTPException(status_code=501, detail="Insertion failed, because part was not created")
    stats = models.Stats(
        id = created_part.id,
        minAtk=part.stats.minAtk,
        maxAtk=part.stats.maxAtk,
        minDef=part.stats.minDef,
        maxDef=part.stats.maxDef,
        minSta=part.stats.minSta,
        maxSta=part.stats.maxSta,
        weight=part.stats.weight,
        burst=part.stats.burst,
        dash=part.stats.dash
    )
    db.add(stats)
    db.commit()
    db.refresh(stats)
    part_stats= db.query(models.Stats).filter(models.Stats.id == created_part.id).first()
    if not part_stats:
        raise HTTPException(status_code=501, detail="Insertion failed, because part stats were not created")
    created_part.stats= part_stats.id
    db.commit()

    
    return {"message": "Part added successfully", "part": new_part.name}

#--------------------------------------------------------------------------------------------------------------------------
@app.get("/Parts", response_model=List[Part_Out], tags=["Parts"])
def get_parts(db: db_dependency, current_user: Users = Depends(get_current_user)):
    result = db.query(models.Parts).all()
    if not result:
        raise HTTPException(status_code=404, detail="No parts found")
    for part in result:
        stats= db.query(models.Stats).filter(models.Stats.id == part.stats).first()
        restriction=db.query(models.Restrictions).filter(models.Restrictions.id == part.restriction).first()
        if stats:
            part.stats = stats
        else:
            raise HTTPException(status_code=404, detail=f"Stats for part ID {part.id} not found")
        if restriction:
            part.restriction = restriction
    return result

@app.patch("/Parts/{part_id}", tags=["Parts"])
def update_part(part_id: int, part: Part_In, db: db_dependency, current_user: Users = Depends(get_current_user)):
    if current_user.user_type != 1: # type: ignore
        raise HTTPException(status_code=403, detail="Operation forbidden: Admins only")
    
    existing_part = db.query(models.Parts).filter(models.Parts.id == part_id).first() if part_id else None
    if not existing_part:
        raise HTTPException(status_code=404, detail="Part not found")
    
    type = db.query(models.PartTypes).filter(models.PartTypes.name == part.type.name).first()
    if not type:
        raise HTTPException(status_code=404, detail=f"Type with name '{part.type.name}' not found")

    existing_stats = db.query(models.Stats).filter(models.Stats.id == existing_part.stats).first()
    if not existing_stats:
        raise HTTPException(status_code=404, detail="Stats not found for the part")
    restriction = db.query(models.Restrictions).filter(models.Restrictions.id == part.restriction.id).first() if part.restriction else None
    
    existing_stats.minAtk = part.stats.minAtk # type: ignore
    existing_stats.maxAtk = part.stats.maxAtk # type: ignore
    existing_stats.minDef = part.stats.minDef # type: ignore
    existing_stats.maxDef = part.stats.maxDef # type: ignore
    existing_stats.minSta = part.stats.minSta # type: ignore
    existing_stats.maxSta = part.stats.maxSta # type: ignore
    existing_stats.weight = part.stats.weight # type: ignore
    existing_stats.burst = part.stats.burst # type: ignore
    existing_stats.dash = part.stats.dash # type: ignore

    existing_part.name = part.name # type: ignore
    existing_part.type = type.id
    existing_part.restriction = restriction.id if restriction else None # type: ignore
    db.commit()
    db.refresh(existing_part)
    return {"message": "Part updated successfully", "part": existing_part.name}

@app.delete("/Parts/{part_id}", tags=["Parts"])
def delete_part(part_id: int, db: db_dependency, current_user: Users = Depends(get_current_user)):
    if current_user.user_type != 1: # type: ignore
        raise HTTPException(status_code=403, detail="Operation forbidden: Admins only")

    existing_part = db.query(models.Parts).filter(models.Parts.id == part_id).first()
    if not existing_part:
        raise HTTPException(status_code=404, detail="Part not found")
    existing_stats = db.query(models.Stats).filter(models.Stats.id == existing_part.stats).first()
    if not existing_stats:
        raise HTTPException(status_code=404, detail="Stats not found for the part")
    db.delete(existing_part)
    db.delete(existing_stats)
    db.commit()
    return {"message": "Part deleted successfully"}