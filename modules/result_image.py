"""처리 결과 영상 저장 (역할 C). 경로는 data_dir 기준 상대 경로로 다룬다."""
from datetime import datetime, timezone

import numpy as np
from PIL import Image

from modules.paths import data_path


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
