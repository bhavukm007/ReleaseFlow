"""Production entrypoint with observable startup phases."""

import logging
import os
import subprocess
import sys
import time

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("releaseflow.startup")
process_started = time.perf_counter()
os.environ["RELEASEFLOW_PROCESS_STARTED"] = str(process_started)

migration_started = time.perf_counter()
subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True)
logger.info(
    "startup_phase phase=migrations duration_ms=%.1f",
    (time.perf_counter() - migration_started) * 1000,
)

logger.info(
    "startup_phase phase=uvicorn_exec elapsed_ms=%.1f",
    (time.perf_counter() - process_started) * 1000,
)
os.execvp(
    sys.executable,
    [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        "0.0.0.0",
        "--port",
        os.getenv("PORT", "8000"),
        "--no-server-header",
    ],
)
