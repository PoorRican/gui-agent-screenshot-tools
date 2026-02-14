import pytest
from pydantic import ValidationError

from gui_agent_screenshot_tools import Coordinate, Space
from gui_agent_screenshot_tools.resize import (
    compute_letterbox_metadata,
)


@pytest.fixture
def space_100():
    return Space(width=100, height=100)


@pytest.fixture
def space_200():
    return Space(width=200, height=200)


class TestCoordinateCreation:
    def test_origin(self, space_100):
        c = Coordinate(x=0, y=0, space=space_100)
        assert c.x == 0 and c.y == 0

    def test_max_edge(self, space_100):
        c = Coordinate(x=99, y=99, space=space_100)
        assert c.x == 99 and c.y == 99

    def test_mid(self, space_100):
        c = Coordinate(x=50, y=50, space=space_100)
        assert c.x == 50


class TestCoordinateBoundsValidation:
    def test_x_too_large(self, space_100):
        with pytest.raises(ValidationError):
            Coordinate(x=100, y=0, space=space_100)

    def test_y_too_large(self, space_100):
        with pytest.raises(ValidationError):
            Coordinate(x=0, y=100, space=space_100)

    def test_x_negative(self, space_100):
        with pytest.raises(ValidationError):
            Coordinate(x=-1, y=0, space=space_100)

    def test_y_negative(self, space_100):
        with pytest.raises(ValidationError):
            Coordinate(x=0, y=-1, space=space_100)


class TestCoordinateToSpaceRatioScaling:
    def test_center_maps_to_center(self, space_100, space_200):
        c = Coordinate(x=50, y=50, space=space_100)
        mapped = c.to_space(space_200)
        # Pixel-center mapping: 50 * 199/99 ≈ 100.5 → 101
        assert mapped.x == 101
        assert mapped.y == 101
        assert mapped.space == space_200

    def test_origin_stays_origin(self, space_100, space_200):
        c = Coordinate(x=0, y=0, space=space_100)
        mapped = c.to_space(space_200)
        assert mapped.x == 0
        assert mapped.y == 0

    def test_scale_down(self, space_200, space_100):
        c = Coordinate(x=100, y=100, space=space_200)
        mapped = c.to_space(space_100)
        assert mapped.x == 50
        assert mapped.y == 50


class TestCoordinateToSpaceWithMetadata:
    def test_letterbox_center(self):
        source = Space(width=1920, height=1080)
        target = Space(width=1024, height=1024)
        metadata = compute_letterbox_metadata(source, target)
        # Center of target should map near center of source
        center = Coordinate(x=512, y=512, space=target)
        result = center.to_space(source, resize_metadata=metadata)
        assert result.space == source
        assert abs(result.x - 960) <= 1
        assert abs(result.y - 540) <= 1

    def test_letterbox_uses_metadata_not_ratio(self):
        source = Space(width=1920, height=1080)
        target = Space(width=1024, height=1024)
        metadata = compute_letterbox_metadata(source, target)
        coord = Coordinate(x=200, y=300, space=target)
        with_meta = coord.to_space(source, resize_metadata=metadata)
        without_meta = coord.to_space(source)
        # Results should differ since letterbox has offsets
        assert with_meta != without_meta
