import logging
import grpc
from concurrent import futures
from app.services.parser import ParserServicer
from proto import parser_pb2_grpc, parser_pb2

import aio_pika
import asyncio
import os
import traceback

logger = logging.getLogger(__name__)

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))
PARSE_QUEUE = os.getenv("RABBITMQ_PARSE_QUEUE", "parse_queue")
ANALYZE_QUEUE = os.getenv("RABBITMQ_ANALYZE_QUEUE", "analyze_queue")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "user")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "password")


async def serve_grpc():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    parser_pb2_grpc.add_ParserServiceServicer_to_server(ParserServicer(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    logger.info("gRPC server started on port 50051.")
    await asyncio.Event().wait()  # Блокируем основной поток


async def consume_parse_queue():
    try:
        connection = await aio_pika.connect_robust(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT,
            login=RABBITMQ_USER,
            password=RABBITMQ_PASSWORD,
        )
        channel = await connection.channel()
        await channel.set_qos(
            prefetch_count=10
        )  # Увеличиваем prefetch_count для параллельной обработки

        queue = await channel.declare_queue(PARSE_QUEUE, durable=True)
        logger.info(f"Подключились к RabbitMQ, прослушиваем очередь: {PARSE_QUEUE}")

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    try:
                        parse_request = parser_pb2.ParseRequest()
                        parse_request.ParseFromString(message.body)
                        url = parse_request.url
                        correlation_id = parse_request.correlation_id
                        logger.info(
                            f"Парсинг URL: {url} с correlation_id: {correlation_id}"
                        )

                        # Обработка парсинга
                        parser = ParserServicer()
                        parse_response = parser.Parse(parse_request, None)
                        parse_response.correlation_id = correlation_id

                        # Публикация в analyze_queue
                        await channel.default_exchange.publish(
                            aio_pika.Message(
                                body=parse_response.SerializeToString(),
                                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                            ),
                            routing_key=ANALYZE_QUEUE,
                        )
                        logger.info(
                            f"Опубликовали parsed content в {ANALYZE_QUEUE} с correlation_id: {correlation_id}"
                        )
                    except Exception as e:
                        logger.error(f"Ошибка при обработке сообщения: {e}")
                        traceback.print_exc()
    except Exception as e:
        logger.critical(f"Не удалось подключиться к RabbitMQ: {e}")
        raise


async def main():
    logging.basicConfig(level=logging.INFO)
    await asyncio.gather(
        serve_grpc(),
        consume_parse_queue(),
    )


if __name__ == "__main__":
    asyncio.run(main())
