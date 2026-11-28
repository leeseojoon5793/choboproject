import streamlit as st
import numpy as np
import cv2

from algorithms.recommend import (
    recommend_settings,
    apply_candidate,
    generate_candidates
)


def show_roi_inputs(img):
    height, width = img.shape

    roi_width = min(30, width)
    roi_height = min(30, height)

    st.subheader("관심 영역(ROI) 설정")

    st.write(
        "평평한 영역, 병변 영역, 주변 영역의 "
        "좌표를 각각 입력해 주세요."
    )

    roi_configs = [
        ("평평한 영역", "flat", 0, 0),
        ("병변 영역", "lesion", width // 3, height // 3),
        ("주변 영역", "background", (width * 2) // 3, (height * 2) // 3)
    ]

    rois = {}

    for label, key, default_x, default_y in roi_configs:
        st.markdown(f"**{label}**")

        col1, col2 = st.columns(2)

        with col1:
            x = st.number_input(
                f"{label} X 좌표",
                min_value=0,
                max_value=width - 1,
                value=min(default_x, width - 1),
                key=f"{key}_x"
            )

            w = st.number_input(
                f"{label} 폭",
                min_value=1,
                max_value=width,
                value=roi_width,
                key=f"{key}_w"
            )

        with col2:
            y = st.number_input(
                f"{label} Y 좌표",
                min_value=0,
                max_value=height - 1,
                value=min(default_y, height - 1),
                key=f"{key}_y"
            )

            h = st.number_input(
                f"{label} 높이",
                min_value=1,
                max_value=height,
                value=roi_height,
                key=f"{key}_h"
            )

        rois[key] = {
            "x": int(x),
            "y": int(y),
            "w": int(w),
            "h": int(h)
        }

        if x + w > width or y + h > height:
            st.error(f"{label} ROI가 영상 범위를 벗어났습니다.")

    return (
        rois["flat"],
        rois["lesion"],
        rois["background"]
    )


def show_recommendation():
    st.header("영상 품질 알고리즘 추천")

    st.write(
        "CT 영상을 업로드하고 ROI를 설정하면 "
        "잡음 감소율과 경계 보존율을 기준으로 "
        "적합한 필터를 추천합니다."
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

    st.caption(
        f"영상 크기: 가로 {img.shape[1]}px × 세로 {img.shape[0]}px"
    )

    st.divider()

    flat_roi, lesion_roi, background_roi = show_roi_inputs(img)

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
                flat_roi=flat_roi,
                lesion_roi=lesion_roi,
                background_roi=background_roi,
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

            best_img = apply_candidate(
                img,
                best_candidate
            )

            st.subheader("추천 설정 적용 결과")

            col1, col2 = st.columns(2)

            with col1:
                st.image(
                    img,
                    caption="처리 전 영상",
                    clamp=True
                )

            with col2:
                st.image(
                    best_img,
                    caption="추천 필터 적용 영상",
                    clamp=True
                )

            st.subheader("추천 품질 지표")

            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    "잡음 감소율",
                    f"{best['잡음 감소율'] * 100:.2f}%"
                )

            with col2:
                st.metric(
                    "경계 보존율",
                    f"{best['경계 보존율'] * 100:.2f}%"
                )

            st.caption(
                "추천 점수는 잡음 감소율과 경계 보존율을 "
                "각각 최대 50점씩 반영합니다."
            )

        except ValueError as e:
            st.error(f"품질 평가 오류: {e}")