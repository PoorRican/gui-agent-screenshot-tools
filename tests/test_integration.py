import io

import pytest
from PIL import Image

from gui_agent_screenshot_tools import (
    BBox,
    Coordinate,
    ResizeMode,
    Screenshot,
    Space,
)


@pytest.fixture
def original_screenshot():
    img = Image.new("RGB", (1920, 1080), color=(100, 150, 200))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return Screenshot(
        image_bytes=buf.getvalue(),
        space=Space(width=1920, height=1080),
    )


class TestStretchPipelineRoundtrip:
    def test_center_roundtrip(self, original_screenshot):
        target = Space(width=1024, height=1024)
        resized = original_screenshot.resize(target, ResizeMode.STRETCH)

        coord = Coordinate(x=512, y=512, space=resized.space)
        result = coord.to_space(original_screenshot.space, resize_metadata=resized.resize_metadata)

        assert result.space == original_screenshot.space
        assert abs(result.x - 960) <= 1
        assert abs(result.y - 540) <= 1

    def test_origin_roundtrip(self, original_screenshot):
        target = Space(width=1024, height=1024)
        resized = original_screenshot.resize(target, ResizeMode.STRETCH)

        coord = Coordinate(x=0, y=0, space=resized.space)
        result = coord.to_space(original_screenshot.space, resize_metadata=resized.resize_metadata)
        assert result.x == 0
        assert result.y == 0


class TestLetterboxPipelineRoundtrip:
    def test_center_roundtrip(self, original_screenshot):
        target = Space(width=1024, height=1024)
        resized = original_screenshot.resize(target, ResizeMode.LETTERBOX)

        coord = Coordinate(x=512, y=512, space=resized.space)
        result = coord.to_space(original_screenshot.space, resize_metadata=resized.resize_metadata)

        assert result.space == original_screenshot.space
        assert abs(result.x - 960) <= 1
        assert abs(result.y - 540) <= 1

    def test_full_roundtrip_from_source(self, original_screenshot):
        """Source coord -> forward -> inverse -> should match original within 1px."""
        target = Space(width=1024, height=1024)
        resized = original_screenshot.resize(target, ResizeMode.LETTERBOX)
        metadata = resized.resize_metadata

        original_coord = Coordinate(x=500, y=300, space=original_screenshot.space)
        forward = metadata.forward_transform_coordinate(original_coord)
        back = metadata.transform_coordinate(forward, original_screenshot.space)

        assert abs(back.x - original_coord.x) <= 1
        assert abs(back.y - original_coord.y) <= 1


class TestAllCornersRoundtrip:
    @pytest.mark.parametrize(
        "x, y",
        [
            (0, 0),
            (1919, 0),
            (0, 1079),
            (1919, 1079),
        ],
    )
    def test_stretch_corners(self, original_screenshot, x, y):
        target = Space(width=1024, height=1024)
        resized = original_screenshot.resize(target, ResizeMode.STRETCH)
        metadata = resized.resize_metadata

        original_coord = Coordinate(x=x, y=y, space=original_screenshot.space)
        forward = metadata.forward_transform_coordinate(original_coord)
        back = metadata.transform_coordinate(forward, original_screenshot.space)

        assert abs(back.x - x) <= 1
        assert abs(back.y - y) <= 1

    @pytest.mark.parametrize(
        "x, y",
        [
            (0, 0),
            (1919, 0),
            (0, 1079),
            (1919, 1079),
        ],
    )
    def test_letterbox_corners(self, original_screenshot, x, y):
        target = Space(width=1024, height=1024)
        resized = original_screenshot.resize(target, ResizeMode.LETTERBOX)
        metadata = resized.resize_metadata

        original_coord = Coordinate(x=x, y=y, space=original_screenshot.space)
        forward = metadata.forward_transform_coordinate(original_coord)
        back = metadata.transform_coordinate(forward, original_screenshot.space)

        assert abs(back.x - x) <= 1
        assert abs(back.y - y) <= 1


