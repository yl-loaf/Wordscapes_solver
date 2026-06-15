#!/bin/bash
# Setup script for project dependencies
# Note: Quartz, AppKit, and ctypes are macOS-only (built-in or via pyobjc)

echo "=== Installing pip packages ==="
pip3 install pyautogui pytesseract opencv-python numpy pynput

echo ""
echo "=== Installing macOS-specific packages (pyobjc) ==="
pip3 install pyobjc-framework-Quartz pyobjc-framework-AppKit pyobjc

echo ""
echo "=== Installing Tesseract OCR engine (required by pytesseract) ==="
if command -v brew &> /dev/null; then
    brew install tesseract
else
    echo "Homebrew not found. Please install it first: https://brew.sh"
    echo "Then run: brew install tesseract"
fi

echo ""
echo "=== All done! ==="
echo "Note: ctypes and math are part of Python's standard library — no install needed."
echo "Note: Quartz and AppKit are macOS-only. This project will not run on Windows/Linux."
