import grpc
from concurrent import futures
from proto import parser_pb2_grpc
from app.services.parser import ParserServicer
import logging

logger = logging.getLogger(__name__)


async def serve_grpc():
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    parser_pb2_grpc.add_ParserServiceServicer_to_server(ParserServicer(), server)
    server.add_insecure_port("[::]:50051")
    await server.start()
    logger.info("gRPC server started on port 50051.")
    await server.wait_for_termination()
