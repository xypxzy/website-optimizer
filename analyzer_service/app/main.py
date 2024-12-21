import logging
import grpc
from concurrent import futures
from proto import parser_pb2, analyzer_pb2, analyzer_pb2_grpc
import aio_pika
import asyncio
import os
import traceback

from app.database import engine, Base
from app.services.text_analyzer import TextAnalyzerServicer

logger = logging.getLogger(__name__)

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))
ANALYZE_QUEUE = os.getenv("RABBITMQ_ANALYZE_QUEUE", "analyze_queue")
RESULTS_QUEUE = os.getenv("RABBITMQ_RESULTS_QUEUE", "results_queue")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "user")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "password")


async def serve_grpc():
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    analyzer_pb2_grpc.add_AnalyzerServiceServicer_to_server(
        TextAnalyzerServicer(), server
    )
    server.add_insecure_port("[::]:50052")
    await server.start()
    logger.info("gRPC сервер запущен на порту 50052.")
    await server.wait_for_termination()


async def consume_analyze_queue():
    try:
        connection = await aio_pika.connect_robust(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT,
            login=RABBITMQ_USER,
            password=RABBITMQ_PASSWORD,
        )
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=10)

        queue = await channel.declare_queue(ANALYZE_QUEUE, durable=True)
        logger.info(f"Подключились к RabbitMQ, прослушиваем очередь: {ANALYZE_QUEUE}")

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    try:
                        # Разбираем сообщение как ParseResponse
                        parse_response = parser_pb2.ParseResponse()
                        parse_response.ParseFromString(message.body)
                        correlation_id = parse_response.correlation_id
                        content = parse_response.content

                        logger.info(
                            f"Анализ содержимого с correlation_id: {correlation_id}"
                        )

                        # Создаем AnalyzeRequest из ParseResponse
                        analyze_request = analyzer_pb2.AnalyzeRequest(
                            correlation_id=correlation_id, content=content
                        )

                        # Выполняем анализ
                        text_analyzer = TextAnalyzerServicer()
                        analyze_response = await text_analyzer.Analyze(
                            analyze_request, None
                        )

                        # Публикуем AnalyzeResponse в results_queue
                        await channel.default_exchange.publish(
                            aio_pika.Message(
                                body=analyze_response.SerializeToString(),
                                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                            ),
                            routing_key=RESULTS_QUEUE,
                        )
                        logger.info(
                            f"Опубликовали AnalyzeResponse в {RESULTS_QUEUE} с correlation_id: {correlation_id}"
                        )
                    except Exception as e:
                        logger.error(f"Ошибка при обработке сообщения: {e}")
                        traceback.print_exc()
    except Exception as e:
        logger.critical(f"Не удалось подключиться к RabbitMQ: {e}")
        raise


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
