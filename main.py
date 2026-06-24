#main.py
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models
from pydantic import BaseModel
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
# ✅ CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ✅ DB dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class StudentCreate(BaseModel):
    firstName: str
    lastName: str
    email: str
    course: str
    age: int

class Student(StudentCreate):
    id: int

    class Config:
        from_attributes = True

@app.post("/students", response_model=Student)
def add_student(student: StudentCreate, db: Session = Depends(get_db)):
    new_student = models.StudentDB(**student.dict())
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    return new_student

@app.get("/students", response_model=List[Student])
def get_students(db: Session = Depends(get_db)):
    return db.query(models.StudentDB).all()

@app.post("/students")
def add_student(student: Student, db: Session = Depends(get_db)):
    new_student = models.StudentDB(**student.dict())
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    return new_student

@app.put("/students/{student_id}")
def update_student(student_id: int, updated: Student, db: Session = Depends(get_db)):
    student = db.query(models.StudentDB).filter(models.StudentDB.id == student_id).first()

    if student:
        for key, value in updated.dict().items():
            setattr(student, key, value)

        db.commit()
        return student

    return {"error": "Student not found"}

@app.delete("/students/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(models.StudentDB).filter(models.StudentDB.id == student_id).first()

    if student:
        db.delete(student)
        db.commit()
        return {"message": "Deleted"}

    return {"error": "Student not found"}

class Login(BaseModel):
    username: str
    password: str

@app.post("/register")
def register(user: Login, db: Session = Depends(get_db)):
    new_user = models.UserDB(username=user.username, password=user.password)
    db.add(new_user)
    db.commit()
    return {"message": "User created"}

@app.post("/login")
def login(user: Login, db: Session = Depends(get_db)):
    db_user = db.query(models.UserDB).filter(
        models.UserDB.username == user.username,
        models.UserDB.password == user.password
    ).first()

    if db_user:
        return {"message": "Login successful"}
    
    return {"error": "Invalid credentials"}

@app.get("/students/{student_id}", response_model=Student)
def get_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(models.StudentDB).filter(models.StudentDB.id == student_id).first()
    if student:
        return student
    return {"error": "Student not found"}