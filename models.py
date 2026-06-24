from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from database import Base

class StudentDB(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    firstName = Column(String)
    lastName = Column(String)
    email = Column(String)
    course = Column(String)
    age = Column(Integer)
    homeAddress = Column(String, nullable=True)
    contactNumber = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    facebook = Column(String, nullable=True)
    instagram = Column(String, nullable=True)
    linkedin = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password = Column(String)
    role = Column(String, default="student")
    is_active = Column(Boolean, default=True)