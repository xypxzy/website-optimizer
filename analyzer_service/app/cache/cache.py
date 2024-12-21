import aioredis
from app.config import settings

REDIS_URL = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"

redis = aioredis.from_url(REDIS_URL, decode_responses=True)
