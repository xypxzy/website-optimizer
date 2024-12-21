import aio_pika
import traceback
import logging
from proto import parser_pb2
from app.models.models import ParsedData
from app.database.database import AsyncSessionLocal
from app.services.parser import ParserServicer
from app.config import settings

logger = logging.getLogger(__name__)

RABBITMQ_HOST = settings.RABBITMQ_HOST
RABBITMQ_PORT = settings.RABBITMQ_PORT
PARSE_QUEUE = settings.RABBITMQ_PARSE_QUEUE
ANALYZE_QUEUE = settings.RABBITMQ_ANALYZE_QUEUE
RABBITMQ_USER = settings.RABBITMQ_USER
RABBITMQ_PASSWORD = settings.RABBITMQ_PASSWORD


async def consume_parse_queue():
    try:
        connection = await aio_pika.connect_robust(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT,
            login=RABBITMQ_USER,
            password=RABBITMQ_PASSWORD,
        )
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=10)

        queue = await channel.declare_queue(PARSE_QUEUE, durable=True)
        logger.info(f"Connected to RabbitMQ, listening to queue: {PARSE_QUEUE}")

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    try:
                        parse_request = parser_pb2.ParseRequest()
                        parse_request.ParseFromString(message.body)
                        url = parse_request.url
                        correlation_id = parse_request.correlation_id
                        logger.info(
                            f"Parsing URL: {url} with correlation_id: {correlation_id}"
                        )

                        # Parsing processing
                        parser = ParserServicer()
                        parse_response = parser.Parse(parse_request, None)
                        parse_response.correlation_id = correlation_id

                        # Save result to database
                        async with AsyncSessionLocal() as session:
                            parsed = ParsedData(
                                correlation_id=correlation_id,
                                content=parse_response.content,
                                status="parsed",
                            )
                            session.add(parsed)
                            await session.commit()

                        # Publish to analyze_queue
                        await channel.default_exchange.publish(
                            aio_pika.Message(
                                body=parse_response.SerializeToString(),
                                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                            ),
                            routing_key=ANALYZE_QUEUE,
                        )
                        logger.info(
                            f"Published parsed content to {ANALYZE_QUEUE} with correlation_id: {correlation_id}"
                        )
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                        traceback.print_exc()
    except Exception as e:
        logger.critical(f"Failed to connect to RabbitMQ: {e}")
        raise
