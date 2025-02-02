import aio_pika
import logging
import traceback
from proto import parser_pb2
from app.services.aggregator import analyze_all

from app.config import settings

logger = logging.getLogger(__name__)


RABBITMQ_HOST = settings.RABBITMQ_HOST
RABBITMQ_PORT = settings.RABBITMQ_PORT
PARSE_QUEUE = settings.RABBITMQ_PARSE_QUEUE
RESULTS_QUEUE = settings.RABBITMQ_RESULTS_QUEUE
ANALYZE_QUEUE = settings.RABBITMQ_ANALYZE_QUEUE
RABBITMQ_USER = settings.RABBITMQ_USER
RABBITMQ_PASSWORD = settings.RABBITMQ_PASSWORD


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
        logger.info(f"Connected to RabbitMQ, listening to queue: {ANALYZE_QUEUE}")

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    try:
                        # Parse the message as ParseResponse
                        parse_response = parser_pb2.ParseResponse()
                        parse_response.ParseFromString(message.body)
                        correlation_id = parse_response.correlation_id
                        content = parse_response.content
                        url = parse_response.url

                        logger.info(
                            f"Analyzing content with correlation_id: {correlation_id}"
                        )

                        # Perform analysis
                        analyze_response = await analyze_all(content, url)
                        analyze_response.correlation_id = correlation_id

                        # Publish AnalyzeResponse to results_queue
                        await channel.default_exchange.publish(
                            aio_pika.Message(
                                body=analyze_response.SerializeToString(),
                                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                            ),
                            routing_key=RESULTS_QUEUE,
                        )
                        logger.info(
                            f"Published AnalyzeResponse to {RESULTS_QUEUE} with correlation_id: {correlation_id}"
                        )
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                        traceback.print_exc()
    except Exception as e:
        logger.critical(f"Failed to connect to RabbitMQ: {e}")
        raise
