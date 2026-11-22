import streamlit as st
import numpy as np
import cv2

from algorithms.recommend import recommend_settings


def show_recommendation():
    st.header("영상 품질 알고리즘 추천")

    st.write(
        "CT 영상을 업로드하면 여러 필터 설정을 비교하고 "
        "품질 점수를 기준으로 추천합니다."
    )

    uploaded_file = st.file_uploader(
        "CT 영상 업로드",
        type=["png", "jpg", "jpeg"]
    )

    if uploaded_file is None:
        st.info("PNG 또는 JPG 영상을 업로드해 주세요.")
        return

    file_bytes = np.frombuffer(
        uploaded_file.getvalue(),
        dtype=np.uint8
    )

    img = cv2.imdecode(
        file_bytes,
        cv2.IMREAD_GRAYSCALE
    )

    if img is None:
        st.error("이미지를 불러올 수 없습니다.")
        return

    st.subheader("업로드한 영상")
    st.image(
        img,
        caption="입력 CT 영상",
        clamp=True
    )

    if st.button("알고리즘 추천 실행"):
        results = recommend_settings(img)

        st.subheader("알고리즘 추천 결과")

        best = results[0]

        st.success(
            f"추천 설정: {best['설정']} "
            f"(점수: {best['점수']})"
        )

        st.write("후보별 품질 평가 결과")

        st.dataframe(
            results,
            use_container_width=True
        )

        st.write("점수가 높은 순서대로 정렬된 결과입니다.")