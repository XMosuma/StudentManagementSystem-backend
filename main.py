from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models
from pydantic import BaseModel
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

ADMIN_SECRET_KEY = "1121"

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#Schemas
class StudentCreate(BaseModel):
    firstName: str
    lastName: str
    email: str
    course: str
    age: int
    homeAddress: Optional[str] = None
    contactNumber: Optional[str] = None
    gender: Optional[str] = None
    facebook: Optional[str] = None
    instagram: Optional[str] = None
    linkedin: Optional[str] = None

class Student(StudentCreate):
    id: int
    user_id: Optional[int] = None

    class Config:
        from_attributes = True

class Register(BaseModel):
    username: str
    password: str
    role: str = "student"
    secretKey: Optional[str] = None

class Login(BaseModel):
    username: str
    password: str

#Student routes
@app.get("/students", response_model=List[Student])
def get_students(db: Session = Depends(get_db)):
    return db.query(models.StudentDB).all()

@app.get("/students/{student_id}", response_model=Student)
def get_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(models.StudentDB).filter(models.StudentDB.id == student_id).first()
    if student:
        return student
    raise HTTPException(status_code=404, detail="Student not found")

@app.post("/students", response_model=Student)
def add_student(student: StudentCreate, db: Session = Depends(get_db)):
    new_student = models.StudentDB(**student.dict())
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    return new_student

@app.put("/students/{student_id}", response_model=Student)
def update_student(student_id: int, updated: StudentCreate, db: Session = Depends(get_db)):
    student = db.query(models.StudentDB).filter(models.StudentDB.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    for key, value in updated.dict().items():
        setattr(student, key, value)
    db.commit()
    db.refresh(student)
    return student

@app.delete("/students/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(models.StudentDB).filter(models.StudentDB.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # deactivate linked user account
    if student.user_id:
        user = db.query(models.UserDB).filter(models.UserDB.id == student.user_id).first()
        if user:
            user.is_active = False
            db.commit()

    db.delete(student)
    db.commit()
    return {"message": "Student deleted"}

#Profile route — student completes their profile after login
@app.post("/students/profile", response_model=Student)
def create_profile(student: StudentCreate, user_id: int, db: Session = Depends(get_db)):
    existing = db.query(models.StudentDB).filter(models.StudentDB.user_id == user_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Profile already exists")
    new_student = models.StudentDB(**student.dict(), user_id=user_id)
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    return new_student

@app.get("/students/profile/{user_id}", response_model=Student)
def get_profile(user_id: int, db: Session = Depends(get_db)):
    student = db.query(models.StudentDB).filter(models.StudentDB.user_id == user_id).first()
    if student:
        return student
    raise HTTPException(status_code=404, detail="Profile not found")

#Auth routes
@app.post("/register")
def register(user: Register, db: Session = Depends(get_db)):
    #check secret key for admin
    if user.role == "admin":
        if user.secretKey != ADMIN_SECRET_KEY:
            return {"error": "Invalid secret key for admin registration"}

    existing = db.query(models.UserDB).filter(models.UserDB.username == user.username).first()
    if existing:
        return {"error": "Username already exists"}

    new_user = models.UserDB(
        username=user.username,
        password=user.password,
        role=user.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created", "id": new_user.id, "role": new_user.role}

@app.post("/login")
def login(user: Login, db: Session = Depends(get_db)):
    db_user = db.query(models.UserDB).filter(
        models.UserDB.username == user.username,
        models.UserDB.password == user.password
    ).first()

    if not db_user:
        return {"error": "Invalid credentials"}

    # check if account was deactivated by admin
    if not db_user.is_active:
        return {"error": "Your account has been removed by admin. Please re-register."}

    return {
        "message": "Login successful",
        "role": db_user.role,
        "user_id": db_user.id,
        "username": db_user.username
    }