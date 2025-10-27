from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session


from ..db import schemas
from ..db import crud, models, database
from . import api, student, teacher

# Tạo main router
mainrouter = APIRouter()

# Include các sub-routers
mainrouter.include_router(api.router)
mainrouter.include_router(student.router)
mainrouter.include_router(teacher.router)