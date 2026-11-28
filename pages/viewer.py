"""케이스·슬라이스 뷰어 + 원본·결과 비교 + ROI 분석 + 처리 이력 (역할 C)."""
import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image

from algorithms.registry import ALGORITHMS, run_algorithm
from modules.auth import require_login
from modules.case_service import list_visible_cases
from modules.db import get_db_or_none
from modules.paths import data_path
from modules.permissions import can_edit
from modules.process_log import list_process_logs
from modules.result_image import save_processed_result
from modules.roi import roi_histogram, roi_stats
from modules.slice_repository import list_slices
from modules.viewer_figure import build_compare_figure

uid, role = require_login()
db = get_db_or_none()

st.title("CT 영상 뷰어")

# ---------- 케이스·슬라이스 선택 ----------
cases = list_visible_cases(db, role, uid)
if not cases:
    st.info("볼 수 있는 케이스가 없습니다.")
    st.stop()

case = st.selectbox(
    "케이스", cases,
    format_func=lambda c: f"{c['case_id']} · {c.get('title', '')} ({c.get('status', '')})",
)

slices = list_slices(case["case_id"], firestore_client=db)
if not slices:
    st.info("이 케이스에 등록된 슬라이스가 없습니다.")
    st.stop()

current = st.selectbox(
    f"슬라이스 (총 {len(slices)}장)", slices, format_func=lambda s: f"{s['slice_index']:03d}"
)
image_id = current["image_id"]

try:
    original = np.array(Image.open(data_path(current["file_path"])).convert("L"))
except (OSError, ValueError) as e:
    st.error(f"영상을 열 수 없습니다: {e}")
    st.stop()
height, width = original.shape

# ---------- 알고리즘 선택 + 파라미터 ----------
st.sidebar.header("알고리즘")
key = st.sidebar.selectbox(
    "알고리즘", list(ALGORITHMS), format_func=lambda k: ALGORITHMS[k]["label"]
)
params = {}
for name, spec in ALGORITHMS[key]["params"].items():
    params[name] = st.sidebar.slider(
        name, min_value=spec["min"], max_value=spec["max"],
        value=spec["default"], step=spec["step"], key=f"{key}_{name}",
    )

try:
    processed = run_algorithm(key, original, params)
except ValueError as e:
    st.error(str(e))
    st.stop()

# ---------- ROI 입력 ----------
st.sidebar.header("ROI (픽셀)")
size = min(64, width, height)
x = st.sidebar.number_input("x (가로 시작)", 0, width - 1, (width - size) // 2)
y = st.sidebar.number_input("y (세로 시작)", 0, height - 1, (height - size) // 2)
w = st.sidebar.number_input("w (폭)", 1, width, size)
h = st.sidebar.number_input("h (높이)", 1, height, size)
roi = {"x": int(x), "y": int(y), "w": int(w), "h": int(h)}

try:
    before = roi_stats(original, roi)
    after = roi_stats(processed, roi)
    roi_ok = True
except ValueError as e:
    st.warning(f"ROI를 확인해 주세요: {e}")
    roi_ok = False

# ---------- 원본 | 결과 ----------
fig = build_compare_figure(original, processed, roi if roi_ok else None)
st.plotly_chart(fig, config={"scrollZoom": True})
st.caption("휠: 확대·축소 / 드래그: 이동 / 더블클릭: 처음 크기로")

# ---------- ROI 통계 + 히스토그램 ----------
if roi_ok:
    st.subheader("ROI 통계")
    c1, c2, c3 = st.columns(3)
    c1.metric("평균 (원본 → 결과)", f"{after['mean']:.1f}", f"{after['mean'] - before['mean']:+.1f}")
    c2.metric("표준편차 (원본 → 결과)", f"{after['std']:.1f}", f"{after['std'] - before['std']:+.1f}")
    c3.metric("분산 (원본 → 결과)", f"{after['var']:.1f}", f"{after['var'] - before['var']:+.1f}")

    bins = 64
    hist_before, _ = roi_histogram(original, roi, bins=bins)
    hist_after, _ = roi_histogram(processed, roi, bins=bins)
    st.subheader("ROI 밝기 히스토그램")
    st.line_chart(
        pd.DataFrame(
            {"원본": hist_before, "결과": hist_after},
            index=np.arange(0, 256, 256 // bins),
        )
    )

# ---------- 처리 결과 저장 ----------
st.subheader("처리 이력")
if can_edit(role, uid, case):
    if st.button("이 결과 저장", disabled=not roi_ok):
        metrics = {
            "before": {k: float(v) for k, v in before.items()},
            "after": {k: float(v) for k, v in after.items()},
        }
        try:
            save_processed_result(
                role, uid, case, image_id, key, ALGORITHMS[key]["version"],
                params, roi, processed, metrics, firestore_client=db,
            )
        except Exception as e:
            st.error(f"저장하지 못했습니다: {e}")
        else:
            st.success("처리 결과를 저장했습니다.")
else:
    st.caption("이 케이스는 보기만 할 수 있습니다. (저장 권한 없음)")

# ---------- 이 슬라이스의 이전 처리 기록 ----------
logs = list_process_logs(image_id, firestore_client=db)
if not logs:
    st.caption("이 슬라이스에 저장된 처리 이력이 없습니다.")
else:
    rows = []
    for log in logs:
        label = ALGORITHMS.get(log["algorithm"], {}).get("label", log["algorithm"])
        std_after = log["metrics"].get("after", {}).get("std")
        rows.append({
            "시각 (UTC)": log["created_at"],
            "알고리즘": label,
            "파라미터": ", ".join(f"{k}={v}" for k, v in log["params"].items()),
            "ROI": str(log["roi"]),
            "결과 표준편차": None if std_after is None else round(std_after, 2),
            "실행자": log["run_by"],
        })
    st.dataframe(pd.DataFrame(rows), hide_index=True)
