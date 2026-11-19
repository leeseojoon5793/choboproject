from unittest.mock import MagicMock
import cv2
import numpy as np
import pytest
from modules.case_repository import register_case
from modules.case_validator import validate_case_id, validate_image_file


def _make_png_bytes(width: int = 128, height: int = 128) -> bytes:
    img = np.zeros((height, width), dtype=np.uint8)
    ok, buf = cv2.imencode(".png", img)
    assert ok
    return buf.tobytes()


def test_validate_image_file_rejects_oversized_file():
    png_bytes = _make_png_bytes(128, 128)
    with pytest.raises(ValueError, match="크기"):
        validate_image_file("large.png", png_bytes, max_size_bytes=10)


def test_validate_image_file_rejects_too_small_resolution():
    small_png = _make_png_bytes(32, 32)
    with pytest.raises(ValueError, match="해상도"):
        validate_image_file("tiny.png", small_png)


def test_validate_case_id_rejects_invalid_characters():
    with pytest.raises(ValueError, match="영문, 숫자"):
        validate_case_id("../C002", set())


def test_register_case_with_firebase_storage_and_firestore():
    png_bytes = _make_png_bytes(128, 128)

    mock_firestore = MagicMock()
    mock_firestore.collection.return_value.stream.return_value = []

    mock_blob = MagicMock()
    mock_blob.public_url = "https://storage.googleapis.com/bucket/cases/C002/low_dose.png"
    mock_bucket = MagicMock()
    mock_bucket.blob.return_value = mock_blob

    result = register_case(
        case_id="C002",
        title="Siemens Chest Low Dose",
        file_name="slice_001.png",
        file_bytes=png_bytes,
        created_by="user_b",
        firestore_client=mock_firestore,
        storage_bucket=mock_bucket,
    )

    assert result["storage_type"] == "firebase_storage"
    assert result["image_path"] == "cases/C002/low_dose.png"
    assert result["image_url"] == "https://storage.googleapis.com/bucket/cases/C002/low_dose.png"
    mock_blob.upload_from_string.assert_called_once()
    mock_firestore.collection.return_value.document.return_value.set.assert_called_once()
