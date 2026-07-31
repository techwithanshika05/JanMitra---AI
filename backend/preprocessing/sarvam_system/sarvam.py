import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from .errors import ExternalProcessorError
from .splitter import PdfChunk
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SarvamResult:
    chunk: PdfChunk
    job_id: str
    zip_path: Path
    status: str
    metrics: dict[str, Any]


class SarvamJob(Protocol):
    job_id: str
    def upload_file(self, path: str) -> Any: ...
    def start(self) -> Any: ...
    def wait_until_complete(self, poll_interval: int, timeout: int) -> Any: ...
    def download_output(self, path: str) -> Any: ...
    def get_page_metrics(self) -> dict[str, Any]: ...


class SarvamJobManager:
    """SDK adapter. Isolated because Sarvam response shapes may evolve."""

    def __init__(
        self,
        api_key: str,
        language: str = "en-IN",
        output_format: str = "html",
        poll_interval: int = 5,
        timeout: int = 600,
        retries: int = 3,
        client: Any | None = None,
    ):
        if client is None:
            if not api_key:
                raise ExternalProcessorError("SARVAM_API_KEY is not configured")
            try:
                from sarvamai import SarvamAI
                client = SarvamAI(api_subscription_key=api_key)
            except Exception as exc:
                raise ExternalProcessorError(f"Cannot initialize Sarvam SDK: {exc}") from exc
        self.client = client
        self.language = language
        self.output_format = output_format
        self.poll_interval = poll_interval
        self.timeout = timeout
        self.retries = retries

    def process(self, chunk: PdfChunk, output_dir: Path) -> SarvamResult:
        output_dir.mkdir(parents=True, exist_ok=True)
        last_error: Exception | None = None
        for attempt in range(1, self.retries + 1):
            try:
                job = self.client.document_intelligence.create_job(
                    language=self.language,
                    output_format=self.output_format,
                )
                job.upload_file(str(chunk.path))
                job.start()
                result = job.wait_until_complete(
                    poll_interval=self.poll_interval,
                    timeout=self.timeout,
                )
                state = getattr(result, "job_state", None) or getattr(result, "status", None)
                if state not in {"Completed", "PartiallyCompleted"}:
                    raise ExternalProcessorError(f"Sarvam job ended in state {state!r}")
                zip_path = output_dir / f"chunk-{chunk.chunk_number:04d}.zip"
                job.download_output(str(zip_path))
                try:
                    metrics = job.get_page_metrics() or {}
                except Exception:
                    metrics = {}
                return SarvamResult(
                    chunk=chunk,
                    job_id=str(getattr(job, "job_id", "unknown")),
                    zip_path=zip_path,
                    status=str(state),
                    metrics=metrics,
                )
            except Exception as exc:
                last_error = exc
                logger.warning("Sarvam attempt %s failed: %s", attempt, exc)
                if attempt < self.retries:
                    time.sleep(self.poll_interval * attempt)
        raise ExternalProcessorError(
            f"Sarvam failed for pages {chunk.start_page}-{chunk.end_page}: {last_error}"
        )
