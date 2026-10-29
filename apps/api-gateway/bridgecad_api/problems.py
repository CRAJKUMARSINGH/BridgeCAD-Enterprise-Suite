"""
RFC 7807 `application/problem+json` error handling for the FastAPI gateway.

Wires GUIDE.md §8 ("Still open: ... RFC 7807 application/problem+json error
bodies") into one reusable module. Mount once in `apps/api-gateway` and every
error path — validation, domain, unexpected — returns a stable problem shape:

    {
      "type":   "about:blank" | URI identifying the problem type,
      "title":  short human summary,
      "status": HTTP status code,
      "detail": specific explanation for this occurrence,
      "instance": request path
    }

Never leak tracebacks or internal paths to clients; log the full stack
server-side with a correlation id instead.
"""

from __future__ import annotations

import logging
import uuid

from fastapi import FastAPI, Request, UploadFile, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = logging.getLogger("bridgecad.api.errors")


# ---------------------------------------------------------------------------
# Stable problem-type registry. Extend here, never invent URIs ad hoc —
# clients branch on `type`, so it is part of your public API contract.
# ---------------------------------------------------------------------------
PROBLEM_BASE = "https://bridgecad.example/problems"

UPLOAD_TOO_LARGE = f"{PROBLEM_BASE}/upload-too-large"
UNSUPPORTED_MEDIA_TYPE = f"{PROBLEM_BASE}/unsupported-media-type"
WORKBOOK_INVALID = f"{PROBLEM_BASE}/workbook-invalid"
WORKBOOK_PARSE_ERROR = f"{PROBLEM_BASE}/workbook-parse-error"
NOT_FOUND = f"{PROBLEM_BASE}/not-found"
INTERNAL_ERROR = f"{PROBLEM_BASE}/internal-error"

ALLOWED_UPLOAD_SUFFIXES = {".xlsx"}


class Problem(BaseModel):
    """RFC 7807 problem detail. `type` and `title` are stable; `detail` may vary."""

    type: str = "about:blank"
    title: str
    status: int
    detail: str = ""
    instance: str = ""


def problem_response(problem: Problem) -> JSONResponse:
    return JSONResponse(
        status_code=problem.status,
        content=problem.model_dump(),
        media_type="application/problem+json",
    )


# ---------------------------------------------------------------------------
# Domain errors — raise these anywhere under apps/api-gateway routers.
# ---------------------------------------------------------------------------
class ApiError(Exception):
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    type_uri: str = INTERNAL_ERROR
    title: str = "Internal error"

    def __init__(self, detail: str = "") -> None:
        super().__init__(detail)
        self.detail = detail


class UploadTooLargeError(ApiError):
    status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    type_uri = UPLOAD_TOO_LARGE
    title = "Upload exceeds size limit"


class UnsupportedMediaTypeError(ApiError):
    status_code = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    type_uri = UNSUPPORTED_MEDIA_TYPE
    title = "Unsupported file type"


class WorkbookInvalidError(ApiError):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    type_uri = WORKBOOK_INVALID
    title = "Workbook failed validation"


class WorkbookParseError(ApiError):
    status_code = status.HTTP_400_BAD_REQUEST
    type_uri = WORKBOOK_PARSE_ERROR
    title = "Workbook could not be parsed"


# ---------------------------------------------------------------------------
# Upload hardening helpers (GUIDE.md §8 open items).
# ---------------------------------------------------------------------------
MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # keep in sync with nginx client_max_body_size


async def enforce_upload_limits(file: UploadFile, max_bytes: int = MAX_UPLOAD_BYTES) -> bytes:
    """Read an upload once, enforcing size cap and `.xlsx`-only allowlist.

    Raises:
        UnsupportedMediaTypeError: suffix is not .xlsx (covers .xls / .xlsm)
        UploadTooLargeError: body exceeds max_bytes
    """
    suffix = (
        "." + (file.filename or "").rsplit(".", 1)[-1].lower()
        if "." in (file.filename or "")
        else ""
    )
    if suffix not in ALLOWED_UPLOAD_SUFFIXES:
        raise UnsupportedMediaTypeError(
            detail=f"Only .xlsx workbooks are accepted; got {suffix or 'no extension'}."
        )
    body = await file.read()
    if len(body) > max_bytes:
        raise UploadTooLargeError(detail=f"Upload is {len(body)} bytes; limit is {max_bytes}.")
    return body


# ---------------------------------------------------------------------------
# Handler registration — call `install_problem_handlers(app)` at startup.
# ---------------------------------------------------------------------------
def install_problem_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def handle_api_error(request: Request, exc: ApiError) -> JSONResponse:
        return problem_response(
            Problem(
                type=exc.type_uri,
                title=exc.title,
                status=exc.status_code,
                detail=exc.detail,
                instance=request.url.path,
            )
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        # Pydantic/FastAPI validation failures map cleanly onto RFC 7807:
        # the request was well-formed JSON but semantically unprocessable.
        detail = "; ".join(
            f"{'.'.join(str(p) for p in e.get('loc', [])[1:]) or 'body'}: {e.get('msg', 'invalid')}"
            for e in exc.errors()[:10]
        )
        return problem_response(
            Problem(
                type=f"{PROBLEM_BASE}/validation-error",
                title="Request validation failed",
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=detail,
                instance=request.url.path,
            )
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, _exc: Exception) -> JSONResponse:
        corr = uuid.uuid4().hex[:12]
        logger.exception("unhandled error correlation=%s path=%s", corr, request.url.path)
        return problem_response(
            Problem(
                type=INTERNAL_ERROR,
                title="Internal error",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error (correlation id {corr}).",
                instance=request.url.path,
            )
        )
