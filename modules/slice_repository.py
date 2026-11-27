"""케이스별 슬라이스(images) 목록 조회 (역할 C).

B의 register_slice가 저장한 형식을 그대로 읽는다.
firestore_client가 있으면 Firestore images 컬렉션, 없으면 data_dir 아래 images_local.json.
"""
from pathlib import Path

from modules.case_repository import _load_json_dict, get_base_data_dir

LOCAL_IMAGES_NAME = "images_local.json"


def list_slices(case_id, firestore_client=None, local_images_db_path=None) -> list[dict]:
    """한 케이스의 슬라이스를 slice_index 순서로 돌려준다.

    file_path는 data_dir 기준 상대 경로 그대로 둔다. 파일은 뷰어에서 data_path()로 연다.
    """
    if firestore_client is not None:
        images = [doc.to_dict() for doc in firestore_client.collection("images").stream()]
    else:
        if local_images_db_path is not None:
            db_path = Path(local_images_db_path)
        else:
            db_path = get_base_data_dir() / LOCAL_IMAGES_NAME
        images = list(_load_json_dict(db_path).values())

    slices = [image for image in images if image.get("case_id") == case_id]
    return sorted(slices, key=lambda image: image["slice_index"])
