import pytest

from gui_agent_screenshot_tools import Coordinate, ResizeMode, Space
from gui_agent_screenshot_tools.resize import (
    ResizeMetadata,
    compute_letterbox_metadata,
    compute_stretch_metadata,
)


@pytest.fixture
def hd():
    return Space(width=1920, height=1080)


@pytest.fixture
def square():
    return Space(width=1024, height=1024)


@pytest.fixture
def tall():
    return Space(width=1080, height=1920)


@pytest.fixture
def mobile():
    return Space(width=1080, height=2400)


@pytest.fixture
def wxga():
    return Space(width=1366, height=768)


@pytest.fixture
def xga():
    return Space(width=1024, height=768)


class TestStretchMetadata:
    def test_basic_values(self, hd, square):
        m = compute_stretch_metadata(hd, square)
        assert m.source_space == hd
        assert m.target_space == square
        assert m.mode == ResizeMode.STRETCH
        assert m.offset_x == 0
        assert m.offset_y == 0
        assert m.scaled_width == 1024
        assert m.scaled_height == 1024

    def test_forward_center(self, hd, square):
        m = compute_stretch_metadata(hd, square)
        center = Coordinate(x=960, y=540, space=hd)
        result = m.forward_transform_coordinate(center)
        assert result.space == square
        assert abs(result.x - 512) <= 1
        assert abs(result.y - 512) <= 1

    def test_inverse_center(self, hd, square):
        m = compute_stretch_metadata(hd, square)
        center = Coordinate(x=512, y=512, space=square)
        result = m.transform_coordinate(center, hd)
        assert result.space == hd
        assert abs(result.x - 960) <= 1
        assert abs(result.y - 540) <= 1

    def test_roundtrip(self, hd, square):
        m = compute_stretch_metadata(hd, square)
        original = Coordinate(x=500, y=300, space=hd)
        forward = m.forward_transform_coordinate(original)
        back = m.transform_coordinate(forward, hd)
        assert abs(back.x - original.x) <= 1
        assert abs(back.y - original.y) <= 1


class TestLetterboxMetadataWiderSource:
    """1920x1080 -> 1024x1024: width-limited, black bars top/bottom."""

    def test_scale(self, hd, square):
        m = compute_letterbox_metadata(hd, square)
        expected_scale = 1024 / 1920
        assert m.scale == pytest.approx(expected_scale, rel=1e-6)

    def test_offset(self, hd, square):
        m = compute_letterbox_metadata(hd, square)
        assert m.offset_x == 0
        assert m.offset_y > 0  # Black bars top/bottom

    def test_scaled_dimensions(self, hd, square):
        m = compute_letterbox_metadata(hd, square)
        assert m.scaled_width == 1024
        assert m.scaled_height < 1024

    def test_image_centered_vertically(self, hd, square):
        m = compute_letterbox_metadata(hd, square)
        assert m.offset_y + m.scaled_height + m.offset_y == square.height


class TestLetterboxMetadataTallerSource:
    """1080x1920 -> 1024x1024: height-limited, black bars left/right."""

    def test_offset(self, tall, square):
        m = compute_letterbox_metadata(tall, square)
        assert m.offset_x > 0  # Black bars left/right
        assert m.offset_y == 0

    def test_scaled_dimensions(self, tall, square):
        m = compute_letterbox_metadata(tall, square)
        assert m.scaled_width < 1024
        assert m.scaled_height == 1024


class TestLetterboxMetadataSameRatio:
    """Same aspect ratio -> no padding."""

    def test_no_offset(self):
        source = Space(width=1920, height=1080)
        target = Space(width=960, height=540)
        m = compute_letterbox_metadata(source, target)
        assert m.offset_x == 0
        assert m.offset_y == 0
        assert m.scaled_width == 960
        assert m.scaled_height == 540


class TestLetterboxForwardInverse:
    def test_center_roundtrip(self, hd, square):
        m = compute_letterbox_metadata(hd, square)
        original = Coordinate(x=960, y=540, space=hd)
        forward = m.forward_transform_coordinate(original)
        back = m.transform_coordinate(forward, hd)
        assert abs(back.x - original.x) <= 1
        assert abs(back.y - original.y) <= 1

    def test_origin_roundtrip(self, hd, square):
        m = compute_letterbox_metadata(hd, square)
        original = Coordinate(x=0, y=0, space=hd)
        forward = m.forward_transform_coordinate(original)
        back = m.transform_coordinate(forward, hd)
        assert abs(back.x - original.x) <= 1
        assert abs(back.y - original.y) <= 1

    def test_corner_roundtrip(self, hd, square):
        m = compute_letterbox_metadata(hd, square)
        original = Coordinate(x=1919, y=1079, space=hd)
        forward = m.forward_transform_coordinate(original)
        back = m.transform_coordinate(forward, hd)
        assert abs(back.x - original.x) <= 1
        assert abs(back.y - original.y) <= 1


