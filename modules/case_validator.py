import re
from pathlib import Path
import cv2
import numpy as np

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg"}
MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20MB
MIN_IMAGE_DIMENSION = 64
CASE_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


class CaseValidationError(ValueError):
    """케이스 입력 데이터 및 업로드 영상 검증 실패 시 발생하는 예외."""


def validate_case_id(
    case_id: str,
    existing_ids: set[str] | list[str] | None = None,
    firestore_client=None,
) -> str:
    """케이스 ID 형식(영문·숫자·-·_) 및 중복 여부를 검증한다."""
    if not isinstance(case_id, str) or not case_id.strip():
        raise CaseValidationError("케이스 ID를 입력해 주세요.")

    cleaned = case_id.strip()
    if not CASE_ID_PATTERN.match(cleaned):
        raise CaseValidationError(
            "케이스 ID는 영문, 숫자, 하이픈(-), 언더스코어(_)만 사용할 수 있습니다."
        )

    if firestore_client is not None:
        doc_snap = firestore_client.collection("cases").document(cleaned).get()
        if getattr(doc_snap, "exists", False):
            raise CaseValidationError(f"이미 등록된 케이스 ID입니다: {cleaned}")

    if existing_ids is not None and cleaned in set(existing_ids):
        raise CaseValidationError(f"이미 등록된 케이스 ID입니다: {cleaned}")

    return cleaned


def validate_image_file(file_name: str, file_bytes: bytes) -> dict:
    """OpenCV를 사용해 업로드된 이미지의 확장자, 용량, 디코딩 가능 여부, 최소 해상도를 검증한다."""
    if not file_name or not isinstance(file_name, str):
        raise CaseValidationError("파일 이름이 올바르지 않습니다.")

    ext = Path(file_name).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise CaseValidationError(
            f"지원하지 않는 파일 형식(확장자)입니다({ext}). PNG 또는 JPEG 파일만 업로드할 수 있습니다."
        )

    if not file_bytes or len(file_bytes) == 0:
        raise CaseValidationError("비어 있는 파일입니다.")

    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise CaseValidationError("파일 크기가 20MB를 초과합니다.")

    buf = np.frombuffer(file_bytes, dtype=np.uint8)
    decoded = cv2.imdecode(buf, cv2.IMREAD_UNCHANGED)
    if decoded is None or decoded.size == 0:
        raise CaseValidationError("손상되었거나 올바른 이미지 파일이 아닙니다.")

    height, width = decoded.shape[:2]
    channels = 1 if decoded.ndim == 2 else decoded.shape[2]
    mode = "L" if channels == 1 else ("RGBA" if channels == 4 else "RGB")
    fmt = "PNG" if ext == ".png" else "JPEG"

    if width < MIN_IMAGE_DIMENSION or height < MIN_IMAGE_DIMENSION:
        raise CaseValidationError(
            f"이미지 해상도가 너무 작습니다({width}x{height}). 최소 {MIN_IMAGE_DIMENSION}x{MIN_IMAGE_DIMENSION} 이상이어야 합니다."
        )

    return {
        "extension": ext,
        "file_format": fmt,
        "width": int(width),
        "height": int(height),
        "mode": mode,
        "size_bytes": len(file_bytes),
    }
