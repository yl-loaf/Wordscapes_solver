import math
import pyautogui
import pytesseract
from Quartz import CGWindowListCopyWindowInfo, kCGWindowListOptionOnScreenOnly, kCGNullWindowID
import Quartz
import os
import cv2
import numpy as np
from itertools import permutations
from collections import Counter
import time
from pynput import keyboard
import subprocess
from random import randint
from AppKit import NSRunningApplication, NSApplicationActivateIgnoringOtherApps
import ctypes
import ctypes.util

from config import DICTIONARY_PATH, SPEED, SHUFFLE_PCT_X, SHUFFLE_PCT_Y, NEXT_LEVEL_CLICKS

Speed = SPEED

def on_press(key):
    try:
        if key.char == 'q':
            print("Stopping...")
            os.kill(os.getpid(), 9)
    except AttributeError:
        pass

listener = keyboard.Listener(on_press=on_press)
listener.start()

TARGET_APP = "BlueStacks"
pyautogui.PAUSE = 0
pyautogui.FAILSAFE = False
windows = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, kCGNullWindowID)

def bring_window_to_front(app_name):
    script = f'tell application "{app_name}" to activate'
    os.system(f"osascript -e '{script}'")

def is_Q(letter_crop):
    white_pixels = cv2.countNonZero(letter_crop)
    total_pixels = letter_crop.shape[0] * letter_crop.shape[1]
    ratio = white_pixels / total_pixels
    return ratio >= 0.40

