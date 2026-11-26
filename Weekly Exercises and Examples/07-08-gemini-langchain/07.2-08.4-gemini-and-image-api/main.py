"""Local FastAPI server: validate requests, apply limits, then call Gemini."""

import asyncio
import logging
import time
from collections import deque

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware

from ai_service import generate_reply
from config import Settings, get_settings
from schemas import ChatRequest, ChatResponse
from provider_errors import safe_provider_error
from pdf_support import PDFValidationError, RequestSizeLimit, validate_pdf
from image_support import ImageValidationError, validate_image

logger = logging.getLogger("uvicorn.error")

ALLOWED_ORIGINS = {
    "http://localhost:5174", "http://127.0.0.1:5174",
    "http://localhost:4174", "http://127.0.0.1:4174",
}


class LocalLimits:
    """Small, process-wide learning limits; these reset when the server restarts."""

    def __init__(self):
        self.recent = deque()
        self.attempts = 0
        self.busy = False

    def reserve(self):
        now = time.monotonic()
        while self.recent and now - self.recent[0] >= 60:
            self.recent.popleft()
        if self.busy:
            raise HTTPException(429, "Kazu is answering another message. Please wait.")
        if len(self.recent) >= 6:
            raise HTTPException(429, "Please wait a minute before sending more messages.")
        if self.attempts >= 50:
            raise HTTPException(429, "This server session has reached its 50-request learning limit.")
        self.recent.append(now)
        self.attempts += 1
        self.busy = True


def create_app(settings: Settings | None = None, responder=generate_reply) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title="Kazu AI Lab", version="0.1.0")
    limits = LocalLimits()
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "testserver"])
    app.add_middleware(
        CORSMiddleware,
        allow_origins=sorted(ALLOWED_ORIGINS),
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-Kazu-Client"],
    )
    app.add_middleware(RequestSizeLimit)

    @app.middleware("http")
    async def local_browser_guard(request: Request, call_next):
        if request.method == "POST":
            origin = request.headers.get("origin")
            if origin and origin not in ALLOWED_ORIGINS:
                return JSONResponse({"detail": "This browser origin is not allowed."}, status_code=403)
            # Cross-origin pages cannot add this header without an approved preflight.
            # It is a browser request guard, not a login token or public API auth.
            if request.headers.get("x-kazu-client") != "web":
                return JSONResponse({"detail": "Use the Kazu app to send messages."}, status_code=403)
            if request.headers.get("content-type", "").split(";")[0] != "application/json":
                return JSONResponse({"detail": "Send JSON data."}, status_code=415)
        return await call_next(request)

    @app.exception_handler(RequestValidationError)
    async def invalid_input(request: Request, error: RequestValidationError):
        # Do not reflect user messages or raw error objects into responses/logs.
        return JSONResponse(
            {"detail": "Use 1–2,000 characters per message and up to 6 conversation pairs (16,000 characters total). Attach one PDF (40 pages) or one JPG/PNG, up to 5 MB. Images must be still and at most 16 megapixels."},
            status_code=422,
        )

    @app.get("/api/health")
    async def health():
        return {"status": "ok", "configured": settings.configured, "model": settings.model}

    @app.post("/api/chat", response_model=ChatResponse, response_model_exclude_none=True)
    async def chat(payload: ChatRequest):
        if not settings.configured:
            return JSONResponse({"code": "key_not_configured", "detail": "Add GEMINI_API_KEY to Kazu's private .env file (see README), then restart the backend."}, status_code=503)
        limits.reserve()

        async def answer():
            pages = await asyncio.to_thread(validate_pdf, payload.document) if payload.document else None
            width = height = None
            checked = payload
            if payload.image:
                image, width, height = await asyncio.to_thread(validate_image, payload.image)
                checked = payload.model_copy(update={"image": image})
            reply = await responder(checked, settings)
            return ChatResponse(reply=reply, document_pages=pages, image_width=width, image_height=height)

        try:
            return await asyncio.wait_for(answer(), timeout=45)
        except PDFValidationError as error:
            return JSONResponse({"detail": error.detail, "code": "invalid_pdf"}, status_code=error.status)
        except ImageValidationError as error:
            return JSONResponse({"detail": error.detail, "code": "invalid_image"}, status_code=error.status)
        except Exception as error:
            status, category, detail = safe_provider_error(error)
            # Fixed categories only: never log exceptions, raw messages, or credentials.
            logger.warning("Gemini request failed: %s", category)
            return JSONResponse({"detail": detail, "code": category}, status_code=status)
        finally:
            limits.busy = False

    return app


app = create_app()
