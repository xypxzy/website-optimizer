import logging
import grpc
from concurrent import futures
from app.services.parser import ParserServicer
from proto import parser_pb2_grpc
from app.models.parsed_page import Base
from app.db.db import engine


def init_db():
    """Creates tables when the container starts."""
    Base.metadata.create_all(bind=engine)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    parser_pb2_grpc.add_ParserServiceServicer_to_server(ParserServicer(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_db()
    serve()
