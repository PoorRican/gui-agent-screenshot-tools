from pydantic import BaseModel, model_validator


class Space(BaseModel, frozen=True):
    width: int
    height: int

    @model_validator(mode="after")
    def _validate_positive(self) -> "Space":
        if self.width <= 0 or self.height <= 0:
            raise ValueError("width and height must be positive")
        return self

    @property
    def aspect_ratio(self) -> float:
        return self.width / self.height
