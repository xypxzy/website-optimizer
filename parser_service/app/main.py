import logging
import grpc
from concurrent import futures
from app.services.parser import ParserServicer
from proto import parser_pb2_grpc, parser_pb2

import pika
import os
import time
from threading import Thread

logger = logging.getLogger(__name__)

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))
PARSE_QUEUE = os.getenv("RABBITMQ_PARSE_QUEUE", "parse_queue")
ANALYZE_QUEUE = os.getenv("RABBITMQ_ANALYZE_QUEUE", "analyze_queue")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "user")  # Добавлено
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "password")  # Добавлено


def serve_grpc():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    parser_pb2_grpc.add_ParserServiceServicer_to_server(ParserServicer(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    logger.info("gRPC server started on port 50051.")
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


def consume_parse_queue():
    connection = connect_to_rabbitmq()
    channel = connection.channel()
    channel.queue_declare(queue=PARSE_QUEUE, durable=True)
    logger.info(f"Подключились к RabbitMQ, прослушиваем очередь: {PARSE_QUEUE}")

    def callback(ch, method, properties, body):
        logger.info("Получено сообщение из parse_queue.")
        try:
            parse_request = parser_pb2.ParseRequest()
            parse_request.ParseFromString(body)
            url = parse_request.url
            correlation_id = parse_request.correlation_id
            logger.info(f"Парсинг URL: {url} с correlation_id: {correlation_id}")

            # Обработка парсинга
            parser = ParserServicer()
            parse_response = parser.Parse(parse_request, None)
            parse_response.correlation_id = correlation_id  # Сохранение correlation_id

            # Публикация в analyze_queue
            channel.basic_publish(
                exchange="",
                routing_key=ANALYZE_QUEUE,
                body=parse_response.SerializeToString(),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Сделать сообщение постоянным
                ),
            )
            logger.info(
                f"Опубликовали parsed content в {ANALYZE_QUEUE} с correlation_id: {correlation_id}"
            )
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logger.error(f"Ошибка при обработке сообщения: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=PARSE_QUEUE, on_message_callback=callback)
    logger.info("Начали прослушивать parse_queue.")
    channel.start_consuming()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    grpc_thread = Thread(target=serve_grpc)
    grpc_thread.start()

    try:
        consume_parse_queue()
    except Exception as e:
        logger.critical(f"Не удалось запустить потребитель: {e}")
