"""Bound PDF requests and validate documents without saving an upload library."""

from __future__ import annotations

import base64
import binascii
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import TYPE_CHECKING

from starlette.responses import JSONResponse

if TYPE_CHECKING:
    from schemas import PDFDocument

MAX_PDF_BYTES = 5 * 1024 * 1024
MAX_PDF_PAGES = 40
MAX_BASE64_CHARS = 4 * ((MAX_PDF_BYTES + 2) // 3)
MAX_REQUEST_BYTES = 8 * 1024 * 1024


class PDFValidationError(Exception):
    def __init__(self, detail: str, status: int = 400):
        self.detail = detail
        self.status = status
        super().__init__(detail)


def validate_pdf(document: PDFDocument) -> int:
    """Check bytes and page count in a separate, time-bounded parser process."""
    try:
        raw = base64.b64decode(document.data, validate=True)
    except (ValueError, binascii.Error):
        raise PDFValidationError("The PDF upload is not valid. Choose the file again.") from None
    if len(raw) > MAX_PDF_BYTES:
        raise PDFValidationError("Choose a PDF no larger than 5 MB.", 413)
    if not raw.startswith(b"%PDF-"):
        raise PDFValidationError("This file is not a valid PDF. Export it as PDF and try again.")
    try:
        result = subprocess.run(
            [sys.executable, "-I", str(Path(__file__).with_name("pdf_worker.py"))],
            input=raw,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=8,
            check=False,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        metadata = json.loads(result.stdout) if result.returncode == 0 else {}
    except (subprocess.TimeoutExpired, OSError, ValueError):
        raise PDFValidationError("The PDF could not be checked safely. Try exporting a smaller copy.") from None
    messages = {
        "encrypted": "Password-protected PDFs are not supported. Choose an unlocked copy.",
        "too_many_pages": "Choose a PDF with no more than 40 pages.",
        "invalid_pdf": "The PDF could not be read. Try exporting it again.",
        "no_pages": "The PDF has no pages. Choose another file.",
    }
    code = metadata.get("error")
    if code in messages:
        raise PDFValidationError(messages[code], 413 if code == "too_many_pages" else 400)
    pages = metadata.get("pages")
    if not isinstance(pages, int) or not 1 <= pages <= MAX_PDF_PAGES:
        raise PDFValidationError("The PDF could not be read. Try exporting it again.")
    return pages


class RequestSizeLimit:
    """Enforce the real streamed body size, including absent/false length headers."""

    def __init__(self, app, maximum=MAX_REQUEST_BYTES):
        self.app = app
        self.maximum = maximum

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope.get("method") != "POST":
            return await self.app(scope, receive, send)
        chunks = []
        length = 0
        while True:
            part = await receive()
            if part["type"] == "http.disconnect":
                return
            chunk = part.get("body", b"")
            length += len(chunk)
            if length > self.maximum:
                response = JSONResponse(
                    {"detail": "This upload is too large. Choose one PDF or image up to 5 MB.", "code": "upload_too_large"},
                    status_code=413,
                )
                return await response(scope, receive, send)
            chunks.append(chunk)
            if not part.get("more_body", False):
                break
        body = b"".join(chunks)
        delivered = False

        async def replay():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": body, "more_body": False}
            return await receive()

        return await self.app(scope, replay, send)
