import numpy as np

from preprocessing.grid_suppress import foreground_data_mask, suppress_grid_and_axes


def test_foreground_mask_smaller_than_plot_mask():
    img = np.ones((200, 300, 3), dtype=np.uint8) * 255
    plot = np.zeros((200, 300), np.uint8)
    plot[40:180, 50:280] = 255
    for y in range(40, 180, 20):
        img[y, 50:280] = [200, 200, 200]
    cleaned = foreground_data_mask(img, plot)
    assert cleaned.sum() <= plot.sum()
    assert cleaned.sum() > 0


def test_suppress_returns_same_shape():
    img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    plot = np.ones((100, 100), np.uint8) * 255
    out = suppress_grid_and_axes(img, plot)
    assert out.shape == plot.shape
