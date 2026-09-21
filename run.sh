#!/usr/bin/env bash
# QueryMind setup and execution script for Linux / macOS

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

VENV_DIR=".venv"

echo "=================================================="
echo "      QueryMind — Query Optimizer Setup & Run     "
echo "=================================================="

# 1. Virtual Environment Setup
if [ ! -d "$VENV_DIR" ]; then
    echo "[+] Creating Python virtual environment in $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
fi

echo "[+] Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# 2. Dependency Installation
echo "[+] Checking and installing dependencies from requirements.txt..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

# 3. Argument Parsing
TRAIN_FLAG=""
EPOCH_ARG=""
TEST_FLAG=""
QUERY_ARG=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --train)
            TRAIN_FLAG="--train"
            shift
            ;;
        --epoch|--epochs)
            EPOCH_ARG="--epochs $2"
            shift 2
            ;;
        --test)
            TEST_FLAG="--test"
            shift
            ;;
        --query)
            QUERY_ARG="--query \"$2\""
            shift 2
            ;;
        *)
            echo "Unknown argument: $1"
            shift
            ;;
    esac
done

# 4. Run CLI
echo "[+] Executing QueryMind..."
echo "--------------------------------------------------"
python cli.py $TRAIN_FLAG $EPOCH_ARG $TEST_FLAG $QUERY_ARG
echo "=================================================="
