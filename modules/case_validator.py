from pathlib import Path
import re
import cv2
import numpy as np

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg"}
MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20MB
MIN_IMAGE_DIMENSION = 64
CASE_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


def validate_image_file(
    file_name: str,
    file_bytes: bytes,
    max_size_bytes: int = MAX_FILE_SIZE_BYTES,
) -> dict:
    """업로드된 파일의 확장자, 크기, 해상도 및 실제 이미지 디코딩 가능 여부를 검사한다."""
    if not file_name or not file_bytes:
        raise ValueError("파일이 비어 있습니다.")

    if len(file_bytes) > max_size_bytes:
        raise ValueError(f"파일 크기가 제한({max_size_bytes // (1024 * 1024)}MB)을 초과했습니다.")

    ext = Path(file_name).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError("PNG 또는 JPEG 파일만 업로드할 수 있습니다.")

    np_buf = np.frombuffer(file_bytes, dtype=np.uint8)
    img = cv2.imdecode(np_buf, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError("손상되었거나 올바른 이미지 형식이 아닙니다.")

    height, width = img.shape
    if width < MIN_IMAGE_DIMENSION or height < MIN_IMAGE_DIMENSION:
        raise ValueError(f"이미지 해상도가 너무 작습니다. (최소 {MIN_IMAGE_DIMENSION}x{MIN_IMAGE_DIMENSION})")

    file_format = "PNG" if ext == ".png" else "JPEG"

    return {
        "file_format": file_format,
        "width": int(width),
        "height": int(height),
        "size_bytes": len(file_bytes),
        "gray_image": img,
    }


def validate_case_id(case_id: str, existing_case_ids: set[str]) -> str:
    """케이스 ID의 공백, 허용 문자 패턴 및 기존 케이스와의 중복 등록 여부를 검사한다."""
    cleaned_id = case_id.strip()
    if not cleaned_id:
        raise ValueError("케이스 ID를 입력해 주세요.")

    if not CASE_ID_PATTERN.match(cleaned_id):
        raise ValueError("케이스 ID는 영문, 숫자, 하이픈(-), 언더스코어(_)만 사용할 수 있습니다.")

    if cleaned_id in existing_case_ids:
        raise ValueError(f"이미 등록된 케이스 ID입니다: {cleaned_id}")

    return cleaned_id
