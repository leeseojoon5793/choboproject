import cv2
import numpy as np
import pytest
from modules.case_repository import register_case, register_slice
from modules.case_validator import CaseValidationError, validate_case_id, validate_image_file


def _make_png_bytes(width: int = 128, height: int = 128) -> bytes:
    img = np.full((height, width), 128, dtype=np.uint8)
    ok, encoded = cv2.imencode(".png", img)
    assert ok
    return encoded.tobytes()


def test_validate_image_file_rejects_oversized_file():
    oversized = b"0" * (20 * 1024 * 1024 + 1)
    with pytest.raises(CaseValidationError, match="20MB"):
        validate_image_file("big.png", oversized)


def test_validate_image_file_rejects_too_small_resolution():
    tiny_png = _make_png_bytes(width=32, height=32)
    with pytest.raises(CaseValidationError, match="64x64"):
        validate_image_file("tiny.png", tiny_png)


def test_validate_case_id_rejects_invalid_characters():
    with pytest.raises(CaseValidationError):
        validate_case_id("CT/001")


def test_register_slice_rolls_back_file_when_db_fails(tmp_path):
    class FailingFirestore:
        def collection(self, name):
            return self

        def document(self, doc_id):
            return self

        def get(self):
            class Snap:
                exists = False
            return Snap()

        def set(self, data):
            raise RuntimeError("Firestore 연결 실패")

    img_dir = tmp_path / "low_dose_images"
    png_bytes = _make_png_bytes()

    with pytest.raises(RuntimeError, match="Firestore 연결 실패"):
        register_slice(
            case_id="ERR-001",
            slice_index=1,
            file_name="001.png",
            file_bytes=png_bytes,
            uploaded_by="register-user-1",
            image_dir=img_dir,
            firestore_client=FailingFirestore(),
            data_dir=tmp_path,
        )

    assert not (img_dir / "ERR-001" / "001.png").exists()


def test_register_case_rolls_back_case_doc_when_slice_fails(tmp_path):
    deleted_cases = []

    class SliceFailingFirestore:
        def collection(self, name):
            self._col = name
            return self

        def document(self, doc_id):
            self._doc_id = doc_id
            return self

        def get(self):
            class Snap:
                exists = False
            return Snap()

        def set(self, data):
            if self._col == "images":
                raise RuntimeError("images 컬렉션 저장 실패")

        def delete(self):
            if self._col == "cases":
                deleted_cases.append(self._doc_id)

    img_dir = tmp_path / "low_dose_images"
    png_bytes = _make_png_bytes()

    with pytest.raises(RuntimeError, match="images 컬렉션 저장 실패"):
        register_case(
            case_id="ERR-002",
            title="롤백 테스트 케이스",
            created_by="register-user-1",
            file_name="001.png",
            file_bytes=png_bytes,
            image_dir=img_dir,
            firestore_client=SliceFailingFirestore(),
            data_dir=tmp_path,
        )

    # 슬라이스 등록 실패 시 파일 삭제 + 선저장된 cases 문서도 함께 삭제되어야 함
    assert not (img_dir / "ERR-002" / "001.png").exists()
    assert deleted_cases == ["ERR-002"]
