import io

import pytest
from PIL import Image

from gui_agent_screenshot_tools import BBox, Screenshot, Space


@pytest.fixture
def hd_space():
    return Space(width=1920, height=1080)


@pytest.fixture
def square_space():
    return Space(width=1024, height=1024)


@pytest.fixture
def small_space():
    return Space(width=100, height=100)


@pytest.fixture
def mobile_space():
    return Space(width=1080, height=2400)


@pytest.fixture
def wxga_space():
    return Space(width=1366, height=768)


@pytest.fixture
def xga_space():
    return Space(width=1024, height=768)


@pytest.fixture
def sample_image_bytes():
    img = Image.new("RGB", (1920, 1080), color=(128, 64, 32))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def sample_screenshot(sample_image_bytes, hd_space):
    return Screenshot(image_bytes=sample_image_bytes, space=hd_space)


@pytest.fixture
def mobile_screenshot(mobile_space):
    img = Image.new("RGB", (mobile_space.width, mobile_space.height), color=(60, 180, 90))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return Screenshot(image_bytes=buf.getvalue(), space=mobile_space)


@pytest.fixture
def screen_space():
    return Space(width=2560, height=1440)


@pytest.fixture
def window_bbox(screen_space):
    return BBox(x=50, y=100, width=1920, height=1080, space=screen_space)
