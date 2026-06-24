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

# =====================
#SCHEMAS
# =====================

class StudentCreate(BaseModel):
    firstName: str
    lastName: str
    email: str
    course: Optional[str] = None
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

class TopicCreate(BaseModel):
    name: str
    user_id: int

class Topic(TopicCreate):
    id: int
    w3schools_url: Optional[str] = None
    youtube_url: Optional[str] = None

    class Config:
        from_attributes = True

class VideoProgressCreate(BaseModel):
    user_id: int
    topic_id: Optional[int] = None
    title: str
    video_url: str
    status: str = "watching"

class VideoProgress(VideoProgressCreate):
    id: int

    class Config:
        from_attributes = True

# =====================
#STUDENT ROUTES
# =====================

@app.get("/students", response_model=List[Student])
def get_students(db: Session = Depends(get_db)):
    return db.query(models.StudentDB).filter(models.StudentDB.is_active == True).all()

@app.get("/students/profile/{user_id}", response_model=Student)
def get_profile(user_id: int, db: Session = Depends(get_db)):
    student = db.query(models.StudentDB).filter(models.StudentDB.user_id == user_id).first()
    if student:
        return student
    raise HTTPException(status_code=404, detail="Profile not found")

@app.get("/students/{student_id}", response_model=Student)
def get_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(models.StudentDB).filter(models.StudentDB.id == student_id).first()
    if student:
        return student
    raise HTTPException(status_code=404, detail="Student not found")

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

    # deactivate user account but keep student record intact
    if student.user_id:
        user = db.query(models.UserDB).filter(models.UserDB.id == student.user_id).first()
        if user:
            user.is_active = False
            db.commit()

    # don't delete the student record — just hide them from the list
    student.is_active = False
    db.commit()
    return {"message": "Student deleted"}
# =====================
#AUTH ROUTES
# =====================

@app.post("/register")
def register(user: Register, db: Session = Depends(get_db)):
    if user.role == "admin":
        if user.secretKey != ADMIN_SECRET_KEY:
            return {"error": "Invalid secret key for admin registration"}

    existing = db.query(models.UserDB).filter(models.UserDB.username == user.username).first()

    if existing:
        if not existing.is_active:
            #reactivate user
            existing.is_active = True
            existing.password = user.password
            existing.role = user.role
            db.commit()

            #reactivate their student record too
            student = db.query(models.StudentDB).filter(
                models.StudentDB.user_id == existing.id
            ).first()
            if student:
                student.is_active = True
                db.commit()

            return {"message": "Account reactivated successfully", "id": existing.id, "role": existing.role}
        else:
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
    if not db_user.is_active:
        return {"error": "Your account has been removed by admin. Please re-register."}
    return {
        "message": "Login successful",
        "role": db_user.role,
        "user_id": db_user.id,
        "username": db_user.username
    }

# =====================
#TOPIC ROUTES
# =====================

@app.post("/topics", response_model=Topic)
def add_topic(topic: TopicCreate, db: Session = Depends(get_db)):
    keyword = topic.name.replace(" ", "+")
    w3schools_url = f"https://www.w3schools.com/{topic.name.lower()}/"
    youtube_url = f"https://www.youtube.com/results?search_query={keyword}+tutorial"

    # =====================
    #YouTube API
    # =====================
    # import requests
    # YOUTUBE_API_KEY = "YOUR_API_KEY_HERE"
    # api_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={topic.name}+tutorial&type=video&key={YOUTUBE_API_KEY}&maxResults=5"
    # response = requests.get(api_url)
    # videos = response.json().get("items", [])
    # youtube_url = f"https://www.youtube.com/watch?v={videos[0]['id']['videoId']}" if videos else youtube_url
    # =====================

    new_topic = models.TopicDB(
        name=topic.name,
        user_id=topic.user_id,
        w3schools_url=w3schools_url,
        youtube_url=youtube_url
    )
    db.add(new_topic)
    db.commit()
    db.refresh(new_topic)
    return new_topic

@app.get("/topics/{user_id}", response_model=List[Topic])
def get_topics(user_id: int, db: Session = Depends(get_db)):
    return db.query(models.TopicDB).filter(models.TopicDB.user_id == user_id).all()

