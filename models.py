#models.py
from sqlalchemy import Column, Integer, String
from database import Base

# ✅ Student table
class StudentDB(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    firstName = Column(String)
    lastName = Column(String)
    email = Column(String)
    course = Column(String)
    age = Column(Integer)

# ✅ User table
class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password = Column(String)
