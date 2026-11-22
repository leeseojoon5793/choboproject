import streamlit as st
import numpy as np
import cv2

from algorithms.recommend import recommend_settings, apply_candidate, generate_candidates


def show_recommendation():
    st.header("영상 품질 알고리즘 추천")

    st.write(
        "CT 영상을 업로드하고 필터 파라미터를 직접 변경하여 "
        "여러 알고리즘 설정을 비교할 수 있습니다."
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
    st.image(img, caption="입력 CT 영상", clamp=True)

    st.divider()

    st.subheader("알고리즘 파라미터 실험")

    median_ksizes = st.multiselect(
        "Median 커널 크기",
        options=[3, 5, 7, 9],
        default=[3, 5, 7]
    )

    gaussian_ksizes = st.multiselect(
        "Gaussian 커널 크기",
        options=[3, 5, 7, 9],
        default=[3, 5, 7]
    )

    st.write("Bilateral 필터 설정")

    bilateral_d = st.slider(
        "필터 크기 (d)",
        min_value=1,
        max_value=15,
        value=9,
        step=2
    )

    bilateral_sigma_color = st.slider(
        "색상 강도 (sigmaColor)",
        min_value=10,
        max_value=150,
        value=75
    )

    bilateral_sigma_space = st.slider(
        "공간 강도 (sigmaSpace)",
        min_value=10,
        max_value=150,
        value=75
    )

    if st.button("파라미터 실험 및 추천 실행"):
        if not median_ksizes and not gaussian_ksizes:
            st.error("최소 하나의 필터 커널 크기를 선택해 주세요.")
            return

        try:
            results = recommend_settings(
                img,
                median_ksizes=tuple(median_ksizes),
                gaussian_ksizes=tuple(gaussian_ksizes),
                bilateral_d=bilateral_d,
                bilateral_sigma_color=bilateral_sigma_color,
                bilateral_sigma_space=bilateral_sigma_space
            )

            st.success("파라미터 실험이 완료되었습니다!")

            st.subheader("실험 결과")

            st.dataframe(
                results,
                use_container_width=True
            )

            best = results[0]

            st.success(
                f"가장 높은 점수의 설정: {best['설정']} "
                f"(점수: {best['점수']})"
            )

            candidates = generate_candidates(
                tuple(median_ksizes),
                tuple(gaussian_ksizes),
                bilateral_d,
                bilateral_sigma_color,
                bilateral_sigma_space
            )

            best_candidate = next(
                candidate for candidate in candidates
                if candidate["이름"] == best["설정"]
            )

            best_img = apply_candidate(img, best_candidate)

            st.subheader("추천 설정 적용 결과")

            st.image(
                best_img,
                caption=best["설정"],
                clamp=True
            )

            st.caption(
                "점수는 밝기, 대비, 선명도를 이용한 개발용 임시 지표입니다."
            )

        except ValueError as e:
            st.error(f"파라미터 오류: {e}")