@app.delete("/topics/{topic_id}")
def delete_topic(topic_id: int, db: Session = Depends(get_db)):
    topic = db.query(models.TopicDB).filter(models.TopicDB.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    db.delete(topic)
    db.commit()
    return {"message": "Topic removed"}

# =====================
#VIDEO PROGRESS ROUTES
# =====================

@app.post("/videos", response_model=VideoProgress)
def add_video(video: VideoProgressCreate, db: Session = Depends(get_db)):
    new_video = models.VideoProgressDB(**video.dict())
    db.add(new_video)
    db.commit()
    db.refresh(new_video)
    return new_video

@app.get("/videos/{user_id}", response_model=List[VideoProgress])
def get_videos(user_id: int, db: Session = Depends(get_db)):
    return db.query(models.VideoProgressDB).filter(
        models.VideoProgressDB.user_id == user_id
    ).all()

@app.put("/videos/{video_id}")
def update_video_status(video_id: int, status: str, db: Session = Depends(get_db)):
    video = db.query(models.VideoProgressDB).filter(models.VideoProgressDB.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    video.status = status
    db.commit()
    return {"message": "Status updated"}

@app.delete("/videos/{video_id}")
def delete_video(video_id: int, db: Session = Depends(get_db)):
    video = db.query(models.VideoProgressDB).filter(models.VideoProgressDB.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    db.delete(video)
    db.commit()
    return {"message": "Video removed"}

# =====================
#ADMIN — student progress
# =====================

@app.get("/admin/student-progress/{user_id}")
def get_student_progress(user_id: int, db: Session = Depends(get_db)):
    topics = db.query(models.TopicDB).filter(models.TopicDB.user_id == user_id).all()
    videos = db.query(models.VideoProgressDB).filter(models.VideoProgressDB.user_id == user_id).all()
    return {
        "topics": [{"id": t.id, "name": t.name, "w3schools_url": t.w3schools_url, "youtube_url": t.youtube_url} for t in topics],
        "videos": [{"id": v.id, "title": v.title, "video_url": v.video_url, "status": v.status} for v in videos]
    }

# =====================
#BUDGET SCHEMAS
# =====================

class StipendUpdate(BaseModel):
    amount: float
    month: str

class BudgetCategoryCreate(BaseModel):
    user_id: int
    name: str
    limit: float = 0.0
    is_default: bool = False

class BudgetCategory(BudgetCategoryCreate):
    id: int
    class Config:
        from_attributes = True

class ExpenseCreate(BaseModel):
    user_id: int
    category_id: int
    category_name: str
    amount: float
    description: Optional[str] = None
    date: str
    month: str

class Expense(ExpenseCreate):
    id: int
    class Config:
        from_attributes = True

# =====================
#STIPEND ROUTES
# =====================

@app.get("/stipend/{user_id}")
def get_stipend(user_id: int, db: Session = Depends(get_db)):
    stipend = db.query(models.StipendDB).filter(
        models.StipendDB.user_id == user_id
    ).first()
    if not stipend:
        #create default stipend
        from datetime import datetime
        month = datetime.now().strftime("%Y-%m")
        stipend = models.StipendDB(user_id=user_id, amount=7000.0, month=month)
        db.add(stipend)
        db.commit()
        db.refresh(stipend)
    return {"id": stipend.id, "amount": stipend.amount, "month": stipend.month}

@app.put("/stipend/{user_id}")
def update_stipend(user_id: int, data: StipendUpdate, db: Session = Depends(get_db)):
    stipend = db.query(models.StipendDB).filter(
        models.StipendDB.user_id == user_id
    ).first()
    if stipend:
        stipend.amount = data.amount
        stipend.month = data.month
    else:
        stipend = models.StipendDB(user_id=user_id, amount=data.amount, month=data.month)
        db.add(stipend)
    db.commit()
    return {"message": "Stipend updated"}

# =====================
#BUDGET CATEGORY ROUTES
# =====================

@app.get("/budget/categories/{user_id}", response_model=List[BudgetCategory])
def get_categories(user_id: int, db: Session = Depends(get_db)):
    categories = db.query(models.BudgetCategoryDB).filter(
        models.BudgetCategoryDB.user_id == user_id
    ).all()
    if not categories:
        #create default categories
        defaults = ["Food", "Transport", "Entertainment", "Education", "Clothing", "Other"]
        for name in defaults:
            cat = models.BudgetCategoryDB(
                user_id=user_id, name=name, limit=0.0, is_default=True
            )
            db.add(cat)
        db.commit()
        categories = db.query(models.BudgetCategoryDB).filter(
            models.BudgetCategoryDB.user_id == user_id
        ).all()
    return categories

@app.post("/budget/categories", response_model=BudgetCategory)
def add_category(category: BudgetCategoryCreate, db: Session = Depends(get_db)):
    new_cat = models.BudgetCategoryDB(**category.dict())
    db.add(new_cat)
    db.commit()
    db.refresh(new_cat)
    return new_cat

@app.put("/budget/categories/{category_id}")
def update_category_limit(category_id: int, limit: float, db: Session = Depends(get_db)):
    cat = db.query(models.BudgetCategoryDB).filter(
        models.BudgetCategoryDB.id == category_id
    ).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    cat.limit = limit
    db.commit()
    return {"message": "Limit updated"}

@app.delete("/budget/categories/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db)):
    cat = db.query(models.BudgetCategoryDB).filter(
        models.BudgetCategoryDB.id == category_id
    ).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    if cat.is_default:
        raise HTTPException(status_code=400, detail="Cannot delete default category")
    db.delete(cat)
    db.commit()
    return {"message": "Category deleted"}

# =====================
#EXPENSE ROUTES
# =====================

@app.get("/expenses/{user_id}")
def get_expenses(user_id: int, month: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(models.ExpenseDB).filter(models.ExpenseDB.user_id == user_id)
    if month:
        query = query.filter(models.ExpenseDB.month == month)
    return query.all()

@app.post("/expenses", response_model=Expense)
def add_expense(expense: ExpenseCreate, db: Session = Depends(get_db)):
    new_expense = models.ExpenseDB(**expense.dict())
    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)
    return new_expense

@app.delete("/expenses/{expense_id}")
def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    expense = db.query(models.ExpenseDB).filter(
        models.ExpenseDB.id == expense_id
    ).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    db.delete(expense)
    db.commit()
    return {"message": "Expense deleted"}

# =====================
#BUDGET OVERVIEW
# =====================

@app.get("/budget/overview/{user_id}")
def get_overview(user_id: int, month: str, db: Session = Depends(get_db)):
    stipend = db.query(models.StipendDB).filter(
        models.StipendDB.user_id == user_id
    ).first()
    stipend_amount = stipend.amount if stipend else 7000.0

    expenses = db.query(models.ExpenseDB).filter(
        models.ExpenseDB.user_id == user_id,
        models.ExpenseDB.month == month
    ).all()

    categories = db.query(models.BudgetCategoryDB).filter(
        models.BudgetCategoryDB.user_id == user_id
    ).all()

    total_spent = sum(e.amount for e in expenses)
    remaining = stipend_amount - total_spent

    # per category breakdown
    breakdown = []
    for cat in categories:
        cat_expenses = [e for e in expenses if e.category_id == cat.id]
        spent = sum(e.amount for e in cat_expenses)
        breakdown.append({
            "id": cat.id,
            "name": cat.name,
            "limit": cat.limit,
            "spent": spent,
            "exceeded": cat.limit > 0 and spent > cat.limit
        })

    # monthly history — last 6 months
    from datetime import datetime, timedelta
    history = []
    for i in range(5, -1, -1):
        d = datetime.now().replace(day=1) - timedelta(days=i*30)
        m = d.strftime("%Y-%m")
        m_expenses = db.query(models.ExpenseDB).filter(
            models.ExpenseDB.user_id == user_id,
            models.ExpenseDB.month == m
        ).all()
        history.append({"month": m, "spent": sum(e.amount for e in m_expenses)})

    return {
        "stipend": stipend_amount,
        "total_spent": total_spent,
        "remaining": remaining,
        "breakdown": breakdown,
        "history": history
    }

# =====================
#ADMIN — view student budget
# =====================

@app.get("/admin/budget/{user_id}")
def admin_view_budget(user_id: int, month: str, db: Session = Depends(get_db)):
    return get_overview(user_id, month, db)