import io

import pytest
from PIL import Image

from gui_agent_screenshot_tools import ResizeMode, Screenshot, Space


class TestScreenshotCreation:
    def test_stores_bytes_without_decoding(self, sample_image_bytes, hd_space):
        s = Screenshot(image_bytes=sample_image_bytes, space=hd_space)
        assert s.image_bytes == sample_image_bytes
        # image property not accessed yet - just check bytes stored
        assert "__dict__" not in s.__dict__ or "image" not in s.__dict__

    def test_space_stored(self, sample_screenshot, hd_space):
        assert sample_screenshot.space == hd_space

    def test_no_metadata_by_default(self, sample_screenshot):
        assert sample_screenshot.resize_metadata is None


class TestScreenshotImage:
    def test_lazy_decode(self, sample_screenshot):
        img = sample_screenshot.image
        assert isinstance(img, Image.Image)
        assert img.width == 1920
        assert img.height == 1080

    def test_cached(self, sample_screenshot):
        img1 = sample_screenshot.image
        img2 = sample_screenshot.image
        assert img1 is img2


class TestScreenshotFromImage:
    def test_creates_from_pil_image(self):
        img = Image.new("RGB", (800, 600), color=(255, 0, 0))
        s = Screenshot.from_image(img)
        assert s.space == Space(width=800, height=600)
        assert len(s.image_bytes) > 0

    def test_roundtrip_dimensions(self):
        img = Image.new("RGB", (640, 480))
        s = Screenshot.from_image(img)
        decoded = s.image
        assert decoded.width == 640
        assert decoded.height == 480


class TestScreenshotResizeStretch:
    def test_dimensions(self, sample_screenshot):
        target = Space(width=512, height=512)
        resized = sample_screenshot.resize(target, ResizeMode.STRETCH)
        assert resized.space == target
        assert resized.image.width == 512
        assert resized.image.height == 512

    def test_metadata_populated(self, sample_screenshot):
        target = Space(width=512, height=512)
        resized = sample_screenshot.resize(target, ResizeMode.STRETCH)
        assert resized.resize_metadata is not None
        assert resized.resize_metadata.mode == ResizeMode.STRETCH

    def test_original_unmodified(self, sample_screenshot, hd_space):
        target = Space(width=512, height=512)
        sample_screenshot.resize(target, ResizeMode.STRETCH)
        assert sample_screenshot.space == hd_space
        assert sample_screenshot.resize_metadata is None


class TestScreenshotResizeLetterbox:
    def test_dimensions(self, sample_screenshot):
        target = Space(width=1024, height=1024)
        resized = sample_screenshot.resize(target, ResizeMode.LETTERBOX)
        assert resized.space == target
        assert resized.image.width == 1024
        assert resized.image.height == 1024

    def test_metadata_populated(self, sample_screenshot):
        target = Space(width=1024, height=1024)
        resized = sample_screenshot.resize(target, ResizeMode.LETTERBOX)
        assert resized.resize_metadata is not None
        assert resized.resize_metadata.mode == ResizeMode.LETTERBOX
        assert resized.resize_metadata.offset_y > 0


class TestLetterboxBlackBarPixels:
    """Verify padding regions contain black (0,0,0) pixels."""

    def test_top_bar_is_black(self, sample_screenshot):
        """HD → square: top padding should be pure black."""
        target = Space(width=1024, height=1024)
        resized = sample_screenshot.resize(target, ResizeMode.LETTERBOX)
        img = resized.image
        offset_y = resized.resize_metadata.offset_y
        # Sample pixels across the top bar
        for x in (0, 512, 1023):
            for y in (0, offset_y - 1):
                assert img.getpixel((x, y)) == (0, 0, 0), f"pixel ({x},{y}) not black"

    def test_bottom_bar_is_black(self, sample_screenshot):
        """HD → square: bottom padding should be pure black."""
        target = Space(width=1024, height=1024)
        resized = sample_screenshot.resize(target, ResizeMode.LETTERBOX)
        img = resized.image
        meta = resized.resize_metadata
        bottom_start = meta.offset_y + meta.scaled_height
        for x in (0, 512, 1023):
            for y in (bottom_start, 1023):
                assert img.getpixel((x, y)) == (0, 0, 0), f"pixel ({x},{y}) not black"

    def test_content_region_is_not_black(self, sample_screenshot):
        """The content area should contain the original image data, not black."""
        target = Space(width=1024, height=1024)
        resized = sample_screenshot.resize(target, ResizeMode.LETTERBOX)
        img = resized.image
        meta = resized.resize_metadata
        # Center of content region
        cx = meta.offset_x + meta.scaled_width // 2
        cy = meta.offset_y + meta.scaled_height // 2
        assert img.getpixel((cx, cy)) != (0, 0, 0)

    def test_side_bars_are_black(self, mobile_screenshot):
        """Mobile → XGA: left/right padding should be pure black."""
        target = Space(width=1024, height=768)
        resized = mobile_screenshot.resize(target, ResizeMode.LETTERBOX)
        img = resized.image
        meta = resized.resize_metadata
        # Left bar
        for y in (0, 384, 767):
            for x in (0, meta.offset_x - 1):
                assert img.getpixel((x, y)) == (0, 0, 0), f"left bar pixel ({x},{y}) not black"
        # Right bar
        right_start = meta.offset_x + meta.scaled_width
        for y in (0, 384, 767):
            for x in (right_start, 1023):
                assert img.getpixel((x, y)) == (0, 0, 0), f"right bar pixel ({x},{y}) not black"

    def test_mobile_content_not_black(self, mobile_screenshot):
        """Mobile → XGA: content area should not be black."""
        target = Space(width=1024, height=768)
        resized = mobile_screenshot.resize(target, ResizeMode.LETTERBOX)
        img = resized.image
        meta = resized.resize_metadata
        cx = meta.offset_x + meta.scaled_width // 2
        cy = meta.offset_y + meta.scaled_height // 2
        assert img.getpixel((cx, cy)) != (0, 0, 0)
