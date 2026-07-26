"""Captured figures -> inlined WebP plates.

WebP rather than PNG is not a preference: measured on representative figures, PNG
is 4-17x larger (a colormap plot inlines at 502 KB as PNG, 29 KB as WebP).

Deduplication is by source content hash, so the same figure referenced from two
slides is embedded once.
"""

from __future__ import annotations

import base64
import hashlib
import io
from pathlib import Path

TARGET_WIDTH = 1000
QUALITY = 82
MIN_WIDTH = 640


class AssetStore:
    """Transcodes figures to inlined WebP, deduplicating identical source content."""

    def __init__(
        self,
        target_width: int = TARGET_WIDTH,
        quality: int = QUALITY,
        min_width: int = MIN_WIDTH,
    ) -> None:
        self._target_width = target_width
        self._quality = quality
        self._min_width = min_width
        self._by_digest: dict[str, str] = {}
        self._warnings: list[str] = []

    @property
    def warnings(self) -> tuple[str, ...]:
        return tuple(self._warnings)

    @property
    def payload_bytes(self) -> int:
        """Total size of the distinct data URIs this store will contribute."""
        return sum(len(uri) for uri in self._by_digest.values())

    def src(self, path: str | Path) -> str:
        """Return a data: URI for `path`, transcoding and deduplicating as needed."""
        p = Path(path)
        if not p.is_file():
            raise FileNotFoundError(f"figure not found: {p}")

        raw = p.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest in self._by_digest:
            return self._by_digest[digest]

        uri = f"data:image/webp;base64,{base64.b64encode(self._webp(raw, p)).decode('ascii')}"
        self._by_digest[digest] = uri
        return uri

    def _webp(self, raw: bytes, path: Path) -> bytes:
        from PIL import Image

        img = Image.open(io.BytesIO(raw))
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGB")

        width, height = img.size
        if width < self._min_width:
            self._warnings.append(
                f"{path.name} is only {width}px wide (below the {self._min_width}px "
                f"floor); recapture it larger or it will be hard to read on a phone"
            )
        if width > self._target_width:
            img = img.resize(
                (self._target_width, round(height * self._target_width / width)),
                Image.LANCZOS,
            )

        buf = io.BytesIO()
        img.save(buf, "WEBP", quality=self._quality, method=6)
        return buf.getvalue()
