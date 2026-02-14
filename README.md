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

### Window offset with BBox

When screenshots are captured from a window (not fullscreen), use `BBox` to represent the window's position on screen and transform coordinates between window-local and screen space:

```python
from gui_agent_screenshot_tools import Space, BBox, Coordinate, Screenshot, ResizeMode

screen = Space(width=2560, height=1440)
window = BBox(x=50, y=100, width=1920, height=1080, space=screen)

# Screenshot is of the window content — its space matches the bbox dimensions
original = Screenshot(image_bytes=..., space=window.as_space)
resized = original.resize(Space(width=1024, height=1024), mode=ResizeMode.LETTERBOX)

# Model clicks at (512, 512) in resized space
coord = Coordinate(x=512, y=512, space=resized.space)
local_coord = coord.to_space(original.space, resize_metadata=resized.resize_metadata)
# local_coord ≈ (960, 540) in 1920x1080

# Convert window-local coordinate to screen coordinate
screen_coord = window.absolutize(local_coord)
# screen_coord ≈ (1010, 640) in 2560x1440

# Other BBox operations
window.contains(screen_coord)             # True — point is inside the window
window.localize(screen_coord)             # Convert screen coord to window-local
window.to_space(Space(width=1280, height=720))  # Scale bbox to a different space
```

## License

MIT
