from redis import Redis
from rq import Queue

redis_conn = Redis(host="valkey", port=6379, db=0)

q = Queue(connection=redis_conn)
