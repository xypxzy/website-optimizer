import logging
import grpc
from concurrent import futures
from app.services.text_analyzer import TextAnalyzerServicer
from proto import analyzer_pb2_grpc, analyzer_pb2

import aio_pika
import asyncio
import os
import traceback
import json
from google.protobuf.json_format import MessageToDict
from sqlalchemy.exc import SQLAlchemyError

from app.database import engine, Base, AsyncSessionLocal
from app.cache import redis
from app.models import AnalysisResult
from sqlalchemy.future import select

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
                        analyze_response = analyzer_pb2.AnalyzeResponse()
                        analyze_response.ParseFromString(message.body)
                        correlation_id = analyze_response.correlation_id

                        logger.info(
                            f"Анализ содержимого с correlation_id: {correlation_id}"
                        )

                        await update_results(correlation_id, analyze_response)

                        logger.info(
                            f"Обработали анализ для correlation_id: {correlation_id}"
                        )

                    except Exception as e:
                        logger.error(f"Ошибка при обработке анализа: {e}")
                        traceback.print_exc()
    except Exception as e:
        logger.critical(f"Не удалось подключиться к RabbitMQ: {e}")
        raise


async def update_results(correlation_id, analyze_response):
    async with AsyncSessionLocal() as session:
        try:
            # Получаем запись для обновления
            result = await session.execute(
                select(AnalysisResult).where(
                    AnalysisResult.correlation_id == correlation_id
                )
            )
            analysis = result.scalars().first()
            if analysis:
                analysis.status = "completed"
                # Конвертация frequency_distribution в стандартный dict
                analysis.frequency_distribution = MessageToDict(
                    analyze_response.frequency_distribution
                )
                # Конвертация entities в список dict
                analysis.entities = [
                    MessageToDict(entity) for entity in analyze_response.entities
                ]
                await session.commit()

                # Обновление кэша в Redis
                response = {
                    "status": analysis.status,
                    "frequency_distribution": analysis.frequency_distribution,
                    "entities": analysis.entities,
                }
                await redis.set(
                    correlation_id, json.dumps(response), ex=3600
                )  # Кэш на 1 час
                logger.info(f"Обновили результаты для correlation_id: {correlation_id}")
            else:
                logger.warning(
                    f"Получены результаты для неизвестного correlation_id: {correlation_id}"
                )
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Ошибка при обновлении записи в базе данных: {e}")
            raise
        except Exception as e:
            logger.error(f"Неизвестная ошибка при обновлении результатов: {e}")
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
