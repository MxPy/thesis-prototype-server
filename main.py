from fastapi import FastAPI
import models
from database import engine
from routers import autorizationAndAuthentication, appdevelopmnet
import uvicorn


models.Base.metadata.drop_all(bind = engine)
models.Base.metadata.create_all(bind = engine)
app = FastAPI(
    title="A&A Prototype",
    summary="Prototype Authentication and Authorization Server for mobile app development",
)

origins = [
    "http://localhost:3000",
]


@app.get("/")
async def read_root():
	return {"Hello":"World"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

app.include_router(autorizationAndAuthentication.router)
app.include_router(appdevelopmnet.router)

if __name__ == '__main__':
    uvicorn.run("main:app", host="0.0.0.0", port=8000, log_level="info")