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

## License

MIT
