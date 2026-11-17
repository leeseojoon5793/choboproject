from pathlib import Path
import cv2
import numpy as np

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg"}


def validate_image_file(file_name: str, file_bytes: bytes) -> dict:
    """업로드된 파일의 확장자와 실제 이미지 디코딩 가능 여부를 검사한다."""
    if not file_name or not file_bytes:
        raise ValueError("파일이 비어 있습니다.")

    ext = Path(file_name).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError("PNG 또는 JPEG 파일만 업로드할 수 있습니다.")

    np_buf = np.frombuffer(file_bytes, dtype=np.uint8)
    img = cv2.imdecode(np_buf, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError("손상되었거나 올바른 이미지 형식이 아닙니다.")

    height, width = img.shape
    file_format = "PNG" if ext == ".png" else "JPEG"

    return {
        "file_format": file_format,
        "width": int(width),
        "height": int(height),
        "gray_image": img,
    }


def validate_case_id(case_id: str, existing_case_ids: set[str]) -> str:
    """케이스 ID의 공백 여부와 기존 케이스와의 중복 등록 여부를 검사한다."""
    cleaned_id = case_id.strip()
    if not cleaned_id:
        raise ValueError("케이스 ID를 입력해 주세요.")

    if cleaned_id in existing_case_ids:
        raise ValueError(f"이미 등록된 케이스 ID입니다: {cleaned_id}")

    return cleaned_id
