"""
Structured JSON logging for production observability.
Every log line is a single JSON object — parseable by Fly.io log drains,
Datadog, Logtail, or any log aggregation system.
"""
import json
import logging
import traceback
from datetime import datetime, timezone


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        data: dict = {
            "ts":      datetime.now(timezone.utc).isoformat(),
            "level":   record.levelname,
            "logger":  record.name,
            "msg":     record.getMessage(),
        }
        # Include structured extras attached via logging.getLogger().info("...", extra={...})
        for key, val in record.__dict__.items():
            if key not in logging.LogRecord.__dict__ and not key.startswith("_"):
                try:
                    json.dumps(val)  # only include JSON-serializable extras
                    data[key] = val
                except (TypeError, ValueError):
                    pass
        if record.exc_info:
            data["exception"] = "".join(traceback.format_exception(*record.exc_info))
        return json.dumps(data, ensure_ascii=False)


def setup_logging() -> None:
    """Configure root logger to emit JSON. Call once at application startup."""
    handler = logging.StreamHandler()
    handler.setFormatter(_JsonFormatter())

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers = [handler]

    # Silence noisy third-party loggers that add no signal in production
    for name in ("uvicorn.access", "httpx", "httpcore", "prophet", "cmdstanpy"):
        logging.getLogger(name).setLevel(logging.WARNING)
