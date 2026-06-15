# ============================================================
#  config.py  —  Edit this file to configure the solver
# ============================================================

DICTIONARY_PATH = '/Users/cheeyl/Documents/Wordscapes_solver/scrabble_words.txt'

# ---- Speed multiplier ----
# Higher = faster clicking. Default: 2.5
SPEED = 2.5

# ---- Shuffle button position (as % of BlueStacks window) ----
SHUFFLE_PCT_X = 0.1
SHUFFLE_PCT_Y = 0.6

# ============================================================
#  click sequence...
#  Each entry is (pct_x, pct_y, delay_after_seconds)
#  These are positions as a percentage of the BlueStacks window
#  so they scale automatically regardless of window size.
#
#  To find the right values:
#    Run cursor_tracker.py and hover over the buttons you want to click.
# ============================================================
NEXT_LEVEL_CLICKS = [
    # (pct_x, pct_y, delay_after_seconds)
    (0.08, 0.05, 1.0),   # Back button [fig 1]
    (0.50, 0.50, 0.5),   # Screen centre [ignore]
    (0.50, 0.72, 0.5),   # Enter level button [fig 2]
    (0.50, 0.72, 0.5),   # piggy bank close button [fig 3]
    (0.50, 0.90, 0.5),   # idk what this is for just keep it here
]
