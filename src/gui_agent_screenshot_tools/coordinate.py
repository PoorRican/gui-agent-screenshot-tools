from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, model_validator

from .space import Space

if TYPE_CHECKING:
    from .resize import ResizeMetadata


class Coordinate(BaseModel, frozen=True):
    x: int
    y: int
    space: Space

    @model_validator(mode="after")
    def _validate_bounds(self) -> Coordinate:
        if not (0 <= self.x < self.space.width):
            raise ValueError(f"x={self.x} out of bounds for width={self.space.width}")
        if not (0 <= self.y < self.space.height):
            raise ValueError(f"y={self.y} out of bounds for height={self.space.height}")
        return self

    def to_space(
        self, target: Space, resize_metadata: ResizeMetadata | None = None
    ) -> Coordinate:
        if resize_metadata is not None:
            return resize_metadata.transform_coordinate(self, target)
        # Pixel-center ratio scaling (stretch / generic)
        new_x = round(self.x * (target.width - 1) / (self.space.width - 1))
        new_y = round(self.y * (target.height - 1) / (self.space.height - 1))
        new_x = min(max(new_x, 0), target.width - 1)
        new_y = min(max(new_y, 0), target.height - 1)
        return Coordinate(x=new_x, y=new_y, space=target)
