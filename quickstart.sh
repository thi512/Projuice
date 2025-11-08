#!/bin/bash

# Quickstart script for Home AI Camera System

set -e

echo "=========================================="
echo "Home AI Camera System - Quick Start"
echo "=========================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

echo "✓ Python found: $(python3 --version)"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

echo "✓ Virtual environment activated"
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip -q
echo "✓ pip upgraded"
echo ""

# Install requirements
echo "Installing dependencies (this may take a few minutes)..."
pip install -r requirements.txt -q
echo "✓ Dependencies installed"
echo ""

# Copy .env.example to .env if not exists
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ .env file created"
else
    echo "✓ .env file already exists"
fi

echo ""

# Run verification
echo "Running installation verification..."
echo ""
python verify_install.py

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "To start the system:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Run the application: python main.py"
echo "  3. Open browser to: http://localhost:5000"
echo ""
echo "Quick commands:"
echo "  - GUI mode:      python main.py"
echo "  - Headless mode: python main.py --headless"
echo "  - No web UI:     python main.py --no-web"
echo "  - Auto-record:   python main.py --record"
echo ""
echo "Press 'q' to quit, 'r' to record, 's' for snapshot"
echo ""
