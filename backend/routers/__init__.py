from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from . import student


from ..db import schemas
from ..db import crud, models, database
from . import api


mainrouter = APIRouter()
mainrouter.include_router(api.router)
mainrouter.include_router(student.router)