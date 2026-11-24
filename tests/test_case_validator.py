import cv2
import numpy as np
import pytest
from modules.case_validator import validate_case_id, validate_image_file


def _make_sample_image_bytes(ext: str) -> bytes:
    sample = np.zeros((64, 80), dtype=np.uint8)
    ok, encoded = cv2.imencode(ext, sample)
    assert ok
    return encoded.tobytes()


def test_validate_image_file_png_and_jpeg():
    png_bytes = _make_sample_image_bytes(".png")
    res_png = validate_image_file("ultrasound_01.PNG", png_bytes)
    assert res_png["file_format"] == "PNG"
    assert (res_png["width"], res_png["height"]) == (80, 64)

    jpg_bytes = _make_sample_image_bytes(".jpg")
    res_jpg = validate_image_file("ultrasound_02.jpeg", jpg_bytes)
    assert res_jpg["file_format"] == "JPEG"


def test_validate_image_file_rejects_invalid_extension():
    with pytest.raises(ValueError, match="PNG 또는 JPEG"):
        validate_image_file("report.txt", b"hello")


def test_validate_image_file_rejects_corrupted_bytes():
    with pytest.raises(ValueError, match="손상되었거나"):
        validate_image_file("fake.png", b"not-a-real-image")


def test_validate_case_id_duplicate_and_empty():
    existing = {"US-20261114-001", "US-20261114-002"}

    assert validate_case_id(" US-20261114-003 ", existing) == "US-20261114-003"

    with pytest.raises(ValueError, match="이미 등록된"):
        validate_case_id("US-20261114-001", existing)

    with pytest.raises(ValueError, match="케이스 ID를 입력"):
        validate_case_id("   ", existing)
