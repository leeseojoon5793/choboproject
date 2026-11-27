"""원본·결과 비교 뷰어 + ROI 분석 (역할 C)."""
import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image

from algorithms.registry import ALGORITHMS, run_algorithm
from modules.auth import require_login
from modules.roi import roi_histogram, roi_stats
from modules.viewer_figure import build_compare_figure

uid, role = require_login()

st.title("CT 영상 뷰어")

# 케이스·영상 저장(B)과 연동하기 전까지는 PNG를 직접 올려서 확인한다
uploaded = st.file_uploader("저선량 CT PNG 불러오기 (임시)", type=["png", "jpg", "jpeg"])
if uploaded is None:
    st.info("PNG 파일을 올리면 원본과 처리 결과를 비교할 수 있어요.")
    st.stop()

original = np.array(Image.open(uploaded).convert("L"))
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
