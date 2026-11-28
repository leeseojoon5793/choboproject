"""처리 결과 영상 저장 (역할 C). 경로는 data_dir 기준 상대 경로로 다룬다."""
from datetime import datetime, timezone

import numpy as np
from PIL import Image

from modules.paths import data_path
from modules.process_log import save_process_log


def make_result_path(case_id, image_id, algorithm, now=None) -> str:
    """results/케이스/영상_알고리즘_UTC시각.png 형태의 상대 경로를 만든다."""
    now = now or datetime.now(timezone.utc)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    return f"results/{case_id}/{image_id}_{algorithm}_{stamp}.png"


def save_result_image(img: np.ndarray, result_path: str) -> None:
    """흑백 결과 영상을 data_dir 아래 result_path에 PNG로 저장한다."""
    path = data_path(result_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(img).save(path)


def save_processed_result(
    role, uid, case, image_id, algorithm, algorithm_version, params, roi, img, metrics,
    firestore_client=None, local_db_path=None,
) -> dict:
    """결과 영상을 저장하고 처리 이력을 남긴다.

    이력 저장이 어떤 이유로든 실패하면 방금 저장한 영상 파일을 지우고 예외를 그대로 올린다.
    권한 검사(can_edit)는 save_process_log 안에서 한다.
    """
    result_path = make_result_path(case["case_id"], image_id, algorithm)
    save_result_image(img, result_path)
    try:
        return save_process_log(
            role, uid, case, image_id, algorithm, algorithm_version,
            params, roi, result_path, metrics,
            firestore_client=firestore_client, local_db_path=local_db_path,
        )
    except Exception:
        data_path(result_path).unlink(missing_ok=True)
        raise
