import logging
import asyncio
from app.database.database import engine, Base
from app.grpc.grpc_server import serve_grpc
from app.rabbitmq.rabbitmq_consumer import consume_analyze_queue


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await asyncio.gather(
        serve_grpc(),
        consume_analyze_queue(),
    )


if __name__ == "__main__":
    asyncio.run(main())
