from fastapi import FastAPI
from app.routes.routes import router

app = FastAPI(
    title="WebSite Optimization Gateway",
    description="API Gateway for parsing and analyzing web content",
    version="0.1.0",
)

app.include_router(router)
