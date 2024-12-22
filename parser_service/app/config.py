from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database settings
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int = 5432

    # RabbitMQ settings
    RABBITMQ_HOST: str = "rabbitmq"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_PARSE_QUEUE: str = "parse_queue"
    RABBITMQ_ANALYZE_QUEUE: str = "analyze_queue"
    RABBITMQ_RESULTS_QUEUE: str = "results_queue"
    RABBITMQ_USER: str = "user"
    RABBITMQ_PASSWORD: str = "password"

    # Redis settings
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379

    # gRPC settings
    GRPC_PORT: int = 50051

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Ensure the settings are loaded from the .env file
settings = Settings()