class TestMobileToWxgaPipeline:
    """Full pipeline: mobile portrait screenshot → WXGA letterbox → coordinate mapping."""

    def test_letterbox_center_roundtrip(self, mobile_screenshot, wxga_space):
        resized = mobile_screenshot.resize(wxga_space, ResizeMode.LETTERBOX)
        metadata = resized.resize_metadata

        # Bars should be on the sides only
        assert metadata.offset_x > 0
        assert metadata.offset_y == 0

        # Center of mobile screen
        original_coord = Coordinate(x=540, y=1200, space=mobile_screenshot.space)
        forward = metadata.forward_transform_coordinate(original_coord)
        back = metadata.transform_coordinate(forward, mobile_screenshot.space)
        assert abs(back.x - original_coord.x) <= 1
        assert abs(back.y - original_coord.y) <= 1

    def test_letterbox_image_dimensions(self, mobile_screenshot, wxga_space):
        resized = mobile_screenshot.resize(wxga_space, ResizeMode.LETTERBOX)
        assert resized.image.width == 1366
        assert resized.image.height == 768

    @pytest.mark.parametrize(
        "x, y",
        [
            (0, 0),
            (1079, 0),
            (0, 2399),
            (1079, 2399),
        ],
    )
    def test_letterbox_all_corners(self, mobile_screenshot, wxga_space, x, y):
        resized = mobile_screenshot.resize(wxga_space, ResizeMode.LETTERBOX)
        metadata = resized.resize_metadata
        original_coord = Coordinate(x=x, y=y, space=mobile_screenshot.space)
        forward = metadata.forward_transform_coordinate(original_coord)
        back = metadata.transform_coordinate(forward, mobile_screenshot.space)
        assert abs(back.x - x) <= 1
        assert abs(back.y - y) <= 1

    def test_stretch_center_roundtrip(self, mobile_screenshot, wxga_space):
        resized = mobile_screenshot.resize(wxga_space, ResizeMode.STRETCH)
        metadata = resized.resize_metadata
        original_coord = Coordinate(x=540, y=1200, space=mobile_screenshot.space)
        forward = metadata.forward_transform_coordinate(original_coord)
        back = metadata.transform_coordinate(forward, mobile_screenshot.space)
        assert abs(back.x - original_coord.x) <= 1
        assert abs(back.y - original_coord.y) <= 1

    def test_side_padding_clamps(self, mobile_screenshot, wxga_space):
        resized = mobile_screenshot.resize(wxga_space, ResizeMode.LETTERBOX)
        metadata = resized.resize_metadata
        # Click in the left black bar
        coord_in_padding = Coordinate(x=0, y=384, space=resized.space)
        result = coord_in_padding.to_space(mobile_screenshot.space, resize_metadata=metadata)
        assert result.x == 0


class TestMobileToXgaPipeline:
    """Full pipeline: mobile portrait screenshot → XGA letterbox → coordinate mapping."""

    def test_letterbox_bars_on_sides(self, mobile_screenshot, xga_space):
        resized = mobile_screenshot.resize(xga_space, ResizeMode.LETTERBOX)
        metadata = resized.resize_metadata
        assert metadata.offset_x > 0  # Bars on left/right
        assert metadata.offset_y == 0  # Image centered vertically (fills height)

    def test_letterbox_image_dimensions(self, mobile_screenshot, xga_space):
        resized = mobile_screenshot.resize(xga_space, ResizeMode.LETTERBOX)
        assert resized.image.width == 1024
        assert resized.image.height == 768

    def test_letterbox_center_roundtrip(self, mobile_screenshot, xga_space):
        resized = mobile_screenshot.resize(xga_space, ResizeMode.LETTERBOX)
        metadata = resized.resize_metadata
        original_coord = Coordinate(x=540, y=1200, space=mobile_screenshot.space)
        forward = metadata.forward_transform_coordinate(original_coord)
        back = metadata.transform_coordinate(forward, mobile_screenshot.space)
        assert abs(back.x - original_coord.x) <= 1
        assert abs(back.y - original_coord.y) <= 1

    @pytest.mark.parametrize(
        "x, y",
        [
            (0, 0),
            (1079, 0),
            (0, 2399),
            (1079, 2399),
        ],
    )
    def test_letterbox_all_corners(self, mobile_screenshot, xga_space, x, y):
        resized = mobile_screenshot.resize(xga_space, ResizeMode.LETTERBOX)
        metadata = resized.resize_metadata
        original_coord = Coordinate(x=x, y=y, space=mobile_screenshot.space)
        forward = metadata.forward_transform_coordinate(original_coord)
        back = metadata.transform_coordinate(forward, mobile_screenshot.space)
        assert abs(back.x - x) <= 1
        assert abs(back.y - y) <= 1

    def test_side_padding_clamps(self, mobile_screenshot, xga_space):
        resized = mobile_screenshot.resize(xga_space, ResizeMode.LETTERBOX)
        metadata = resized.resize_metadata
        # Click in left black bar
        coord_in_padding = Coordinate(x=0, y=384, space=resized.space)
        result = coord_in_padding.to_space(mobile_screenshot.space, resize_metadata=metadata)
        assert result.x == 0
        # Click in right black bar
        coord_right = Coordinate(x=1023, y=384, space=resized.space)
        result_right = coord_right.to_space(mobile_screenshot.space, resize_metadata=metadata)
        assert result_right.x == 1079


