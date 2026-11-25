from pathlib import Path

DEFAULT_DATA_DIR = Path("data")


def get_data_dir() -> Path:
    # secrets.toml에 data_dir가 있으면 그 폴더, 없으면 레포 안 data/
    try:
        import streamlit as st

        configured = st.secrets.get("data_dir")
        if configured:
            return Path(str(configured))
    except Exception:
        pass
    return DEFAULT_DATA_DIR


def data_path(relative_path: str) -> Path:
    rel = Path(relative_path)
    if rel.anchor or ".." in rel.parts:
        raise ValueError(f"data_dir 기준 상대 경로만 사용할 수 있습니다: {relative_path}")
    return get_data_dir() / rel