class TestLetterboxMobileToWxga:
    """1080x2400 (mobile portrait) -> 1366x768 (WXGA): height-limited, bars on left/right."""

    def test_scale(self, mobile, wxga):
        m = compute_letterbox_metadata(mobile, wxga)
        expected_scale = 768 / 2400
        assert m.scale == pytest.approx(expected_scale, rel=1e-6)

    def test_bars_on_sides_only(self, mobile, wxga):
        m = compute_letterbox_metadata(mobile, wxga)
        assert m.offset_x > 0  # Black bars left/right
        assert m.offset_y == 0  # No top/bottom bars

    def test_scaled_dimensions(self, mobile, wxga):
        m = compute_letterbox_metadata(mobile, wxga)
        assert m.scaled_width == round(1080 * (768 / 2400))
        assert m.scaled_height == 768

    def test_image_centered(self, mobile, wxga):
        m = compute_letterbox_metadata(mobile, wxga)
        # Left bar + content + right bar = target width
        assert m.offset_x + m.scaled_width + m.offset_x == wxga.width

    def test_center_roundtrip(self, mobile, wxga):
        m = compute_letterbox_metadata(mobile, wxga)
        original = Coordinate(x=540, y=1200, space=mobile)
        forward = m.forward_transform_coordinate(original)
        back = m.transform_coordinate(forward, mobile)
        assert abs(back.x - original.x) <= 1
        assert abs(back.y - original.y) <= 1

    def test_all_corners_roundtrip(self, mobile, wxga):
        m = compute_letterbox_metadata(mobile, wxga)
        corners = [(0, 0), (1079, 0), (0, 2399), (1079, 2399)]
        for cx, cy in corners:
            c = Coordinate(x=cx, y=cy, space=mobile)
            fwd = m.forward_transform_coordinate(c)
            back = m.transform_coordinate(fwd, mobile)
            assert abs(back.x - cx) <= 1, f"x roundtrip failed for ({cx}, {cy})"
            assert abs(back.y - cy) <= 1, f"y roundtrip failed for ({cx}, {cy})"

    def test_left_padding_clamps_to_source_edge(self, mobile, wxga):
        m = compute_letterbox_metadata(mobile, wxga)
        # x=0 is in the left black bar
        coord = Coordinate(x=0, y=384, space=wxga)
        result = m.transform_coordinate(coord, mobile)
        assert result.x == 0  # Clamped to left edge

    def test_right_padding_clamps_to_source_edge(self, mobile, wxga):
        m = compute_letterbox_metadata(mobile, wxga)
        # x=1365 is in the right black bar
        coord = Coordinate(x=1365, y=384, space=wxga)
        result = m.transform_coordinate(coord, mobile)
        assert result.x == 1079  # Clamped to right edge


class TestLetterboxMobileToXga:
    """1080x2400 (mobile portrait) -> 1024x768 (XGA): height-limited, bars on left/right."""

    def test_scale(self, mobile, xga):
        m = compute_letterbox_metadata(mobile, xga)
        expected_scale = 768 / 2400
        assert m.scale == pytest.approx(expected_scale, rel=1e-6)

    def test_bars_on_sides_only(self, mobile, xga):
        m = compute_letterbox_metadata(mobile, xga)
        assert m.offset_x > 0  # Black bars left/right
        assert m.offset_y == 0  # No top/bottom bars

    def test_scaled_dimensions(self, mobile, xga):
        m = compute_letterbox_metadata(mobile, xga)
        assert m.scaled_width == round(1080 * (768 / 2400))
        assert m.scaled_height == 768

    def test_image_centered(self, mobile, xga):
        m = compute_letterbox_metadata(mobile, xga)
        assert m.offset_x + m.scaled_width + m.offset_x == xga.width

    def test_center_roundtrip(self, mobile, xga):
        m = compute_letterbox_metadata(mobile, xga)
        original = Coordinate(x=540, y=1200, space=mobile)
        forward = m.forward_transform_coordinate(original)
        back = m.transform_coordinate(forward, mobile)
        assert abs(back.x - original.x) <= 1
        assert abs(back.y - original.y) <= 1

    def test_all_corners_roundtrip(self, mobile, xga):
        m = compute_letterbox_metadata(mobile, xga)
        corners = [(0, 0), (1079, 0), (0, 2399), (1079, 2399)]
        for cx, cy in corners:
            c = Coordinate(x=cx, y=cy, space=mobile)
            fwd = m.forward_transform_coordinate(c)
            back = m.transform_coordinate(fwd, mobile)
            assert abs(back.x - cx) <= 1, f"x roundtrip failed for ({cx}, {cy})"
            assert abs(back.y - cy) <= 1, f"y roundtrip failed for ({cx}, {cy})"

    def test_left_padding_clamps(self, mobile, xga):
        m = compute_letterbox_metadata(mobile, xga)
        coord = Coordinate(x=0, y=384, space=xga)
        result = m.transform_coordinate(coord, mobile)
        assert result.x == 0

    def test_right_padding_clamps(self, mobile, xga):
        m = compute_letterbox_metadata(mobile, xga)
        coord = Coordinate(x=1023, y=384, space=xga)
        result = m.transform_coordinate(coord, mobile)
        assert result.x == 1079


class TestLetterboxPaddingRegionClamping:
    def test_coordinate_in_top_padding_clamps_to_edge(self, hd, square):
        m = compute_letterbox_metadata(hd, square)
        # y=0 is in the top black bar for a wider source letterboxed to square
        coord = Coordinate(x=512, y=0, space=square)
        result = m.transform_coordinate(coord, hd)
        assert result.y == 0  # Clamped to top edge

    def test_coordinate_in_bottom_padding_clamps_to_edge(self, hd, square):
        m = compute_letterbox_metadata(hd, square)
        coord = Coordinate(x=512, y=1023, space=square)
        result = m.transform_coordinate(coord, hd)
        assert result.y == 1079  # Clamped to bottom edge
