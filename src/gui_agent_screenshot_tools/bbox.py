from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, model_validator

from .coordinate import Coordinate
from .space import Space

if TYPE_CHECKING:
    from .resize import ResizeMetadata


class BBox(BaseModel, frozen=True):
    x: int
    y: int
    width: int
    height: int
    space: Space

    @model_validator(mode="after")
    def _validate(self) -> BBox:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("width and height must be positive")
        if self.x < 0 or self.y < 0:
            raise ValueError("x and y must be non-negative")
        if self.x + self.width > self.space.width:
            raise ValueError(
                f"bbox right edge {self.x + self.width} exceeds space width {self.space.width}"
            )
        if self.y + self.height > self.space.height:
            raise ValueError(
                f"bbox bottom edge {self.y + self.height} exceeds space height {self.space.height}"
            )
        return self

    @property
    def top_left(self) -> Coordinate:
        return Coordinate(x=self.x, y=self.y, space=self.space)

    @property
    def bottom_right(self) -> Coordinate:
        return Coordinate(
            x=self.x + self.width - 1,
            y=self.y + self.height - 1,
            space=self.space,
        )

    @property
    def center(self) -> Coordinate:
        return Coordinate(
            x=self.x + self.width // 2,
            y=self.y + self.height // 2,
            space=self.space,
        )

    @property
    def as_space(self) -> Space:
        return Space(width=self.width, height=self.height)

    def to_space(
        self, target: Space, resize_metadata: ResizeMetadata | None = None
    ) -> BBox:
        top_left = self.top_left.to_space(target, resize_metadata=resize_metadata)
        bottom_right = self.bottom_right.to_space(
            target, resize_metadata=resize_metadata
        )
        new_x = top_left.x
        new_y = top_left.y
        new_width = bottom_right.x - top_left.x + 1
        new_height = bottom_right.y - top_left.y + 1
        return BBox(
            x=new_x, y=new_y, width=new_width, height=new_height, space=target
        )

    def contains(self, coord: Coordinate) -> bool:
        return (
            self.x <= coord.x <= self.x + self.width - 1
            and self.y <= coord.y <= self.y + self.height - 1
        )

    def localize(self, coord: Coordinate) -> Coordinate:
        return Coordinate(
            x=coord.x - self.x, y=coord.y - self.y, space=self.as_space
        )

    def absolutize(self, coord: Coordinate) -> Coordinate:
        return Coordinate(
            x=coord.x + self.x, y=coord.y + self.y, space=self.space
        )