def is_P(letter_crop):
    h = letter_crop.shape[0]
    top_half = letter_crop[:h//2, :]
    bottom_half = letter_crop[h//2:, :]
    top_white = cv2.countNonZero(top_half)
    bottom_white = cv2.countNonZero(bottom_half)
    return top_white > bottom_white

def apply_circular_mask(img):
    h, w = img.shape[:2]
    mask = np.zeros((h, w), dtype=np.uint8)
    center = (w // 2, h // 2)
    radius = min(w, h) // 2
    cv2.circle(mask, center, radius, 255, -1)
    return cv2.bitwise_and(img, img, mask=mask)

def detect_letter_color_mode(region_x, region_y, region_w, region_h):
    screenshot = pyautogui.screenshot(region=(region_x, region_y, region_w, region_h))
    img = np.array(screenshot)

    h, w = img.shape[:2]
    circle_mask = np.zeros((h, w), dtype=np.uint8)
    cv2.circle(circle_mask, (w // 2, h // 2), min(w, h) // 2, 255, -1)
    pixels = img[circle_mask == 255, :3].astype(np.float32)

    if len(pixels) < 10:
        return {'mode': 'dark',
                'lower': np.array([0, 0, 0]),
                'upper': np.array([180, 255, 85])}

    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
    _, labels, centers = cv2.kmeans(pixels, 2, None, criteria, 5,
                                    cv2.KMEANS_PP_CENTERS)
    centers = centers.astype(np.uint8)

    label_counts = np.bincount(labels.flatten())
    bg_idx = int(np.argmax(label_counts))
    fg_idx = 1 - bg_idx

    bg_color_rgb = centers[bg_idx]
    fg_color_rgb = centers[fg_idx]

    bg_hsv = cv2.cvtColor(bg_color_rgb.reshape(1, 1, 3), cv2.COLOR_RGB2HSV)[0, 0]
    fg_hsv = cv2.cvtColor(fg_color_rgb.reshape(1, 1, 3), cv2.COLOR_RGB2HSV)[0, 0]

    fg_value = int(fg_hsv[2])
    fg_sat   = int(fg_hsv[1])
    fg_hue   = int(fg_hsv[0])

    print(f"  [ColourDetect] BG RGB={bg_color_rgb}  FG RGB={fg_color_rgb}")
    print(f"  [ColourDetect] FG HSV: H={fg_hue} S={fg_sat} V={fg_value}")

    if fg_value < 80:
        return {
            'mode': 'dark',
            'lower': np.array([0, 0, 0]),
            'upper': np.array([180, 255, min(fg_value + 50, 120)])
        }

    if fg_value > 170 and fg_sat < 60:
        return {
            'mode': 'light',
            'lower': np.array([0, 0, max(fg_value - 60, 140)]),
            'upper': np.array([180, 80, 255])
        }

    hue_lo = max(0, fg_hue - 25)
    hue_hi = min(179, fg_hue + 25)
    sat_lo = max(0, fg_sat - 60)
    val_lo = max(0, fg_value - 80)

    if fg_hue < 15 or fg_hue > 165:
        return {
            'mode': 'color_red_wrap',
            'lower':  np.array([0,   sat_lo, val_lo]),
            'upper':  np.array([15,  255,    255]),
            'lower2': np.array([165, sat_lo, val_lo]),
            'upper2': np.array([179, 255,    255]),
        }

    return {
        'mode': 'color',
        'lower': np.array([hue_lo, sat_lo, val_lo]),
        'upper': np.array([hue_hi, 255,    255])
    }


def build_letter_mask(img_rgb, color_info):
    hsv = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV)
    mode = color_info['mode']

    if mode == 'color_red_wrap':
        mask1 = cv2.inRange(hsv, color_info['lower'],  color_info['upper'])
        mask2 = cv2.inRange(hsv, color_info['lower2'], color_info['upper2'])
        mask = cv2.bitwise_or(mask1, mask2)
    else:
        mask = cv2.inRange(hsv, color_info['lower'], color_info['upper'])

    return mask


def get_wordscapes_letters_with_positions(region_x, region_y, region_width, region_height,
                                          color_info=None, save_debug=False):
    home = os.path.expanduser("~")
    screenshot = pyautogui.screenshot(region=(region_x, region_y, region_width, region_height))
    img = np.array(screenshot)

    if color_info is None:
        color_info = {
            'mode': 'dark',
            'lower': np.array([0, 0, 0]),
            'upper': np.array([180, 255, 85])
        }

    mask = build_letter_mask(img, color_info)

    scaled = cv2.resize(mask, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    scaled = apply_circular_mask(scaled)
    contours, _ = cv2.findContours(scaled, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    BASE_CONFIG = '--oem 3 -c tesseract_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ'

    def ocr_single(crop, psm):
        raw = pytesseract.image_to_string(crop, config=f'--psm {psm} {BASE_CONFIG}').strip()
        return ''.join(c for c in raw if c.isalpha()).upper()

    def try_ocr_variants(letter_crop):
        char = ocr_single(letter_crop, 10)
        if len(char) == 1:
            return char

        fallbacks = [
            (cv2.resize(letter_crop, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC), 10),
            (cv2.dilate(letter_crop, np.ones((2, 2), np.uint8), iterations=1), 10),
            (letter_crop, 8),
            (cv2.resize(letter_crop, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC), 8),
        ]

        candidates = [char] if len(char) == 1 else []
        for prepped, psm in fallbacks:
            result = ocr_single(prepped, psm)
            if len(result) == 1:
                candidates.append(result)
            if len(candidates) >= 3:
                break

        if not candidates:
            return None
        winner, count = Counter(candidates).most_common(1)[0]
        return winner if count / max(len(candidates), 1) >= 0.4 else None

    letter_positions = {}

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        area = cv2.contourArea(cnt)

        if area < 1500 or area > 50000:
            continue
        if h < 50:
            continue

        aspect = w / h if h != 0 else 0
        if aspect > 2.5 or aspect < 0.1:
            continue

        img_h, img_w = scaled.shape
        if x <= 2 or y <= 2 or (x + w) >= img_w - 2 or (y + h) >= img_h - 2:
            continue

        padding = 10
        letter_crop = scaled[max(0, y - padding):y + h + padding, max(0, x - padding):x + w + padding]

        if aspect < 0.25:
            char = 'I'
        else:
            char = try_ocr_variants(letter_crop)

            if not char:
                print(f"  [SKIP] Could not confidently detect letter at ({x},{y})")
                continue

            if char == 'O' and w > 70 and h > 70:
                char = 'Q' if is_Q(letter_crop) else 'O'
            if char == 'D':
                char = 'P' if is_P(letter_crop) else 'D'

        if char:
            center_x = region_x + (x + w // 2) // 3
            center_y = region_y + (y + h // 2) // 3

            if char not in letter_positions:
                letter_positions[char] = []
            letter_positions[char].append((center_x, center_y))
            print(f"  Detected '{char}' at screen ({center_x},{center_y})")

    if save_debug:
        debug_img = cv2.cvtColor(scaled, cv2.COLOR_GRAY2BGR)
        img_h, img_w = scaled.shape
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            area = cv2.contourArea(cnt)
            if 500 < area < 50000 and h >= 50:
                aspect = w / h if h != 0 else 0
                if aspect > 2.5 or aspect < 0.1:
                    continue
                if x <= 2 or y <= 2 or (x + w) >= img_w - 2 or (y + h) >= img_h - 2:
                    continue
                cv2.rectangle(debug_img, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.imwrite(f"{home}/Desktop/debug_processed.png", debug_img)
        print("Saved debug_processed.png to Desktop")

    return letter_positions

def find_letter_circle(win_left, win_top, win_width, win_height):
    screenshot = pyautogui.screenshot(region=(win_left, win_top, win_width, win_height))
    img = np.array(screenshot)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    blurred = cv2.GaussianBlur(gray, (9, 9), 2)

    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=100,
        param1=50,
        param2=30,
        minRadius=int(win_height * 0.15),
        maxRadius=int(win_height * 0.35)
    )

    if circles is not None:
        cx, cy, r = np.round(circles[0][0]).astype(int)
        return (win_left + cx - r, win_top + cy - r, r * 2, r * 2)

    return None

def get_letters_with_shuffle_retry(region_x, region_y, region_w, region_h,
                                   win_left, win_top, win_width, win_height,
                                   color_info=None, max_retries=math.inf):
    shuffle_x = int(win_left + win_width * SHUFFLE_PCT_X)
    shuffle_y = int(win_top + win_height * SHUFFLE_PCT_Y)
    pyautogui.leftClick(x=shuffle_x, y=shuffle_y)
    time.sleep(0.8)

    letter_positions = {}
    for attempt in range(max_retries + 1):
        screenshot = pyautogui.screenshot(region=(region_x, region_y, region_w, region_h))
        img = np.array(screenshot)

        if color_info is None:
            color_info = {
                'mode': 'dark',
                'lower': np.array([0, 0, 0]),
                'upper': np.array([180, 255, 85])
            }

        mask = build_letter_mask(img, color_info)
        scaled = cv2.resize(mask, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        scaled = apply_circular_mask(scaled)
        contours, _ = cv2.findContours(scaled, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        img_h, img_w = scaled.shape
        expected_count = 0
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            area = cv2.contourArea(cnt)
            if area < 1500 or area > 50000: continue
            if h < 50: continue
            aspect = w / h if h != 0 else 0
            if aspect > 2.5 or aspect < 0.1: continue
            if x <= 2 or y <= 2 or (x + w) >= img_w - 2 or (y + h) >= img_h - 2: continue
            expected_count += 1

        print(f"  [Attempt {attempt + 1}/{max_retries + 1}] Expecting {expected_count} letters from contours...")

        letter_positions = get_wordscapes_letters_with_positions(
            region_x, region_y, region_w, region_h,
            color_info=color_info,
            save_debug=(attempt == 0)
        )
        letters_found = [char for char, positions in letter_positions.items() for _ in positions]
        total_found = len(letters_found)
        print(f"  Detected {total_found}/{expected_count} letters: {letters_found}")

        if total_found >= expected_count:
            print("  Detection successful!")
            return letter_positions

        if attempt < max_retries:
            print(f"  Missing {expected_count - total_found} letter(s) — clicking shuffle at ({shuffle_x}, {shuffle_y})...")
            pyautogui.leftClick(x=shuffle_x, y=shuffle_y)
            time.sleep(0.8)

    print(f"  [WARN] Could not detect all letters after {max_retries} shuffles. Proceeding with best result.")
    return letter_positions

def load_scrabble_dictionary():
    path = DICTIONARY_PATH
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"\n[ERROR] Dictionary not found at: {path}\n"
            f"Please update DICTIONARY_PATH in config.py\n"
            f"Or download it with:\n"
            f"  curl -o dictionary.txt https://raw.githubusercontent.com/redbo/scrabble/master/dictionary.txt"
        )
    with open(path, 'r') as f:
        return set(word.strip().upper() for word in f)

def solve_wordscapes(letter_positions, dictionary):
    letters = []
    for char, positions in letter_positions.items():
        letters.extend([char] * len(positions))

    valid_words = set()
    for length in range(3, len(letters) + 1):
        for perm in permutations(letters, length):
            word = ''.join(perm)
            if word in dictionary:
                valid_words.add(word)

    return sorted(valid_words, key=len, reverse=True)

def click_word(word, letter_positions):
    word = word.upper()

    usage = {}
    positions = []

    for char in word:
        usage[char] = usage.get(char, 0)
        available = letter_positions.get(char, [])

        if usage[char] >= len(available):
            print(f"  Not enough '{char}' in palette!")
            return

        positions.append(available[usage[char]])
        usage[char] += 1

    print(f"Clicking word: {word}")

    first_x, first_y = positions[0]
    pyautogui.moveTo(first_x, first_y, duration=0.05)
    time.sleep(0.05)
    pyautogui.mouseDown(button='left')
    time.sleep(0.05)

    for idx, (x, y) in enumerate(positions[1:], start=2):
        print(f"  Dragging to letter {idx}: ({x}, {y})")
        if len(word) >= 7:
            pyautogui.moveTo(x, y, duration=0.13/Speed)
        elif len(word) >= 5:
            pyautogui.moveTo(x, y, duration=0.1/Speed)
        else:
            pyautogui.moveTo(x, y, duration=0.07/Speed)
        time.sleep(0.1/Speed)

    pyautogui.mouseUp(button='left')
    print(f"  Done clicking {word}!")

def advance_to_next_level(win_left, win_top, win_width, win_height):
    """Click through the end-of-level screens. Edit NEXT_LEVEL_CLICKS in config.py."""
    print("Advancing to next level...")
    for pct_x, pct_y, delay in NEXT_LEVEL_CLICKS:
        x = int(win_left + win_width  * pct_x)
        y = int(win_top  + win_height * pct_y)
        print(f"  Clicking ({x}, {y})")
        pyautogui.leftClick(x=x, y=y)
        time.sleep(delay)


# -------main------- #
while True:
    win_bounds = None
    windows = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, kCGNullWindowID)
    for w in windows:
        name = w.get('kCGWindowOwnerName', '')
        if name == TARGET_APP:
            win_bounds = w.get('kCGWindowBounds', {})
            break

    if not win_bounds:
        print(f"Window '{TARGET_APP}' not found! Is it open?")
    else:
        win_left   = int(win_bounds['X'])
        win_top    = int(win_bounds['Y'])
        win_width  = int(win_bounds['Width'])
        win_height = int(win_bounds['Height'])

        print(f"Found {TARGET_APP}: {win_bounds}")

        bring_window_to_front(TARGET_APP)

        detected = find_letter_circle(win_left, win_top, win_width, win_height)
        if detected:
            region_x, region_y, region_w, region_h = detected
        else:
            region_x = int(win_left + win_width * 0.185)

        print("  Detecting letter colour mode...")
        color_info = detect_letter_color_mode(region_x, region_y, region_w, region_h)
        print(f"  Colour mode: {color_info['mode']}  lower={color_info['lower']}  upper={color_info['upper']}")

        letter_positions = get_letters_with_shuffle_retry(
            region_x, region_y, region_w, region_h,
            win_left, win_top, win_width, win_height,
            color_info=color_info,
            max_retries=3
        )

        letters = [char for char, positions in letter_positions.items() for _ in positions]
        print("Letters found:", letters)

        dictionary = load_scrabble_dictionary()
        words = solve_wordscapes(letter_positions, dictionary)

        print(f"\nFound {len(words)} words:")
        for word in words:
            print(f"  {len(word)} letters: {word}")

        if words:
            for word in words:
                time.sleep(0.05)
                click_word(word, letter_positions)

        advance_to_next_level(win_left, win_top, win_width, win_height)