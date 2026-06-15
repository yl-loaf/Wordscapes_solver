# Wordscapes Solver

A macOS automation tool that uses screen capture and OCR to read your Wordscapes puzzle in real time, then finds every valid word from your letter palette using a Scrabble dictionary. Just run it and let it solve the board for you.

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

## Config  
1. Open config file and edit the window %.
2. If you have trouble finding the window %, run
```bash
python3 cursor_tracker.py
```
Back button position [fig. 1]:  

<img width="146" height="316" alt="IMG_2758" src="https://github.com/user-attachments/assets/e13c8156-6be5-43b2-aee6-4267f702735f" />

Enter level button [fig 2]    
<img width="146" height="232" alt="IMG_2759" src="https://github.com/user-attachments/assets/428c9eb1-d3b2-428b-9c58-90213f305b8f" />
Piggy bank close button [fig 3]  
<img width="131" height="258" alt="Screenshot 2026-06-15 at 10 32 59 AM" src="https://github.com/user-attachments/assets/f21b8949-0261-4235-8a85-b99b3bea5f41" />

## License

MIT
