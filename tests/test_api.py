"""API endpoint tests for Phase 2 — dual caption mode."""

from io import BytesIO
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)

# Minimal valid JPEG bytes for testing
_VALID_JPEG = (
    b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c"
    b"\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c"
    b"\x1c $.\' \",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x0b\x08"
    b"\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01"
    b"\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03"
    b"\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03"
    b"\x02\x04\x03\x05\x05\x04\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05"
    b"\x12!1A\x06\x13Qa\x07\"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0"
    b"\x24\x33\x62\xf2\x82\t\n\x16\x17\x18\x19\x1a%&\'()*456789:CDEFGHIJ"
    b"STUVWXYZcdefghijstuvwxyz\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94"
    b"\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3"
    b"\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2"
    b"\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9"
    b"\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xda\x00\x08\x01\x01"
    b"\x00\x00?\x00\xfb\xd5\xff\xd9"
)


def test_health_check():
    """Health endpoint reports Phase 2."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "OmniVision API"
    assert data["phase"] == "2"


@patch("backend.routes.caption.caption_service.generate_captions")
def test_caption_endpoint_dual_captions(mock_generate):
    """Caption endpoint returns both short and detailed captions."""
    mock_generate.return_value = {
        "short_caption": "A dog running on grass.",
        "detailed_caption": (
            "A golden retriever runs across a lush green lawn on a sunny day, "
            "with trees in the background."
        ),
    }

    response = client.post(
        "/caption",
        files={"file": ("test.jpg", BytesIO(_VALID_JPEG), "image/jpeg")},
    )

    assert response.status_code == 200
    data = response.json()

    # Phase 2 response structure
    assert "short_caption" in data
    assert "detailed_caption" in data
    assert data["short_caption"] == "A dog running on grass."
    assert "golden retriever" in data["detailed_caption"]
    assert "processing_time" in data
    assert data["processing_time"] >= 0
    assert "image_path" in data
    mock_generate.assert_called_once()


@patch("backend.routes.caption.caption_service.generate_captions")
def test_caption_processing_time_is_float(mock_generate):
    """Processing time is a non-negative float."""
    mock_generate.return_value = {
        "short_caption": "A cat sitting.",
        "detailed_caption": "A cat sitting on a windowsill looking outside.",
    }

    response = client.post(
        "/caption",
        files={"file": ("test.jpg", BytesIO(_VALID_JPEG), "image/jpeg")},
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["processing_time"], float)
    assert data["processing_time"] >= 0


def test_caption_rejects_invalid_type():
    """Non-image uploads are rejected with 400."""
    response = client.post(
        "/caption",
        files={"file": ("test.txt", BytesIO(b"not an image"), "text/plain")},
    )
    assert response.status_code == 400


def test_caption_rejects_empty_file():
    """Empty uploads are rejected with 400."""
    response = client.post(
        "/caption",
        files={"file": ("test.jpg", BytesIO(b""), "image/jpeg")},
    )
    assert response.status_code == 400


@patch("backend.routes.caption.caption_service.generate_captions")
def test_caption_response_schema_fields(mock_generate):
    """Response contains exactly the expected Phase 2 fields."""
    mock_generate.return_value = {
        "short_caption": "Short.",
        "detailed_caption": "A more detailed description.",
    }

    response = client.post(
        "/caption",
        files={"file": ("test.jpg", BytesIO(_VALID_JPEG), "image/jpeg")},
    )

    assert response.status_code == 200
    data = response.json()
    expected_keys = {"short_caption", "detailed_caption", "image_path", "processing_time"}
    assert set(data.keys()) == expected_keys
"""API endpoint tests for Phase 2 — dual caption mode."""

from io import BytesIO
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)

# Minimal valid JPEG bytes for testing
_VALID_JPEG = (
    b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c"
    b"\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c"
    b"\x1c $.\' \",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x0b\x08"
    b"\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01"
    b"\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03"
    b"\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03"
    b"\x02\x04\x03\x05\x05\x04\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05"
    b"\x12!1A\x06\x13Qa\x07\"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0"
    b"\x24\x33\x62\xf2\x82\t\n\x16\x17\x18\x19\x1a%&\'()*456789:CDEFGHIJ"
    b"STUVWXYZcdefghijstuvwxyz\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94"
    b"\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3"
    b"\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2"
    b"\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9"
    b"\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xda\x00\x08\x01\x01"
    b"\x00\x00?\x00\xfb\xd5\xff\xd9"
)


def test_health_check():
    """Health endpoint reports Phase 2."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "OmniVision API"
    assert data["phase"] == "2"


