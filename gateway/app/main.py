from fastapi import FastAPI
from app.routes.routes import router
from app.database import engine, Base

app = FastAPI(
    title="WebSite Optimization Gateway",
    description="API Gateway for parsing and analyzing web content",
    version="0.1.0",
)


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


app.include_router(router)
