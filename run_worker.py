"""
Starts an RQ worker listening to all background job queues used by this
project. Run with: python run_worker.py

Both document_processing (parsing/chunking) and embedding_processing
(B1) are handled by a single worker process -- see B1 decisions log for
why two separate worker processes weren't used at this project's scale.
"""

from rq import Worker

from app.services.queue import redis_conn, document_queue, embedding_queue

if __name__ == "__main__":
    worker = Worker([document_queue, embedding_queue], connection=redis_conn)
    worker.work()