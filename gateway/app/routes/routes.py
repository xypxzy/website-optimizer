from fastapi import APIRouter, Query, HTTPException
from google.protobuf.json_format import MessageToDict
from fastapi.responses import JSONResponse
from sqlalchemy.future import select
import aio_pika
import uuid
import json
import logging
import asyncio

from proto.parser_pb2 import ParseRequest
from proto.analyzer_pb2 import AnalyzeResponse
from app.cache.cache import redis
from app.models.models import AnalysisResult
from app.database.database import AsyncSessionLocal
from app.config import settings


router = APIRouter()

RABBITMQ_HOST = settings.RABBITMQ_HOST
RABBITMQ_PORT = settings.RABBITMQ_PORT
PARSE_QUEUE = settings.RABBITMQ_PARSE_QUEUE
RESULTS_QUEUE = settings.RABBITMQ_RESULTS_QUEUE
RABBITMQ_USER = settings.RABBITMQ_USER
RABBITMQ_PASSWORD = settings.RABBITMQ_PASSWORD

logger = logging.getLogger("gateway")


async def get_aio_pika_connection():
    return await aio_pika.connect_robust(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        login=RABBITMQ_USER,
        password=RABBITMQ_PASSWORD,
    )


@router.get("/healthcheck")
async def healthcheck():
    return JSONResponse(content={"status": "ok"})


@router.post("/analyze_url")
async def analyze_url(url: str = Query(..., description="The URL to analyze")):
    correlation_id = str(uuid.uuid4())

    # Save initial record in PostgreSQL
    async with AsyncSessionLocal() as session:
        analysis = AnalysisResult(correlation_id=correlation_id, status="processing")
        session.add(analysis)
        await session.commit()

    # Publish to parse_queue
    try:
        connection = await get_aio_pika_connection()
        channel = await connection.channel()
        await channel.declare_queue(PARSE_QUEUE, durable=True)

        parse_request = ParseRequest(url=url, correlation_id=correlation_id)

        message = aio_pika.Message(
            body=parse_request.SerializeToString(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )

        await channel.default_exchange.publish(
            message,
            routing_key=PARSE_QUEUE,
        )
        await connection.close()
        logger.info(
            f"Published ParseRequest to {PARSE_QUEUE} with correlation_id: {correlation_id}"
        )
    except Exception as e:
        logger.error(f"Failed to publish message: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to publish message: {e}")

    return {"message": "URL is being processed.", "correlation_id": correlation_id}


@router.get("/results/{correlation_id}")
async def get_results(correlation_id: str):
    # Try to get data from Redis
    cached_result = await redis.get(correlation_id)
    if cached_result:
        return json.loads(cached_result)

    # If not in Redis, get from PostgreSQL
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(AnalysisResult).where(
                AnalysisResult.correlation_id == correlation_id
            )
        )
        analysis = result.scalars().first()
        if not analysis:
            raise HTTPException(status_code=404, detail="Correlation ID not found.")

        response = {
            "status": analysis.status,
            "seo_data": analysis.seo_data,
            "performance_data": analysis.performance_data,
            "accessibility_data": analysis.accessibility_data,
            "security_data": analysis.security_data,
            "structure_data": analysis.structure_data,
            "recommendations": analysis.recommendations,
            "frequency_distribution": analysis.frequency_distribution,
            "entities": analysis.entities,
        }

        # Cache the result in Redis
        await redis.set(correlation_id, json.dumps(response), ex=3600)

        return response


async def process_message(message: aio_pika.IncomingMessage):
    async with message.process():
        try:
            analyze_response = AnalyzeResponse()
            analyze_response.ParseFromString(message.body)
            correlation_id = analyze_response.correlation_id

            # Update results in PostgreSQL
            await update_results(correlation_id, analyze_response)

            logger.info(f"Processed analysis for correlation_id: {correlation_id}")

        except Exception as e:
            logger.error(f"Error processing analysis results: {e}")
            # Nack message without retry to avoid looping
            await message.nack(requeue=False)


async def update_results(correlation_id, analyze_response):
    async with AsyncSessionLocal() as session:
        analysis_result = await session.execute(
            select(AnalysisResult).where(
                AnalysisResult.correlation_id == correlation_id
            )
        )
        analysis = analysis_result.scalars().first()
        if analysis:
            analysis.status = "completed"
            # Convert ScalarMapContainer to dict
            analysis.frequency_distribution = dict(
                analyze_response.frequency_distribution
            )
            analysis.entities = [
                MessageToDict(entity) for entity in analyze_response.entities
            ]
            await session.commit()

            # Update cache in Redis
            response = {
                "status": analysis.status,
                "seo_data": analysis.seo_data,
                "performance_data": analysis.performance_data,
                "accessibility_data": analysis.accessibility_data,
                "security_data": analysis.security_data,
                "structure_data": analysis.structure_data,
                "recommendations": analysis.recommendations,
                "frequency_distribution": analysis.frequency_distribution,
                "entities": analysis.entities,
            }
            await redis.set(correlation_id, json.dumps(response), ex=3600)
            logger.info(f"Updated results for correlation_id: {correlation_id}")
        else:
            logger.warning(
                f"Received results for unknown correlation_id: {correlation_id}"
            )


async def consume_results():
    connection = await get_aio_pika_connection()
    channel = await connection.channel()
    await channel.declare_queue(RESULTS_QUEUE, durable=True)
    queue = await channel.get_queue(RESULTS_QUEUE)

    await queue.consume(process_message, no_ack=False)
    logger.info("Started listening to results_queue.")
    await asyncio.Future()


@router.on_event("startup")
async def startup_event():
    asyncio.create_task(consume_results())
