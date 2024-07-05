from fastapi import FastAPI
import models
from database import engine
from routers import autorizationAndAuthentication, appdevelopmnet

models.Base.metadata.create_all(bind = engine)
app = FastAPI(
    title="A&A Prototype",
    summary="Prototype Authentication and Authorization Server for mobile app development",
)

@app.get("/")
async def read_root():
	return {"Hello":"World"}


app.include_router(autorizationAndAuthentication.router)
app.include_router(appdevelopmnet.router)