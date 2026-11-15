"""Stateless Adaption Responses transport with explicit failure classification."""

from datetime import datetime, timezone
import json
import os
import socket
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener
from ..preflight import NoRedirect, response_summary


class ProviderFailure(RuntimeError):
    def __init__(self, kind, retryable=False, http_status=None, raw=None):
        super().__init__(kind)
        self.kind, self.retryable, self.http_status, self.raw = kind, retryable, http_status, raw


class AdaptionProvider:
    name = "adaption"

    def __init__(self, config):
        self.config = config

    def generate(self, messages, model):
        key = os.environ.get(self.config["api_key_env"], "").strip()
        if not key:
            raise ProviderFailure("missing_credentials")
        payload = {"model": model["model_id"], "input": messages, **model["generation"],
                   "agentic_memory": False, "store": False, "stream": False, "tools": [], "tool_choice": "none"}
        request = Request(self.config["base_url"].rstrip("/") + self.config["responses_path"],
                          data=json.dumps(payload).encode(),
                          headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        start = time.monotonic()
        timestamp = datetime.now(timezone.utc).isoformat()
        try:
            with build_opener(NoRedirect()).open(request, timeout=self.config["timeout_seconds"]) as response:
                raw = json.load(response)
                request_id = response.headers.get("x-request-id") or response.headers.get("request-id")
        except HTTPError as exc:
            status = exc.code
            # Inspect only the error code for classification; never retain auth error bodies.
            try:
                error = json.loads(exc.read(65536)).get("error", {})
                error_code = error.get("code") if isinstance(error, dict) else None
            except (ValueError, TypeError):
                error_code = None
            if error_code in {"content_filter", "content_policy_violation", "safety_filter"}:
                raise ProviderFailure("provider_filter", http_status=status) from None
            if 500 <= status <= 599:
                raise ProviderFailure("5xx", True, status) from None
            raise ProviderFailure("rate_limit" if status == 429 else "provider_rejection", http_status=status) from None
        except (TimeoutError, socket.timeout):
            raise ProviderFailure("timeout", True) from None
        except URLError as exc:
            raise ProviderFailure("timeout" if isinstance(exc.reason, (TimeoutError, socket.timeout)) else "transport", True) from None
        except OSError:
            raise ProviderFailure("transport", True) from None
        except ValueError:
            raise ProviderFailure("invalid_provider_response") from None
        if not isinstance(raw, dict):
            raise ProviderFailure("invalid_provider_response")
        if raw.get("status") in {"failed", "cancelled", "queued", "in_progress"}:
            error = raw.get("error") or {}
            code = error.get("code") if isinstance(error, dict) else None
            kind = "provider_filter" if code in {"content_filter", "content_policy_violation", "safety_filter"} else "5xx" if code in {"server_error", "internal_error"} else "provider_error"
            raise ProviderFailure(kind, kind == "5xx", raw=raw)
        if raw.get("model") != model["model_id"]:
            raise ProviderFailure("model_mismatch", raw=raw)
        summary = response_summary(raw)
        return {"raw": raw, "text": summary["output_text"], "summary": summary,
                "timestamp": timestamp, "request_id": request_id,
                "latency_seconds": time.monotonic() - start}