@patch("backend.routes.caption.caption_service.generate_captions")
def test_caption_endpoint_dual_captions(mock_generate):
    """Caption endpoint returns both short and detailed captions."""
    mock_generate.return_value = {
        "short_caption": "A dog running on grass.",
        "detailed_caption": (
            "A golden retriever runs across a lush green lawn on a sunny day, "
            "with trees in the background."
        ),
    }

    response = client.post(
        "/caption",
        files={"file": ("test.jpg", BytesIO(_VALID_JPEG), "image/jpeg")},
    )

    assert response.status_code == 200
    data = response.json()

    # Phase 2 response structure
    assert "short_caption" in data
    assert "detailed_caption" in data
    assert data["short_caption"] == "A dog running on grass."
    assert "golden retriever" in data["detailed_caption"]
    assert "processing_time" in data
    assert data["processing_time"] >= 0
    assert "image_path" in data
    mock_generate.assert_called_once()


@patch("backend.routes.caption.caption_service.generate_captions")
def test_caption_processing_time_is_float(mock_generate):
    """Processing time is a non-negative float."""
    mock_generate.return_value = {
        "short_caption": "A cat sitting.",
        "detailed_caption": "A cat sitting on a windowsill looking outside.",
    }

    response = client.post(
        "/caption",
        files={"file": ("test.jpg", BytesIO(_VALID_JPEG), "image/jpeg")},
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["processing_time"], float)
    assert data["processing_time"] >= 0


def test_caption_rejects_invalid_type():
    """Non-image uploads are rejected with 400."""
    response = client.post(
        "/caption",
        files={"file": ("test.txt", BytesIO(b"not an image"), "text/plain")},
    )
    assert response.status_code == 400


def test_caption_rejects_empty_file():
    """Empty uploads are rejected with 400."""
    response = client.post(
        "/caption",
        files={"file": ("test.jpg", BytesIO(b""), "image/jpeg")},
    )
    assert response.status_code == 400


@patch("backend.routes.caption.caption_service.generate_captions")
def test_caption_response_schema_fields(mock_generate):
    """Response contains exactly the expected Phase 2 fields."""
    mock_generate.return_value = {
        "short_caption": "Short.",
        "detailed_caption": "A more detailed description.",
    }

    response = client.post(
        "/caption",
        files={"file": ("test.jpg", BytesIO(_VALID_JPEG), "image/jpeg")},
    )

    assert response.status_code == 200
    data = response.json()
    expected_keys = {"short_caption", "detailed_caption", "image_path", "processing_time"}
    assert set(data.keys()) == expected_keys
"""API endpoint tests for Phase 1."""

from io import BytesIO
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "OmniVision API"
    assert data["phase"] == "1"


@patch("backend.routes.caption.blip_service.generate_caption")
def test_caption_endpoint(mock_generate):
    mock_generate.return_value = "A dog running on grass."

    image_bytes = (
        b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
        b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c"
        b"\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c"
        b"\x1c $.\' \",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x0b\x08"
        b"\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01"
        b"\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03"
        b"\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03"
        b"\x02\x04\x03\x05\x05\x04\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05"
        b"\x12!1A\x06\x13Qa\x07\"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0"
        b"\x24\x33\x62\xf2\x82\t\n\x16\x17\x18\x19\x1a%&\'()*456789:CDEFGHIJ"
        b"STUVWXYZcdefghijstuvwxyz\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94"
        b"\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3"
        b"\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2"
        b"\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9"
        b"\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xda\x00\x08\x01\x01"
        b"\x00\x00?\x00\xfb\xd5\xff\xd9"
    )

    response = client.post(
        "/caption",
        files={"file": ("test.jpg", BytesIO(image_bytes), "image/jpeg")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["caption"] == "A dog running on grass."
    assert "processing_time_seconds" in data
    assert "image_path" in data
    mock_generate.assert_called_once()


def test_caption_rejects_invalid_type():
    response = client.post(
        "/caption",
        files={"file": ("test.txt", BytesIO(b"not an image"), "text/plain")},
    )
    assert response.status_code == 400


def test_caption_rejects_empty_file():
    response = client.post(
        "/caption",
        files={"file": ("test.jpg", BytesIO(b""), "image/jpeg")},
    )
    assert response.status_code == 400
