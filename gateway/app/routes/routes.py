from fastapi import APIRouter, Query, HTTPException
import grpc
from google.protobuf.json_format import MessageToDict
import pika
import os
import uuid
import json
import logging
import threading  # Добавлено

from proto.parser_pb2_grpc import ParserServiceStub
from proto.parser_pb2 import ParseRequest
from proto.analyzer_pb2_grpc import AnalyzerServiceStub
from proto.analyzer_pb2 import AnalyzeRequest, AnalyzeResponse

router = APIRouter()

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))
PARSE_QUEUE = os.getenv("RABBITMQ_PARSE_QUEUE", "parse_queue")
RESULTS_QUEUE = os.getenv("RABBITMQ_RESULTS_QUEUE", "results_queue")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "user")  # Добавлено
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "password")  # Добавлено


def get_rabbitmq_connection():
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    return pika.BlockingConnection(
        pika.ConnectionParameters(
            host=RABBITMQ_HOST, port=RABBITMQ_PORT, credentials=credentials
        )
    )


# In-memory storage for results (можно заменить на базу данных или Redis)
results_store = {}
lock = threading.Lock()
logger = logging.getLogger("gateway")


@router.get("/healthcheck")
def healthcheck():
    return {"status": "ok"}


@router.post("/analyze_url")
def analyze_url(url: str = Query(..., description="The URL to analyze")):
    correlation_id = str(uuid.uuid4())

    # Инициализация хранилища для результатов
    with lock:
        results_store[correlation_id] = {"status": "processing"}

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
def get_results(correlation_id: str):
    with lock:
        result = results_store.get(correlation_id)
    if not result:
        raise HTTPException(status_code=404, detail="Correlation ID не найден.")
    return result


# Фоновая задача для прослушивания results_queue
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

                # Обновление результатов в хранилище
                with lock:
                    if correlation_id in results_store:
                        results_store[correlation_id] = {
                            "status": "completed",
                            "frequency_distribution": analyze_response.frequency_distribution,
                            "entities": [
                                MessageToDict(entity)
                                for entity in analyze_response.entities
                            ],
                        }
                        logger.info(
                            f"Обновили результаты для correlation_id: {correlation_id}"
                        )
                    else:
                        logger.warning(
                            f"Получены результаты для неизвестного correlation_id: {correlation_id}"
                        )

                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                logger.error(f"Ошибка при обработке результатов анализа: {e}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(queue=RESULTS_QUEUE, on_message_callback=callback)
        logger.info("Начали прослушивать results_queue.")
        channel.start_consuming()
    except Exception as e:
        logger.error(f"Не удалось подключиться к RabbitMQ: {e}")


# Запуск фоновой задачи при старте приложения
grpc_thread = threading.Thread(target=consume_results_queue, daemon=True)
grpc_thread.start()
