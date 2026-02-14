from __future__ import annotations

from dataclasses import dataclass

from .coordinate import Coordinate
from .space import Space
from .types import ResizeMode


@dataclass(frozen=True)
class ResizeMetadata:
    source_space: Space
    target_space: Space
    mode: ResizeMode
    scale: float
    offset_x: int
    offset_y: int
    scaled_width: int
    scaled_height: int

    def transform_coordinate(self, coord: Coordinate, target: Space) -> Coordinate:
        """Inverse transform: target_space coords -> source_space coords, then re-map to target."""
        sw = self.source_space.width - 1
        sh = self.source_space.height - 1

        if self.mode == ResizeMode.STRETCH:
            tw = self.target_space.width - 1
            th = self.target_space.height - 1
            src_x = round(coord.x * sw / tw)
            src_y = round(coord.y * sh / th)
        else:
            cw = self.scaled_width - 1
            ch = self.scaled_height - 1
            src_x = round((coord.x - self.offset_x) * sw / cw) if cw > 0 else 0
            src_y = round((coord.y - self.offset_y) * sh / ch) if ch > 0 else 0

        src_x = min(max(src_x, 0), sw)
        src_y = min(max(src_y, 0), sh)

        if target == self.source_space:
            return Coordinate(x=src_x, y=src_y, space=target)

        # Re-map from source_space to arbitrary target
        new_x = round(src_x * (target.width - 1) / sw)
        new_y = round(src_y * (target.height - 1) / sh)
        new_x = min(max(new_x, 0), target.width - 1)
        new_y = min(max(new_y, 0), target.height - 1)
        return Coordinate(x=new_x, y=new_y, space=target)

    def forward_transform_coordinate(self, coord: Coordinate) -> Coordinate:
        """Forward transform: source_space coords -> target_space coords."""
        sw = self.source_space.width - 1
        sh = self.source_space.height - 1

        if self.mode == ResizeMode.STRETCH:
            tw = self.target_space.width - 1
            th = self.target_space.height - 1
            new_x = round(coord.x * tw / sw)
            new_y = round(coord.y * th / sh)
        else:
            cw = self.scaled_width - 1
            ch = self.scaled_height - 1
            new_x = round(coord.x * cw / sw) + self.offset_x if sw > 0 else self.offset_x
            new_y = round(coord.y * ch / sh) + self.offset_y if sh > 0 else self.offset_y

        new_x = min(max(new_x, 0), self.target_space.width - 1)
        new_y = min(max(new_y, 0), self.target_space.height - 1)
        return Coordinate(x=new_x, y=new_y, space=self.target_space)


def compute_letterbox_metadata(source: Space, target: Space) -> ResizeMetadata:
    scale = min(target.width / source.width, target.height / source.height)
    scaled_w = round(source.width * scale)
    scaled_h = round(source.height * scale)
    offset_x = (target.width - scaled_w) // 2
    offset_y = (target.height - scaled_h) // 2
    return ResizeMetadata(
        source_space=source,
        target_space=target,
        mode=ResizeMode.LETTERBOX,
        scale=scale,
        offset_x=offset_x,
        offset_y=offset_y,
        scaled_width=scaled_w,
        scaled_height=scaled_h,
    )


def compute_stretch_metadata(source: Space, target: Space) -> ResizeMetadata:
    return ResizeMetadata(
        source_space=source,
        target_space=target,
        mode=ResizeMode.STRETCH,
        scale=1.0,
        offset_x=0,
        offset_y=0,
        scaled_width=target.width,
        scaled_height=target.height,
    )
