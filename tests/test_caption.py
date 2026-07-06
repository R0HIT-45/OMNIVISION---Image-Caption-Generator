"""Image utility unit tests."""

from io import BytesIO
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from backend.utils.image_utils import save_upload, validate_upload


def test_validate_upload_rejects_bad_extension():
    file = MagicMock()
    file.filename = "document.pdf"
    file.content_type = "application/pdf"

    with pytest.raises(HTTPException) as exc:
        validate_upload(file)

    assert exc.value.status_code == 400
    assert "Unsupported file type" in exc.value.detail


def test_validate_upload_accepts_jpg():
    file = MagicMock()
    file.filename = "photo.jpg"
    file.content_type = "image/jpeg"

    validate_upload(file)


def test_save_upload_persists_file(tmp_path, monkeypatch):
    import asyncio

    from backend.utils import config

    monkeypatch.setattr(config.settings, "upload_dir", str(tmp_path))

    file = AsyncMock()
    file.filename = "sample.png"
    file.content_type = "image/png"
    file.read = AsyncMock(return_value=b"\x89PNG\r\n\x1a\n" + b"\x00" * 64)

    saved_path = asyncio.run(save_upload(file))
    assert saved_path.exists()
    assert saved_path.suffix == ".png"
