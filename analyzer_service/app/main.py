import logging
import traceback
import grpc
from concurrent import futures
from app.services.text_analyzer import TextAnalyzerServicer
from proto import analyzer_pb2_grpc, analyzer_pb2

import aio_pika
import asyncio
import os

logger = logging.getLogger(__name__)

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))
ANALYZE_QUEUE = os.getenv("RABBITMQ_ANALYZE_QUEUE", "analyze_queue")
RESULTS_QUEUE = os.getenv("RABBITMQ_RESULTS_QUEUE", "results_queue")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "user")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "password")


async def serve_grpc():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    analyzer_pb2_grpc.add_AnalyzerServiceServicer_to_server(
        TextAnalyzerServicer(), server
    )
    server.add_insecure_port("[::]:50052")
    server.start()
    logger.info("gRPC server started on port 50052.")
    await asyncio.Event().wait()


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

        await channel.declare_queue(ANALYZE_QUEUE, durable=True)
        await channel.declare_queue(RESULTS_QUEUE, durable=True)
        logger.info(f"Подключились к RabbitMQ, прослушиваем очередь: {ANALYZE_QUEUE}")

        queue = await channel.declare_queue(ANALYZE_QUEUE, durable=True)

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    try:
                        analyze_request = analyzer_pb2.AnalyzeRequest()
                        analyze_request.ParseFromString(message.body)
                        content = analyze_request.content
                        correlation_id = analyze_request.correlation_id
                        logger.info(
                            f"Анализ содержимого с correlation_id: {correlation_id}"
                        )

                        # Обработка анализа
                        analyzer = TextAnalyzerServicer()
                        analyze_response = analyzer.Analyze(analyze_request, None)
                        analyze_response.correlation_id = correlation_id

                        # Публикация в results_queue
                        await channel.default_exchange.publish(
                            aio_pika.Message(
                                body=analyze_response.SerializeToString(),
                                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                            ),
                            routing_key=RESULTS_QUEUE,
                        )
                        logger.info(
                            f"Опубликовали результаты анализа в {RESULTS_QUEUE} с correlation_id: {correlation_id}"
                        )
                    except Exception as e:
                        logger.error(f"Ошибка при обработке анализа: {e}")
                        traceback.print_exc()
    except Exception as e:
        logger.critical(f"Не удалось подключиться к RabbitMQ: {e}")
        raise


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    await asyncio.gather(
        serve_grpc(),
        consume_analyze_queue(),
    )


if __name__ == "__main__":
    asyncio.run(main())
