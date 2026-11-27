import re

import streamlit as st

from modules.auth import require_login
from modules.case_repository import register_case, register_slice
from modules.case_validator import CaseValidationError, validate_image_file
from modules.db import get_db_or_none

FIXED_MANUFACTURER = "SIEMENS"
FIXED_MODEL = "Somatom Definition Flash"
FIXED_BODY_PART = "CHEST"
FIXED_SLICE_THICKNESS_MM = 1.5
FIXED_WINDOW_SETTING = {"center": -600, "width": 1500}


def _natural_sort_key(file_obj):
    parts = re.split(r"(\d+)", file_obj.name)
    return [int(p) if p.isdigit() else p.lower() for p in parts]


st.set_page_config(page_title="케이스 등록", layout="wide")
uid, role = require_login()

st.title("새 케이스 등록")

if role not in ("register", "admin"):
    st.warning("케이스 등록은 등록 담당(register) 또는 관리 담당(admin)만 이용할 수 있습니다.")
    st.stop()

st.subheader("장비 및 프로토콜 기본값 (고정)")
col1, col2, col3, col4 = st.columns(4)
col1.metric("제조사", FIXED_MANUFACTURER)
col2.metric("장비 모델", FIXED_MODEL)
col3.metric("촬영 부위", FIXED_BODY_PART)
col4.metric("슬라이스 두께", f"{FIXED_SLICE_THICKNESS_MM} mm")

with st.form("register_case_form"):
    case_id = st.text_input("케이스 ID *", placeholder="예: C002")
    title = st.text_input("케이스 제목 *", placeholder="예: 저선량 흉부 CT 케이스 #2")
    uploaded_files = st.file_uploader(
        "저선량 CT 슬라이스 PNG 파일 (여러 장 선택 가능, 파일명 숫자 순으로 정렬) *",
        type=["png"],
        accept_multiple_files=True,
    )
    submitted = st.form_submit_button("케이스 등록", type="primary")

if submitted:
    if not uploaded_files:
        st.error("최소 1장 이상의 PNG 파일을 업로드해 주세요.")
    else:
        sorted_files = sorted(uploaded_files, key=_natural_sort_key)
        prepared_files = [(f.name, f.getvalue()) for f in sorted_files]

        validation_failed = False
        for idx, (fname, fbytes) in enumerate(prepared_files, start=1):
            try:
                validate_image_file(fname, fbytes)
            except CaseValidationError as e:
                st.error(f"{idx}번째 파일({fname}) 검증 실패: {e}")
                validation_failed = True
                break

        if not validation_failed:
            total_slices = len(prepared_files)
            db = get_db_or_none()

            try:
                first_name, first_bytes = prepared_files[0]
                case_doc = register_case(
                    case_id=case_id,
                    title=title,
                    created_by=uid,
                    file_name=first_name,
                    file_bytes=first_bytes,
                    manufacturer=FIXED_MANUFACTURER,
                    model=FIXED_MODEL,
                    body_part=FIXED_BODY_PART,
                    slice_thickness_mm=FIXED_SLICE_THICKNESS_MM,
                    total_slices=total_slices,
                    window_setting=FIXED_WINDOW_SETTING,
                    firestore_client=db,
                )

                for idx, (fname, fbytes) in enumerate(prepared_files[1:], start=2):
                    register_slice(
                        case_id=case_doc["case_id"],
                        slice_index=idx,
                        file_name=fname,
                        file_bytes=fbytes,
                        uploaded_by=uid,
                        firestore_client=db,
                    )

                st.success(
                    f"케이스 '{case_doc['case_id']}' 등록이 완료되었습니다! (총 {total_slices}장 슬라이스)"
                )
            except CaseValidationError as e:
                st.error(f"입력값 검증 실패: {e}")
            except Exception as e:
                st.error(f"케이스 저장 중 오류가 발생했습니다: {e}")
