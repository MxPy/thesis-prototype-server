from fastapi import FastAPI
import models
from database import engine
from routers import autorizationAndAuthentication, appdevelopmnet
import uvicorn
import logging
import sys
import grpc
from concurrent import futures
import auth_pb2_grpc
import asyncio
logger = logging.getLogger()

ch = logging.StreamHandler(sys.stdout)
logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(funcName)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[ch]
    )


# models.Base.metadata.drop_all(bind = engine)
# models.Base.metadata.create_all(bind = engine)
async def serve():
    server = grpc.aio.server()
    auth_servicer = autorizationAndAuthentication.AuthServiceServicer()

    auth_pb2_grpc.add_AuthServiceServicer_to_server(auth_servicer, server)
    server.add_insecure_port('[::]:50051')
    logger.info("Server started on port 50051")
    await server.start()
    await server.wait_for_termination()

async def lifespan(app: FastAPI):
    loop = asyncio.get_event_loop()
    # await autorizationAndAuthentication.populate_admin("admin")
    # await autorizationAndAuthentication.populate_admin("doman")
    # Uruchomienie serwera gRPC w nowym wątku
    grpc_server = loop.create_task(serve())

    yield  # Tu aplikacja działa normalnie

    # Po zakończeniu działania aplikacji zatrzymaj serwer gRPC
    grpc_server.cancel()
    try:
        await grpc_server
    except asyncio.CancelledError:
        pass

app = FastAPI(
    lifespan=lifespan,
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
    uvicorn.run("main:app", host="0.0.0.0", port=8000, log_level="info", reload=True)

    