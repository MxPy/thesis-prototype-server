from fastapi import FastAPI
import models
from database import engine
from routers import autorizationAndAuthentication

models.Base.metadata.create_all(bind = engine)
app = FastAPI()

@app.get("/")
async def read_root():
	return {"Hello":"World"}


app.include_router(autorizationAndAuthentication.router)