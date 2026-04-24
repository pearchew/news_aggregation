#!/bin/bash

# Ensure the script runs in the directory where the script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "==================================================="
echo "Starting Autonomous Tech News & Trends Aggregator..."
echo "==================================================="

# Check if the virtual environment exists
if [ ! -f "venv/bin/activate" ]; then
    echo "[ERROR] Virtual environment not found in the 'venv' folder."
    echo "Please follow the README instructions to set it up first."
    echo "Press any key to exit."
    read -n 1 -s
    exit 1
fi

# Activate the virtual environment
source venv/bin/activate

# Run the main pipeline orchestrator
python3 main.py

# Deactivate the environment
deactivate

echo ""
echo "Pipeline finished. Press any key to exit."
read -n 1 -s