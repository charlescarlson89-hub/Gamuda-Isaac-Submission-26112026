"""Decode one still image and emit only clean pixels; no upload files are saved."""

from io import BytesIO
import json
import sys
import warnings

from PIL import Image, ImageOps

MAX_BYTES = 5 * 1024 * 1024
MAX_PIXELS = 16_000_000


def prepare(raw, expected):
    Image.MAX_IMAGE_PIXELS = MAX_PIXELS
    warnings.simplefilter("error", Image.DecompressionBombWarning)
    with Image.open(BytesIO(raw)) as probe:
        if probe.format != expected:
            raise ValueError("format")
        if probe.width * probe.height > MAX_PIXELS:
            raise ValueError("pixels")
        if getattr(probe, "n_frames", 1) != 1:
            raise ValueError("animated")
        probe.verify()
    with Image.open(BytesIO(raw)) as source:
        source.load()
        oriented = ImageOps.exif_transpose(source)
        transparent = "A" in oriented.getbands() or "transparency" in oriented.info
        mode = "RGBA" if expected == "PNG" and transparent else "RGB"
        # Copy pixels into a fresh image: exclude EXIF, text, comments and profiles.
        converted = oriented.convert(mode)
        clean = Image.new(mode, converted.size)
        clean.paste(converted)
        output = BytesIO()
        clean.save(output, format=expected, **({"quality": 90} if expected == "JPEG" else {}))
        encoded = output.getvalue()
        if len(encoded) > MAX_BYTES:
            raise ValueError("size")
        return {"width": clean.width, "height": clean.height}, encoded


if __name__ == "__main__":
    try:
        raw = sys.stdin.buffer.read(MAX_BYTES + 1)
        if not raw or len(raw) > MAX_BYTES:
            raise ValueError("size")
        expected = {"image/jpeg": "JPEG", "image/png": "PNG"}[sys.argv[1]]
        metadata, pixels = prepare(raw, expected)
        sys.stdout.buffer.write(json.dumps(metadata).encode("ascii") + b"\n" + pixels)
    except Exception:
        # Never expose parser exception messages, paths, or uploaded content.
        sys.exit(1)
