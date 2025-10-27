#!/bin/bash

# Check for Python
if ! command -v python3 &> /dev/null
then
    echo "Python 3 is not installed. Please install Python 3.8+."
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
pip3 install -r requirements.txt

echo "Setup complete."