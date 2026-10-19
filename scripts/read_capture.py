"""Private, durable receipts for explicitly read-only call windows.

This module does not perform authentication or HTTP itself. Callers use their
vetted read path and pass its response to ``capture_readonly_call``. Times are
call-window bounds, not transport-level wire timestamps.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlsplit, urlunsplit

SAFE_RESPONSE_HEADERS = {
    "date", "age", "cache-control", "last-modified", "content-type",
    "content-length", "etag", "retry-after",
}
SAFE_REQUEST_FIELDS = {
    "read_only", "method", "url", "endpoint", "operation", "rpc_method",
    "scope", "call_window_label", "chain_id", "block_number",
    "query_sha256", "request_body_sha256",
}
BODY_REPRESENTATIONS = {
    "supplied_bytes", "http_body", "sdk_result_serialization", "jsonrpc_provider_result",
}
_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,79}$")
_SENSITIVE = re.compile(r"auth|cookie|token|secret|password|credential|private.?key|owner.?uuid", re.I)


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _valid_utc(value: str) -> bool:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, TypeError, ValueError):
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() == timezone.utc.utcoffset(parsed)


def _safe_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(metadata, dict) or metadata.get("read_only") is not True:
        raise ValueError("request metadata must explicitly declare read_only=True")
    unknown = set(metadata) - SAFE_REQUEST_FIELDS
    if unknown or any(_SENSITIVE.search(str(key)) for key in metadata):
        raise ValueError(f"unsafe or unsupported request metadata field(s): {sorted(unknown)}")
    cleaned: dict[str, Any] = {}
    for key, value in metadata.items():
        if key == "url":
            if not isinstance(value, str):
                raise ValueError("url metadata must be a string")
            parts = urlsplit(value)
            # Query strings/fragments and userinfo can contain credentials.
            host = parts.hostname or ""
            if parts.port:
                host += f":{parts.port}"
            cleaned[key] = urlunsplit((parts.scheme, host, parts.path, "", ""))
        elif isinstance(value, (str, int, float, bool)) or value is None:
            if isinstance(value, str) and len(value) > 300:
                raise ValueError(f"metadata value too long: {key}")
            cleaned[key] = value
        else:
            raise ValueError(f"metadata value must be scalar: {key}")
    return cleaned


def _write_new(path: Path, data: bytes) -> None:
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temp_path = Path(temp_name)
    dir_fd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        # A hard-link publishes the fully written file atomically and fails if
        # another capture already owns the destination name.
        os.link(temp_path, path)
        temp_path.unlink()
        os.fsync(dir_fd)
    except Exception:
        try:
            temp_path.unlink()
        except FileNotFoundError:
            pass
        raise
    finally:
        os.close(dir_fd)


class Capture:
    """Write private intent and response receipts before a caller parses data."""

    def __init__(self, directory: str | Path):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, mode=0o700, exist_ok=False)
        os.chmod(self.directory, 0o700)

    def write_intent(self, name: str, request_safe_metadata: dict[str, Any],
                     started_utc: str | None = None) -> dict[str, Any]:
        if not isinstance(name, str) or not _NAME.fullmatch(name):
            raise ValueError("invalid capture name")
        metadata = _safe_metadata(request_safe_metadata)
        started = started_utc or _utcnow()
        if not _valid_utc(started):
            raise ValueError("started_utc must be an aware UTC timestamp")
        row = {
            "schema": "read_capture.intent.v1", "name": name,
            "timing_basis": "call_window", "started_utc": started,
            "request": metadata,
        }
        path = self.directory / f"{name}.intent.json"
        _write_new(path, (json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode())
        return row

    def write_response(self, name: str, request_safe_metadata: dict[str, Any],
                       response_status: int | None, raw_bytes: bytes,
                       started_utc: str, received_utc: str,
                       response_headers: dict[str, str] | None = None,
                       error_type: str | None = None,
                       body_representation: str = "supplied_bytes") -> dict[str, Any]:
        """Durably save body then manifest; never stores unsafe headers or exception text."""
        if not isinstance(name, str) or not _NAME.fullmatch(name):
            raise ValueError("invalid capture name")
        metadata = _safe_metadata(request_safe_metadata)
        intent_path = self.directory / f"{name}.intent.json"
        if not intent_path.is_file():
            raise FileNotFoundError("call-window intent must be durable before response capture")
        intent = json.loads(intent_path.read_text(encoding="utf8"))
        if intent.get("request") != metadata or intent.get("started_utc") != started_utc:
            raise ValueError("response metadata/timing must match the durable intent")
        if not _valid_utc(started_utc) or not _valid_utc(received_utc):
            raise ValueError("response times must be aware UTC timestamps")
        if datetime.fromisoformat(received_utc.replace("Z", "+00:00")) < datetime.fromisoformat(started_utc.replace("Z", "+00:00")):
            raise ValueError("received_utc cannot precede started_utc")
        if not isinstance(raw_bytes, bytes):
            raise TypeError("raw_bytes must be bytes")
        if response_status is not None and (
            not isinstance(response_status, int) or isinstance(response_status, bool)
            or not 100 <= response_status <= 599
        ):
            raise ValueError("response_status must be an HTTP status code or None")
        if error_type is not None and not re.fullmatch(r"[A-Za-z][A-Za-z0-9_.]{0,79}", error_type):
            raise ValueError("error_type must be a class name, not exception text")
        if body_representation not in BODY_REPRESENTATIONS:
            raise ValueError("unsupported body_representation")
        safe_headers = {
            k.lower(): v for k, v in (response_headers or {}).items()
            if k.lower() in SAFE_RESPONSE_HEADERS and isinstance(v, str) and len(v) <= 500
        }
        compressed = gzip.compress(raw_bytes, mtime=0)
        body_path = self.directory / f"{name}.body.json.gz"
        _write_new(body_path, compressed)
        receipt = {
            "schema": "read_capture.response.v1", "name": name,
            "timing_basis": "call_window", "started_utc": started_utc,
            "received_utc": received_utc, "response_status": response_status,
            "error_type": error_type, "headers": safe_headers,
            "body_representation": body_representation,
            "hash_scope": "supplied_bytes_only_not_wire_authentication",
            "request": metadata, "raw_bytes": len(raw_bytes),
            "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
            "gzip_sha256": hashlib.sha256(compressed).hexdigest(),
            "body_path": body_path.name,
        }
        receipt_path = self.directory / f"{name}.receipt.json"
        _write_new(receipt_path, (json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n").encode())
        return receipt

    def capture_readonly_call(self, name: str, request_safe_metadata: dict[str, Any],
                              invoke: Callable[[], Any],
                              unpack: Callable[[Any], tuple[int | None, bytes, dict[str, str]]],
                              parse: Callable[[int | None, bytes, dict[str, Any]], Any],
                              body_representation: str = "supplied_bytes") -> Any:
        """Wrap an existing read-only call; persist response before invoking parser."""
        started = _utcnow()
        self.write_intent(name, request_safe_metadata, started)
        try:
            response = invoke()
        except Exception as exc:
            received = _utcnow()
            self.write_response(name, request_safe_metadata, None, b"", started, received,
                                error_type=type(exc).__name__, body_representation=body_representation)
            raise
        received = _utcnow()
        try:
            status, raw, headers = unpack(response)
        except Exception as exc:
            # Preserve the call window even if a response adapter cannot extract
            # a raw body; do not serialize exception text or response objects.
            self.write_response(name, request_safe_metadata, None, b"", started, received,
                                error_type=type(exc).__name__, body_representation=body_representation)
            raise
        receipt = self.write_response(name, request_safe_metadata, status, raw, started,
                                      received, headers, body_representation=body_representation)
        # Parser exceptions cannot remove the durable intent, body, or receipt.
        return parse(status, raw, receipt)
