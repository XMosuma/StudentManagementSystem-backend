from sqlalchemy import Column, Integer, String, Boolean, ForeignKey,Float
from database import Base

class StudentDB(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    firstName = Column(String)
    lastName = Column(String)
    email = Column(String)
    course = Column(String, nullable=True)
    age = Column(Integer)
    homeAddress = Column(String, nullable=True)
    contactNumber = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    facebook = Column(String, nullable=True)
    instagram = Column(String, nullable=True)
    linkedin = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_active = Column(Boolean, default=True)

class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password = Column(String)
    role = Column(String, default="student")
    is_active = Column(Boolean, default=True)

#Topics student wants to learn
class TopicDB(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))
    w3schools_url = Column(String, nullable=True)
    youtube_url = Column(String, nullable=True)

#Videos student is watching or completed
class VideoProgressDB(Base):
    __tablename__ = "video_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=True)
    title = Column(String)
    video_url = Column(String)
    status = Column(String, default="watching")


#Monthly stipend settings per student
class StipendDB(Base):
    __tablename__ = "stipends"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    amount = Column(Float, default=7000.0)
    month = Column(String)

#Budget categories
class BudgetCategoryDB(Base):
    __tablename__ = "budget_categories"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String)
    limit = Column(Float, default=0.0)
    is_default = Column(Boolean, default=False)

#Expenses
class ExpenseDB(Base):
    __tablename__ = "expenses"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    category_id = Column(Integer, ForeignKey("budget_categories.id"))
    category_name = Column(String)
    amount = Column(Float)
    description = Column(String, nullable=True)
    date = Column(String)
    month = Column(String)