from __future__ import annotations

import io
from functools import cached_property

from PIL import Image
from pydantic import BaseModel, ConfigDict

from .resize import (
    ResizeMetadata,
    compute_letterbox_metadata,
    compute_stretch_metadata,
)
from .space import Space
from .types import ResizeMode


class Screenshot(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    image_bytes: bytes
    space: Space
    resize_metadata: ResizeMetadata | None = None

    @cached_property
    def image(self) -> Image.Image:
        return Image.open(io.BytesIO(self.image_bytes))

    @staticmethod
    def from_image(img: Image.Image) -> Screenshot:
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return Screenshot(
            image_bytes=buf.getvalue(),
            space=Space(width=img.width, height=img.height),
        )

    def resize(self, target: Space, mode: ResizeMode) -> Screenshot:
        img = self.image

        if mode == ResizeMode.LETTERBOX:
            metadata = compute_letterbox_metadata(self.space, target)
            scaled = img.resize(
                (metadata.scaled_width, metadata.scaled_height), Image.LANCZOS
            )
            canvas = Image.new("RGB", (target.width, target.height), (0, 0, 0))
            canvas.paste(scaled, (metadata.offset_x, metadata.offset_y))
            result_img = canvas
        else:
            metadata = compute_stretch_metadata(self.space, target)
            result_img = img.resize((target.width, target.height), Image.LANCZOS)

        buf = io.BytesIO()
        result_img.save(buf, format="PNG")
        return Screenshot(
            image_bytes=buf.getvalue(),
            space=target,
            resize_metadata=metadata,
        )
