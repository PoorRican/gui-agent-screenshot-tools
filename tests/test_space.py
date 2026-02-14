import pytest
from pydantic import ValidationError

from gui_agent_screenshot_tools import Space


class TestSpaceCreation:
    def test_basic_creation(self):
        s = Space(width=1920, height=1080)
        assert s.width == 1920
        assert s.height == 1080

    def test_square(self):
        s = Space(width=1024, height=1024)
        assert s.width == s.height == 1024


class TestSpaceValidation:
    def test_zero_width_rejected(self):
        with pytest.raises(ValidationError):
            Space(width=0, height=100)

    def test_zero_height_rejected(self):
        with pytest.raises(ValidationError):
            Space(width=100, height=0)

    def test_negative_width_rejected(self):
        with pytest.raises(ValidationError):
            Space(width=-1, height=100)

    def test_negative_height_rejected(self):
        with pytest.raises(ValidationError):
            Space(width=100, height=-1)


class TestSpaceImmutability:
    def test_frozen(self):
        s = Space(width=100, height=200)
        with pytest.raises(ValidationError):
            s.width = 50


class TestSpaceAspectRatio:
    def test_landscape(self):
        s = Space(width=1920, height=1080)
        assert s.aspect_ratio == pytest.approx(16 / 9, rel=1e-3)

    def test_square(self):
        s = Space(width=1024, height=1024)
        assert s.aspect_ratio == 1.0

    def test_portrait(self):
        s = Space(width=1080, height=1920)
        assert s.aspect_ratio == pytest.approx(9 / 16, rel=1e-3)


class TestSpaceEquality:
    def test_equal(self):
        assert Space(width=100, height=200) == Space(width=100, height=200)

    def test_not_equal(self):
        assert Space(width=100, height=200) != Space(width=200, height=100)

    def test_hashable(self):
        s1 = Space(width=100, height=200)
        s2 = Space(width=100, height=200)
        assert hash(s1) == hash(s2)
        assert len({s1, s2}) == 1
