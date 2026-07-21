from redis import Redis
from rq import Queue

from app.core.config import settings

redis_conn = Redis.from_url(settings.redis_url)
document_queue = Queue("document_processing", connection=redis_conn)