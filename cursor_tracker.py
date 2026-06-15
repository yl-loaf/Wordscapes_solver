import pyautogui
import time
from Quartz import CGWindowListCopyWindowInfo, kCGWindowListOptionOnScreenOnly, kCGNullWindowID

TARGET_APP = "BlueStacks"

def get_bluestacks_bounds():
    windows = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, kCGNullWindowID)
    for w in windows:
        if w.get('kCGWindowOwnerName', '') == TARGET_APP:
            b = w.get('kCGWindowBounds', {})
            return int(b['X']), int(b['Y']), int(b['Width']), int(b['Height'])
    return None

print(f"Tracking cursor relative to {TARGET_APP} window.")
print("Press Ctrl+C to stop.\n")

last_output = None

while True:
    bounds = get_bluestacks_bounds()

    if bounds is None:
        print(f"\r[ERROR] '{TARGET_APP}' window not found. Is it open?        ", end='', flush=True)
        time.sleep(1)
        continue

    win_left, win_top, win_width, win_height = bounds
    mouse_x, mouse_y = pyautogui.position()

    pct_x = (mouse_x - win_left)  / win_width
    pct_y = (mouse_y - win_top)   / win_height

    output = (
        f"  cursor: ({mouse_x}, {mouse_y})  |  "
        f"window: x={win_left} y={win_top} w={win_width} h={win_height}  |  "
        f"pct_x={pct_x:.4f}  pct_y={pct_y:.4f}"
    )

    if output != last_output:
        print(f"\r{output}   ", end='', flush=True)
        last_output = output

    time.sleep(0.05)
