import logging
import asyncio
from app.grpc.grpc_server import serve_grpc
from app.rabbitmq.rabbitmq_consumer import consume_parse_queue
from app.database.database import init_db


async def main():
    logging.basicConfig(level=logging.INFO)
    await init_db()
    await asyncio.gather(
        serve_grpc(),
        consume_parse_queue(),
    )


if __name__ == "__main__":
    asyncio.run(main())
