"""Custom retry strategy for GeoAgent supporting Groq HTTP 429 and rate limits."""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Any

from strands.event_loop._retry import ModelRetryStrategy
from strands.hooks.events import AfterModelCallEvent
from strands.types._events import EventLoopThrottleEvent
from strands.types.exceptions import ModelThrottledException

logger = logging.getLogger(__name__)


def parse_retry_delay(err: Exception, default: float = 2.0) -> float:
    """Parse retry-after delay from headers or exception message."""
    # 1. HTTP response headers
    response = getattr(err, "response", None)
    if response is not None:
        headers = getattr(response, "headers", None)
        if headers and "retry-after" in headers:
            try:
                return max(0.5, float(headers["retry-after"]))
            except (ValueError, TypeError):
                pass

    # 2. Error message string: e.g. "try again in 2.5s"
    msg = str(err)
    match_s = re.search(r"try again in ([\d\.]+)\s*s", msg, re.IGNORECASE)
    if match_s:
        try:
            return max(0.5, float(match_s.group(1)))
        except (ValueError, TypeError):
            pass

    # 3. Minute/second format: e.g. "try again in 1m20s"
    match_ms = re.search(r"try again in (\d+)m([\d\.]+)s", msg, re.IGNORECASE)
    if match_ms:
        try:
            return max(0.5, float(match_ms.group(1)) * 60 + float(match_ms.group(2)))
        except (ValueError, TypeError):
            pass

    return default


class GeoAgentRetryStrategy(ModelRetryStrategy):
    """Safe retry strategy for Groq and LiteLLM rate limits."""

    def __init__(
        self,
        *,
        max_attempts: int = 5,
        initial_delay: int = 2,
        max_delay: int = 60,
    ) -> None:
        super().__init__(
            max_attempts=max_attempts,
            initial_delay=initial_delay,
            max_delay=max_delay,
        )

    def is_retryable(self, exception: Exception) -> bool:
        """Return True if exception represents a rate limit / 429 error."""
        if isinstance(exception, ModelThrottledException):
            return True

        # Check litellm RateLimitError without hard dependency if litellm not imported
        type_name = type(exception).__name__
        if "RateLimit" in type_name or "Throttl" in type_name:
            return True

        if getattr(exception, "status_code", None) == 429:
            return True

        msg = str(exception).lower()
        if (
            "429" in msg
            or "rate_limit_exceeded" in msg
            or "rate limit" in msg
            or "too many requests" in msg
        ):
            return True

        return super().is_retryable(exception)

    async def _handle_after_model_call(self, event: AfterModelCallEvent) -> None:
        """Handle model call completion and retry with exact retry-after when available."""
        if event.retry:
            return

        if event.stop_response is not None:
            self._reset_retry_state()
            return

        if event.exception is None or not self.is_retryable(event.exception):
            return

        self._current_attempt += 1
        if self._current_attempt >= self._max_attempts:
            logger.warning(
                "Max retry attempts (%d) reached for model call; error: %s",
                self._max_attempts,
                event.exception,
            )
            return

        # Calculate delay respecting server retry-after
        calc_delay = self._calculate_delay(self._current_attempt - 1)
        delay = parse_retry_delay(event.exception, default=calc_delay)
        delay = min(delay, float(self._max_delay))

        self._backwards_compatible_event_to_yield = EventLoopThrottleEvent(delay=int(delay))
        logger.info(
            "Rate limit encountered (%s). Retrying model call (attempt %d/%d) after %.1fs...",
            type(event.exception).__name__,
            self._current_attempt,
            self._max_attempts,
            delay,
        )

        await asyncio.sleep(delay)
        event.retry = True

