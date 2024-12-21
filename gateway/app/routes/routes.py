from fastapi import APIRouter, Query, HTTPException
from google.protobuf.json_format import MessageToDict
from fastapi.responses import JSONResponse
import pika
import os
import uuid
import json
import logging
import threading
import asyncio

from proto.parser_pb2 import ParseRequest
from proto.analyzer_pb2 import AnalyzeResponse
from app.cache import redis
from app.models import AnalysisResult
from app.database import AsyncSessionLocal
from sqlalchemy.future import select

router = APIRouter()

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))
PARSE_QUEUE = os.getenv("RABBITMQ_PARSE_QUEUE", "parse_queue")
RESULTS_QUEUE = os.getenv("RABBITMQ_RESULTS_QUEUE", "results_queue")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "user")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "password")

logger = logging.getLogger("gateway")


def get_rabbitmq_connection():
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    return pika.BlockingConnection(
        pika.ConnectionParameters(
            host=RABBITMQ_HOST, port=RABBITMQ_PORT, credentials=credentials
        )
    )


@router.get("/healthcheck")
async def healthcheck():
    return JSONResponse(content={"status": "ok"})


@router.post("/analyze_url")
async def analyze_url(url: str = Query(..., description="The URL to analyze")):
    correlation_id = str(uuid.uuid4())

    # Сохранение начальной записи в PostgreSQL
    async with AsyncSessionLocal() as session:
        analysis = AnalysisResult(correlation_id=correlation_id, status="processing")
        session.add(analysis)
        await session.commit()

    # Публикация в parse_queue
    try:
        connection = get_rabbitmq_connection()
        channel = connection.channel()
        channel.queue_declare(queue=PARSE_QUEUE, durable=True)

        parse_request = ParseRequest(url=url, correlation_id=correlation_id)

        channel.basic_publish(
            exchange="",
            routing_key=PARSE_QUEUE,
            body=parse_request.SerializeToString(),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Сделать сообщение постоянным
            ),
        )
        connection.close()
        logger.info(
            f"Опубликовали ParseRequest в {PARSE_QUEUE} с correlation_id: {correlation_id}"
        )
    except Exception as e:
        logger.error(f"Не удалось опубликовать сообщение: {e}")
        raise HTTPException(
            status_code=500, detail=f"Не удалось опубликовать сообщение: {e}"
        )

    return {"message": "URL обрабатывается.", "correlation_id": correlation_id}


@router.get("/results/{correlation_id}")
async def get_results(correlation_id: str):
    # Попытка получить данные из Redis
    cached_result = await redis.get(correlation_id)
    if cached_result:
        return json.loads(cached_result)

    # Если нет в Redis, получить из PostgreSQL
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(AnalysisResult).where(
                AnalysisResult.correlation_id == correlation_id
            )
        )
        analysis = result.scalars().first()
        if not analysis:
            raise HTTPException(status_code=404, detail="Correlation ID не найден.")

        response = {
            "status": analysis.status,
            "frequency_distribution": analysis.frequency_distribution,
            "entities": analysis.entities,
        }

        # Кэшировать результат в Redis
        await redis.set(correlation_id, json.dumps(response), ex=3600)  # Кэш на 1 час

        return response


# Фоновая задача для прослушивания results_queue остается без изменений
def consume_results_queue():
    try:
        connection = get_rabbitmq_connection()
        channel = connection.channel()
        channel.queue_declare(queue=RESULTS_QUEUE, durable=True)
        logger.info(f"Подключились к RabbitMQ, прослушиваем очередь: {RESULTS_QUEUE}")

        def callback(ch, method, properties, body):
            logger.info("Получено сообщение из results_queue.")
            try:
                analyze_response = AnalyzeResponse()
                analyze_response.ParseFromString(body)
                correlation_id = analyze_response.correlation_id

                # Обновление результатов в PostgreSQL
                asyncio.run(update_results(correlation_id, analyze_response))

                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                logger.error(f"Ошибка при обработке результатов анализа: {e}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        async def update_results(correlation_id, analyze_response):
            async with AsyncSessionLocal() as session:
                analysis = await session.execute(
                    select(AnalysisResult).where(
                        AnalysisResult.correlation_id == correlation_id
                    )
                )
                analysis = analysis.scalars().first()
                if analysis:
                    analysis.status = "completed"
                    analysis.frequency_distribution = (
                        analyze_response.frequency_distribution
                    )
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
                    logger.info(
                        f"Обновили результаты для correlation_id: {correlation_id}"
                    )
                else:
                    logger.warning(
                        f"Получены результаты для неизвестного correlation_id: {correlation_id}"
                    )

        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(queue=RESULTS_QUEUE, on_message_callback=callback)
        logger.info("Начали прослушивать results_queue.")
        channel.start_consuming()
    except Exception as e:
        logger.error(f"Не удалось подключиться к RabbitMQ: {e}")


# Запуск фоновой задачи при старте приложения
grpc_thread = threading.Thread(target=consume_results_queue, daemon=True)
grpc_thread.start()
