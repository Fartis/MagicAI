from __future__ import annotations

from typing import Any

import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from magicai.versioning import JUDGE_RESULT_SCHEMA_VERSION


def build_error_payload(
    *,
    code: str,
    message: str,
    retryable: bool,
    details: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": JUDGE_RESULT_SCHEMA_VERSION,
        "error": {
            "code": code,
            "message": message,
            "retryable": retryable,
            "details": list(details or []),
        },
    }


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def request_validation_handler(
        request: Request,
        error: RequestValidationError,
    ) -> JSONResponse:
        details = [
            {
                "location": [str(item) for item in issue.get("loc", ())],
                "message": str(issue.get("msg", "Invalid value.")),
                "type": str(issue.get("type", "validation_error")),
            }
            for issue in error.errors()
        ]
        return JSONResponse(
            status_code=422,
            content=build_error_payload(
                code="invalid_request",
                message="The request payload is not valid.",
                retryable=False,
                details=details,
            ),
        )

    @app.exception_handler(requests.RequestException)
    async def upstream_service_handler(
        request: Request,
        error: requests.RequestException,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=503,
            content=build_error_payload(
                code="llm_unavailable",
                message=(
                    "The local language model service is unavailable. "
                    "Deterministic Judge routes may still be usable."
                ),
                retryable=True,
            ),
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request,
        error: HTTPException,
    ) -> JSONResponse:
        detail = error.detail
        if isinstance(detail, dict):
            code = str(detail.get("code", "http_error"))
            message = str(detail.get("message", "The request could not be completed."))
            retryable = bool(detail.get("retryable", False))
            details = detail.get("details", [])
        else:
            code = "http_error"
            message = str(detail)
            retryable = error.status_code >= 500
            details = []

        return JSONResponse(
            status_code=error.status_code,
            headers=error.headers,
            content=build_error_payload(
                code=code,
                message=message,
                retryable=retryable,
                details=details if isinstance(details, list) else [],
            ),
        )

    @app.exception_handler(Exception)
    async def unexpected_exception_handler(
        request: Request,
        error: Exception,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content=build_error_payload(
                code="internal_error",
                message="MagicAI could not complete the request.",
                retryable=True,
            ),
        )