class TestPaddingAreaClamping:
    def test_padding_coord_clamps_to_source_edge(self, original_screenshot):
        """Coordinate in the letterbox padding area should clamp to source boundary."""
        target = Space(width=1024, height=1024)
        resized = original_screenshot.resize(target, ResizeMode.LETTERBOX)
        metadata = resized.resize_metadata

        # Top-left of target (0,0) is in the top padding for HD->square letterbox
        coord_in_padding = Coordinate(x=0, y=0, space=resized.space)
        result = coord_in_padding.to_space(
            original_screenshot.space, resize_metadata=metadata
        )
        assert result.x == 0
        assert result.y == 0  # Clamped to top edge


class TestBboxScreenOffset:
    @pytest.fixture
    def window_screenshot(self):
        img = Image.new("RGB", (1920, 1080), color=(100, 150, 200))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return Screenshot(
            image_bytes=buf.getvalue(),
            space=Space(width=1920, height=1080),
        )

    def test_letterbox_window_to_screen(self, window_screenshot):
        screen = Space(width=2560, height=1440)
        window = BBox(x=50, y=100, width=1920, height=1080, space=screen)

        original = Screenshot(
            image_bytes=window_screenshot.image_bytes,
            space=window.as_space,
        )
        target = Space(width=1024, height=1024)
        resized = original.resize(target, ResizeMode.LETTERBOX)

        coord = Coordinate(x=512, y=512, space=resized.space)
        local_coord = coord.to_space(original.space, resize_metadata=resized.resize_metadata)
        screen_coord = window.absolutize(local_coord)

        assert screen_coord.space == screen
        assert abs(screen_coord.x - 1010) <= 2
        assert abs(screen_coord.y - 640) <= 2

    def test_stretch_window_to_screen(self, window_screenshot):
        screen = Space(width=2560, height=1440)
        window = BBox(x=50, y=100, width=1920, height=1080, space=screen)

        original = Screenshot(
            image_bytes=window_screenshot.image_bytes,
            space=window.as_space,
        )
        target = Space(width=1024, height=1024)
        resized = original.resize(target, ResizeMode.STRETCH)

        coord = Coordinate(x=512, y=512, space=resized.space)
        local_coord = coord.to_space(original.space, resize_metadata=resized.resize_metadata)
        screen_coord = window.absolutize(local_coord)

        assert screen_coord.space == screen
        assert abs(screen_coord.x - 1010) <= 2
        assert abs(screen_coord.y - 640) <= 2

    def test_bbox_does_not_affect_resize(self, window_screenshot):
        """Resize metadata is identical whether bbox is involved or not."""
        screen = Space(width=2560, height=1440)
        window = BBox(x=50, y=100, width=1920, height=1080, space=screen)

        target = Space(width=1024, height=1024)

        # Direct resize from screenshot
        resized_direct = window_screenshot.resize(target, ResizeMode.LETTERBOX)

        # Resize via bbox.as_space
        screenshot_via_bbox = Screenshot(
            image_bytes=window_screenshot.image_bytes,
            space=window.as_space,
        )
        resized_via_bbox = screenshot_via_bbox.resize(target, ResizeMode.LETTERBOX)

        assert resized_direct.resize_metadata == resized_via_bbox.resize_metadata
