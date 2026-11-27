import json

from modules.slice_repository import list_slices


def image_doc(case_id, slice_index):
    """B의 register_slice가 저장하는 형식과 같은 딕셔너리."""
    image_id = f"{case_id}_{slice_index:03d}"
    return {
        "image_id": image_id,
        "case_id": case_id,
        "slice_index": slice_index,
        "z_position": None,
        "file_path": f"low_dose_images/{case_id}/{slice_index:03d}.png",
        "width": 512,
        "height": 512,
        "size_bytes": 1000,
        "uploaded_by": "reg-1",
        "uploaded_at": "2026-11-27T10:00:00Z",
    }


def write_local(path, docs):
    path.write_text(json.dumps({d["image_id"]: d for d in docs}), encoding="utf-8")


class FakeDoc:
    def __init__(self, data):
        self._data = data

    def to_dict(self):
        return dict(self._data)


class FakeFirestore:
    """collection("images").stream()만 흉내 낸다."""

    def __init__(self, docs):
        self.docs = docs
        self.collection_name = None

    def collection(self, name):
        self.collection_name = name
        return self

    def stream(self):
        return [FakeDoc(d) for d in self.docs]


def test_only_given_case_sorted_by_slice_index(tmp_path):
    db_path = tmp_path / "images_local.json"
    write_local(db_path, [image_doc("C001", 2), image_doc("C002", 0), image_doc("C001", 0), image_doc("C001", 1)])

    slices = list_slices("C001", local_images_db_path=db_path)

    assert [s["image_id"] for s in slices] == ["C001_000", "C001_001", "C001_002"]


def test_file_path_stays_relative(tmp_path):
    db_path = tmp_path / "images_local.json"
    write_local(db_path, [image_doc("C001", 0)])

    assert list_slices("C001", local_images_db_path=db_path)[0]["file_path"] == "low_dose_images/C001/000.png"


def test_unknown_case_is_empty(tmp_path):
    db_path = tmp_path / "images_local.json"
    write_local(db_path, [image_doc("C001", 0)])

    assert list_slices("C999", local_images_db_path=db_path) == []


def test_missing_file_is_empty(tmp_path):
    assert list_slices("C001", local_images_db_path=tmp_path / "none.json") == []


def test_default_path_follows_data_dir(tmp_path, monkeypatch):
    monkeypatch.setattr("modules.slice_repository.get_base_data_dir", lambda: tmp_path)
    write_local(tmp_path / "images_local.json", [image_doc("C001", 0)])

    assert [s["image_id"] for s in list_slices("C001")] == ["C001_000"]


def test_firestore_filters_and_sorts():
    db = FakeFirestore([image_doc("C001", 1), image_doc("C002", 0), image_doc("C001", 0)])

    slices = list_slices("C001", firestore_client=db)

    assert db.collection_name == "images"
    assert [s["image_id"] for s in slices] == ["C001_000", "C001_001"]
