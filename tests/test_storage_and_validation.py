import io
import pytest
from PIL import Image
from modules.case_repository import register_case, register_slice
from modules.case_validator import CaseValidationError, validate_case_id, validate_image_file


def _make_png_bytes(width: int = 128, height: int = 128) -> bytes:
    img = Image.new("L", (width, height), color=128)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


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
            image_dir=img_dir,
            firestore_client=FailingFirestore(),
        )

    # DB 저장 실패 시 방금 생성된 이미지 파일이 삭제되어 남지 않아야 함
    assert not (img_dir / "ERR-001" / "001.png").exists()


def test_register_case_rolls_back_file_when_db_fails(tmp_path):
    class FailingCaseFirestore:
        def collection(self, name):
            self._col = name
            return self

        def document(self, doc_id):
            return self

        def get(self):
            class Snap:
                exists = False
            return Snap()

        def set(self, data):
            if self._col == "cases":
                raise RuntimeError("cases 컬렉션 저장 실패")

    img_dir = tmp_path / "low_dose_images"
    png_bytes = _make_png_bytes()

    with pytest.raises(RuntimeError, match="cases 컬렉션 저장 실패"):
        register_case(
            case_id="ERR-002",
            title="롤백 테스트 케이스",
            file_name="001.png",
            file_bytes=png_bytes,
            image_dir=img_dir,
            firestore_client=FailingCaseFirestore(),
        )

    assert not (img_dir / "ERR-002" / "001.png").exists()
