"""
TELOS API authentication helpers.

When TELOS_API_TOKEN or TELOS_INTERNAL_TOKEN is configured, protected
routes require one of those tokens via Bearer auth, X-Telos-Api-Token,
or access_token for SSE-style clients.
"""

from __future__ import annotations

from fastapi import HTTPException, Request, status

from services.orchestrator.config import get_settings


def configured_tokens() -> set[str]:
    settings = get_settings()
    return {
        token
        for token in (settings.telos_api_token.strip(), settings.telos_internal_token.strip())
        if token
    }


def extract_request_token(request: Request) -> str:
    bearer = request.headers.get("authorization", "")
    if bearer.lower().startswith("bearer "):
        return bearer[7:].strip()

    header_token = request.headers.get("x-telos-api-token", "").strip()
    if header_token:
        return header_token

    query_token = request.query_params.get("access_token", "").strip()
    if query_token:
        return query_token

    return ""


async def auth_dependency(request: Request) -> None:
    tokens = configured_tokens()
    if not tokens:
        return

    token = extract_request_token(request)
    if token in tokens:
        return

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized",
        headers={"WWW-Authenticate": "Bearer"},
    )
