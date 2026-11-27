import numpy as np

from modules.viewer_figure import build_compare_figure


def images():
    a = np.zeros((20, 30), dtype=np.uint8)
    b = np.full((20, 30), 100, dtype=np.uint8)
    return a, b


def test_two_images_side_by_side():
    a, b = images()
    fig = build_compare_figure(a, b)
    assert len(fig.data) == 2
    assert np.array_equal(np.asarray(fig.data[0].z), a)
    assert np.array_equal(np.asarray(fig.data[1].z), b)


def test_no_roi_no_rectangle():
    fig = build_compare_figure(*images())
    assert len(fig.layout.shapes) == 0


def test_roi_drawn_on_both_images():
    roi = {"x": 2, "y": 3, "w": 4, "h": 5}
    fig = build_compare_figure(*images(), roi=roi)
    assert len(fig.layout.shapes) == 2
    rect = fig.layout.shapes[0]
    assert (rect.x0, rect.y0, rect.x1, rect.y1) == (1.5, 2.5, 5.5, 7.5)
