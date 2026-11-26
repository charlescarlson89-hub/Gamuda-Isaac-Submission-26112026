"""Isolated metadata check. Read bytes from stdin; emit only safe JSON metadata."""

from io import BytesIO
import json
import logging
import sys

from pypdf import PdfReader


def main():
    logging.disable(logging.CRITICAL)
    # Same file/page limits as pdf_support; no document text or errors are printed.
    raw = sys.stdin.buffer.read(5 * 1024 * 1024 + 1)
    result = {"error": "invalid_pdf"}
    try:
        if len(raw) <= 5 * 1024 * 1024:
            reader = PdfReader(BytesIO(raw))
            if reader.is_encrypted:
                result = {"error": "encrypted"}
            else:
                pages = len(reader.pages)
                if pages > 40:
                    result = {"error": "too_many_pages"}
                elif pages == 0:
                    result = {"error": "no_pages"}
                else:
                    result = {"pages": pages}
    except Exception:
        pass
    sys.stdout.write(json.dumps(result))


if __name__ == "__main__":
    main()
