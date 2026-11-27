"""원본·결과 비교용 Plotly 그림 (역할 C)."""
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

GRAY = [[0, "black"], [1, "white"]]


def build_compare_figure(
    original: np.ndarray, processed: np.ndarray, roi: dict | None = None
) -> go.Figure:
    """원본과 결과를 나란히 그린다. 두 칸은 확대·이동이 같이 움직이고, ROI가 있으면 빨간 사각형을 그린다."""
    fig = make_subplots(
        rows=1, cols=2, shared_xaxes="all", shared_yaxes="all",
        subplot_titles=("원본", "결과"), horizontal_spacing=0.03,
    )
    for col, img in enumerate((original, processed), start=1):
        fig.add_trace(
            go.Heatmap(
                z=img, colorscale=GRAY, zmin=0, zmax=255, showscale=False,
                hovertemplate="x=%{x}, y=%{y}, 밝기=%{z}<extra></extra>",
            ),
            row=1, col=col,
        )
        if roi is not None:
            # 히트맵의 픽셀 중심은 정수 좌표라서, 칸 테두리에 맞추려고 0.5씩 뺀다
            fig.add_shape(
                type="rect",
                x0=roi["x"] - 0.5, y0=roi["y"] - 0.5,
                x1=roi["x"] + roi["w"] - 0.5, y1=roi["y"] + roi["h"] - 0.5,
                line=dict(color="red", width=2), row=1, col=col,
            )
    # 영상은 위가 0행이라 y축을 뒤집고, 픽셀이 정사각형으로 보이게 비율을 고정
    fig.update_yaxes(autorange="reversed", scaleanchor="x", scaleratio=1)
    fig.update_xaxes(constrain="domain")
    fig.update_yaxes(constrain="domain")
    fig.update_layout(height=520, margin=dict(l=10, r=10, t=40, b=10), dragmode="pan")
    return fig
