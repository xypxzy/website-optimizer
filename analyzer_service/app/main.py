import logging
import traceback
import grpc
from concurrent import futures
from app.services.text_analyzer import TextAnalyzerServicer
from proto import analyzer_pb2_grpc, analyzer_pb2

import pika
import os
import time
from threading import Thread

logger = logging.getLogger(__name__)

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))
ANALYZE_QUEUE = os.getenv("RABBITMQ_ANALYZE_QUEUE", "analyze_queue")
RESULTS_QUEUE = os.getenv("RABBITMQ_RESULTS_QUEUE", "results_queue")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "user")  # Добавлено
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "password")  # Добавлено


def serve_grpc():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    analyzer_pb2_grpc.add_AnalyzerServiceServicer_to_server(
        TextAnalyzerServicer(), server
    )
    server.add_insecure_port("[::]:50052")
    server.start()
    logger.info("gRPC server started on port 50052.")
    server.wait_for_termination()


def connect_to_rabbitmq():
    retries = 5
    delay = 5  # секунды
    for attempt in range(1, retries + 1):
        try:
            credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=RABBITMQ_HOST, port=RABBITMQ_PORT, credentials=credentials
                )
            )
            logger.info(
                f"Успешно подключились к RabbitMQ на {RABBITMQ_HOST}:{RABBITMQ_PORT}"
            )
            return connection
        except pika.exceptions.AMQPConnectionError as e:
            logger.error(f"Попытка {attempt} из {retries} не удалась: {e}")
            if attempt < retries:
                logger.info(f"Повторная попытка через {delay} секунд...")
                time.sleep(delay)
            else:
                logger.critical(
                    "Не удалось подключиться к RabbitMQ после нескольких попыток."
                )
                raise


def consume_analyze_queue():
    connection = connect_to_rabbitmq()
    channel = connection.channel()
    channel.queue_declare(queue=ANALYZE_QUEUE, durable=True)
    channel.queue_declare(queue=RESULTS_QUEUE, durable=True)
    logger.info(f"Подключились к RabbitMQ, прослушиваем очередь: {ANALYZE_QUEUE}")

    def callback(ch, method, properties, body):
        logger.info("Получено сообщение из analyze_queue.")
        try:
            analyze_request = analyzer_pb2.AnalyzeRequest()
            analyze_request.ParseFromString(body)
            content = analyze_request.content
            correlation_id = analyze_request.correlation_id
            logger.info(f"Анализ содержимого с correlation_id: {correlation_id}")

            # Обработка анализа
            analyzer = TextAnalyzerServicer()
            analyze_response = analyzer.Analyze(analyze_request, None)
            analyze_response.correlation_id = (
                correlation_id  # Сохранение correlation_id
            )

            # Публикация в results_queue
            channel.basic_publish(
                exchange="",
                routing_key=RESULTS_QUEUE,
                body=analyze_response.SerializeToString(),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Сделать сообщение постоянным
                ),
            )
            logger.info(
                f"Опубликовали результаты анализа в {RESULTS_QUEUE} с correlation_id: {correlation_id}"
            )
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logger.error(f"Ошибка при обработке анализа: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=ANALYZE_QUEUE, on_message_callback=callback)
    logger.info("Начали прослушивать analyze_queue.")
    channel.start_consuming()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    grpc_thread = Thread(target=serve_grpc)
    grpc_thread.start()

    try:
        consume_analyze_queue()
    except Exception as e:
        logger.critical(f"Не удалось запустить потребитель: {e}")
