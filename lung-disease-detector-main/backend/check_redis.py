
import redis
import sys

try:
    r = redis.Redis(host='localhost', port=6379, db=0, socket_timeout=5)
    r.ping()
    print("Redis is reachable")
except Exception as e:
    print(f"Redis connection failed: {e}")
    sys.exit(1)
