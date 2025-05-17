import os
from multiprocessing import cpu_count

# ===== Server Socket =====
# The socket(s) to bind the server to, specified as HOST:PORT.
bind = os.getenv("GUNICORN_BIND", "0.0.0.0:8000")
# The maximum number of pending connections before refusing new ones.
backlog = int(os.getenv("GUNICORN_BACKLOG", "2048"))

# ===== Worker Processes =====
# The number of worker processes, typically set to 2xCPU cores + 1.
workers = int(os.getenv("GUNICORN_WORKERS", cpu_count() * 2 + 1))
# The type of workers to handle requests (e.g., sync, gthread, UvicornWorker).
worker_class = os.getenv("GUNICORN_WORKER_CLASS", "uvicorn.workers.UvicornWorker")
# The number of threads per worker to handle concurrent requests.
threads = int(os.getenv("GUNICORN_THREADS", "1"))
# The maximum number of requests a worker will process before restarting.
max_requests = int(os.getenv("GUNICORN_MAX_REQUESTS", "1000"))
# The random jitter to add to max_requests for staggered restarts.
max_requests_jitter = int(os.getenv("GUNICORN_MAX_REQUESTS_JITTER", "50"))
# The number of seconds a worker can take to respond before being killed.
timeout = int(os.getenv("GUNICORN_TIMEOUT", "30"))
# The time given to workers to finish gracefully after a restart.
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", "30"))
# The seconds to wait for the next request on a keep-alive connection.
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", "5"))

# ===== Server Mechanics =====
# Loads the application code before forking workers to save memory.
preload_app = True

# ===== Logging =====
# The file to write access logs to; '-' means stdout.
accesslog = "-"
# The file to write error logs to; '-' means stderr.
errorlog = "-"
# The format string for access log entries.
access_log_format = (
    '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s '
    '[Time: %(T)ssec, %(M)sms] "%(f)s" "%(a)s"'
)
# The granularity of error log outputs (debug through critical).
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")
# Redirects worker stdout/stderr to the error log if True.
capture_output = True
# The Python class used for logging events in Gunicorn.
logger_class = "gunicorn.glogging.Logger"
