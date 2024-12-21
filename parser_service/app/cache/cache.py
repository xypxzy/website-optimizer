import aioredis
import os

REDIS_URL = f"redis://{os.getenv('REDIS_HOST')}:{os.getenv('REDIS_PORT')}"

redis = aioredis.from_url(REDIS_URL, decode_responses=True)
