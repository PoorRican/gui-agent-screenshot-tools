import pytest

from gui_agent_screenshot_tools import BBox, Coordinate, ResizeMode, Screenshot, Space


class TestCreationAndValidation:
    def test_basic_creation(self):
        space = Space(width=1920, height=1080)
        bbox = BBox(x=10, y=20, width=100, height=200, space=space)
        assert bbox.x == 10
        assert bbox.y == 20
        assert bbox.width == 100
        assert bbox.height == 200
        assert bbox.space == space

    def test_positive_dimensions_required(self):
        space = Space(width=1920, height=1080)
        with pytest.raises(ValueError):
            BBox(x=0, y=0, width=0, height=100, space=space)
        with pytest.raises(ValueError):
            BBox(x=0, y=0, width=100, height=-1, space=space)

    def test_must_fit_within_space(self):
        space = Space(width=100, height=100)
        with pytest.raises(ValueError):
            BBox(x=50, y=0, width=60, height=10, space=space)
        with pytest.raises(ValueError):
            BBox(x=0, y=90, width=10, height=20, space=space)

    def test_frozen(self):
        space = Space(width=1920, height=1080)
        bbox = BBox(x=0, y=0, width=100, height=100, space=space)
        with pytest.raises(Exception):
            bbox.x = 5


class TestProperties:
    def test_top_left(self):
        space = Space(width=1920, height=1080)
        bbox = BBox(x=50, y=100, width=200, height=300, space=space)
        tl = bbox.top_left
        assert tl.x == 50
        assert tl.y == 100
        assert tl.space == space

    def test_bottom_right(self):
        space = Space(width=1920, height=1080)
        bbox = BBox(x=50, y=100, width=200, height=300, space=space)
        br = bbox.bottom_right
        assert br.x == 249
        assert br.y == 399
        assert br.space == space

    def test_center(self):
        space = Space(width=1920, height=1080)
        bbox = BBox(x=50, y=100, width=200, height=300, space=space)
        c = bbox.center
        assert c.x == 150
        assert c.y == 250
        assert c.space == space

    def test_as_space(self):
        space = Space(width=1920, height=1080)
        bbox = BBox(x=50, y=100, width=200, height=300, space=space)
        s = bbox.as_space
        assert s.width == 200
        assert s.height == 300


class TestToSpace:
    def test_to_space_ratio_scaling(self):
        source = Space(width=1920, height=1080)
        target = Space(width=960, height=540)
        bbox = BBox(x=100, y=200, width=400, height=300, space=source)
        result = bbox.to_space(target)
        assert result.space == target
        assert result.x == 50
        assert result.y == 100
        assert result.width == 200
        assert result.height == 150

    def test_to_space_with_letterbox_metadata(self, sample_screenshot, square_space):
        resized = sample_screenshot.resize(square_space, ResizeMode.LETTERBOX)
        # Create a bbox in the resized space and transform back
        bbox_in_resized = BBox(x=100, y=100, width=200, height=200, space=resized.space)
        result = bbox_in_resized.to_space(
            sample_screenshot.space, resize_metadata=resized.resize_metadata
        )
        assert result.space == sample_screenshot.space

    def test_to_space_with_stretch_metadata(self, sample_screenshot, square_space):
        resized = sample_screenshot.resize(square_space, ResizeMode.STRETCH)
        bbox_in_resized = BBox(x=100, y=100, width=200, height=200, space=resized.space)
        result = bbox_in_resized.to_space(
            sample_screenshot.space, resize_metadata=resized.resize_metadata
        )
        assert result.space == sample_screenshot.space

    def test_to_space_with_offset(self):
        screen = Space(width=2560, height=1440)
        window = BBox(x=50, y=100, width=1920, height=1080, space=screen)
        local_space = window.as_space
        # A bbox in window-local space
        local_bbox = BBox(x=100, y=200, width=400, height=300, space=local_space)
        result = local_bbox.to_space(local_space, offset=window)
        assert result.space == screen
        assert result.x == 150  # 100 + 50
        assert result.y == 300  # 200 + 100
        assert result.width == 400
        assert result.height == 300

    def test_to_space_with_resize_metadata_and_offset(self, sample_screenshot, square_space):
        screen = Space(width=2560, height=1440)
        window = BBox(x=50, y=100, width=1920, height=1080, space=screen)

        resized = sample_screenshot.resize(square_space, ResizeMode.LETTERBOX)
        bbox_in_resized = BBox(x=100, y=100, width=200, height=200, space=resized.space)

        # Two-step: transform then absolutize manually
        intermediate = bbox_in_resized.to_space(
            sample_screenshot.space, resize_metadata=resized.resize_metadata
        )
        manual_x = intermediate.x + window.x
        manual_y = intermediate.y + window.y

        # One-step: transform with offset
        result = bbox_in_resized.to_space(
            sample_screenshot.space,
            resize_metadata=resized.resize_metadata,
            offset=window,
        )
        assert result.space == screen
        assert result.x == manual_x
        assert result.y == manual_y
        assert result.width == intermediate.width
        assert result.height == intermediate.height


class TestContains:
    def test_contains_inside(self):
        space = Space(width=1920, height=1080)
        bbox = BBox(x=50, y=100, width=200, height=300, space=space)
        coord = Coordinate(x=150, y=250, space=space)
        assert bbox.contains(coord)

    def test_contains_corner(self):
        space = Space(width=1920, height=1080)
        bbox = BBox(x=50, y=100, width=200, height=300, space=space)
        coord = Coordinate(x=50, y=100, space=space)
        assert bbox.contains(coord)

    def test_contains_outside(self):
        space = Space(width=1920, height=1080)
        bbox = BBox(x=50, y=100, width=200, height=300, space=space)
        coord = Coordinate(x=300, y=500, space=space)
        assert not bbox.contains(coord)


class TestLocalizeAbsolutize:
    def test_localize_converts_to_local_space(self):
        space = Space(width=1920, height=1080)
        bbox = BBox(x=50, y=100, width=200, height=300, space=space)
        coord = Coordinate(x=100, y=200, space=space)
        local = bbox.localize(coord)
        assert local.x == 50
        assert local.y == 100
        assert local.space == bbox.as_space

    def test_absolutize_converts_to_parent_space(self):
        space = Space(width=1920, height=1080)
        bbox = BBox(x=50, y=100, width=200, height=300, space=space)
        local_coord = Coordinate(x=50, y=100, space=bbox.as_space)
        absolute = bbox.absolutize(local_coord)
        assert absolute.x == 100
        assert absolute.y == 200
        assert absolute.space == space

    def test_localize_absolutize_roundtrip(self):
        space = Space(width=1920, height=1080)
        bbox = BBox(x=50, y=100, width=200, height=300, space=space)
        coord = Coordinate(x=100, y=200, space=space)
        local = bbox.localize(coord)
        back = bbox.absolutize(local)
        assert back.x == coord.x
        assert back.y == coord.y
        assert back.space == coord.space
