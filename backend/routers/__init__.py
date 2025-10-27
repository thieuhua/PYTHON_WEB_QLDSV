from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from . import student  # Import student router
from . import api      # Import api router

from ..db import schemas
from ..db import crud, models, database

# Tạo main router
mainrouter = APIRouter()

# Include các sub-routers
mainrouter.include_router(api.router)
mainrouter.include_router(student.router)