import grpc
from concurrent import futures
from proto import analyzer_pb2_grpc
from app.services.text_analyzer import TextAnalyzerServicer
import logging

logger = logging.getLogger(__name__)


async def serve_grpc():
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    analyzer_pb2_grpc.add_AnalyzerServiceServicer_to_server(
        TextAnalyzerServicer(), server
    )
    server.add_insecure_port("[::]:50052")
    await server.start()
    logger.info("gRPC server started on port 50052.")
    await server.wait_for_termination()
