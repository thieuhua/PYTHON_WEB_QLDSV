from fastapi import FastAPI
from . import models, database
from .routers import items

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

app.include_router(items.router)
