from sqlalchemy import Column, Integer, String
from .database import Base
import enum

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String, nullable=True)


# # bảng users(id, username, password)

# class userRole(enum.Enum):
#     ADMIN = "admin"
#     STUDENT = "student"
#     TEACHER = "TEACHER"


# class User(Base):
#     __tablename__ = "users"

#     username = Column(String, primary_key = True, index = True)
#     password = Column(String)
#     role = Column(enum.Enum(userRole), default = userRole.STUDENT, nullable = False)


