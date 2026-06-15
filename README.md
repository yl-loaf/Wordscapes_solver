# Wordscapes Solver

A macOS automation tool that uses screen capture and OCR to read your Wordscapes puzzle in real time, then finds every valid word from your letter rack using a Scrabble dictionary. Just run it and let it solve the board for you.

## Features

- Automatically detects and captures the puzzle from your screen
- Uses OCR (Tesseract) to read the available letters
- Finds all valid word combinations using a Scrabble dictionary
- macOS only (uses Quartz + AppKit for screen/window capture)

## Requirements

- macOS
- Python 3
- Tesseract OCR (installed via Homebrew)

## Installation

**1. Clone the repo**
```bash
git clone https://github.com/yourusername/wordscapes-solver.git
cd wordscapes-solver
```

**2. Install dependencies**
```bash
chmod +x setup.sh && ./setup.sh
```

Or manually:
```bash
pip3 install -r requirements.txt
brew install tesseract
```

## Usage

1. Open Wordscapes on your device (or emulator)
2. Run the solver:
```bash
python3 V2Wordscapes solver_noWifi.py
```
3. The tool will capture your screen, read the letters, and output all valid words.
4. Please allow the script to capture your screen and control your mouse cursor.
5. Press 'q' to exit the script.

## License

MIT
