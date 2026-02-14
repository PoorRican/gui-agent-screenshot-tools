# gui-agent-screenshot-tools

Tools for coordinate mapping and screenshot transformations across screen resolutions for GUI agents.

When a GUI agent takes a screenshot at one resolution and needs to map coordinates to a different resolution (e.g. the actual display), this library handles the math — including letterboxing and stretch transforms.

## Installation

```bash
pip install gui-agent-screenshot-tools
```

## Usage

```python
from gui_agent_screenshot_tools import Space, Coordinate, Screenshot, ResizeMode

# Define source and target screen spaces
source = Space(width=1920, height=1080)
target = Space(width=1280, height=720)

# Map a coordinate between spaces
coord = Coordinate(x=960, y=540, space=source)
mapped = coord.to_space(target)
print(mapped.x, mapped.y)  # 640, 360

# Resize a screenshot with letterboxing
from PIL import Image

img = Image.new("RGB", (1920, 1080), color=(255, 0, 0))
screenshot = Screenshot.from_image(img)
resized = screenshot.resize(target, ResizeMode.LETTERBOX)

# Map coordinates back through the resize metadata
coord_in_resized = Coordinate(x=640, y=360, space=target)
original = coord_in_resized.to_space(source, resized.resize_metadata)
```

### Remapping a BBox across spaces

When screenshots are captured from a window, use `BBox` to represent the window's position on screen. A model may detect a bounding box in resized screenshot space — use `BBox.to_space` with `offset` to remap it all the way back to physical screen coordinates in one step:

```python
from gui_agent_screenshot_tools import Space, BBox, Screenshot, ResizeMode

screen = Space(width=2560, height=1440)
window = BBox(x=50, y=100, width=1920, height=1080, space=screen)

# Screenshot is of the window content
original = Screenshot(image_bytes=..., space=window.as_space)
resized = original.resize(Space(width=1024, height=1024), mode=ResizeMode.LETTERBOX)

# Model detects a UI element in resized space
detection = BBox(x=100, y=200, width=300, height=150, space=resized.space)

# Remap to screen: undo resize + apply window offset in one call
screen_bbox = detection.to_space(
    original.space,
    resize_metadata=resized.resize_metadata,
    offset=window,
)
# screen_bbox is now in 2560x1440 screen coordinates

screen_bbox.center      # Coordinate at the center of the remapped box
screen_bbox.top_left    # Top-left corner as a Coordinate
screen_bbox.as_space    # The bbox dimensions as a Space
```

## License

MIT
