#!/bin/bash
cd "$(dirname "$0")"

echo "Setting up EDA Agent..."

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "ANTHROPIC_API_KEY=your-api-key-here" > .env
    echo ""
    echo "Created .env — add your Anthropic API key to it before running the app."
    echo "Get your key at: https://console.anthropic.com"
else
    echo ".env already exists, skipping."
fi

# Create data directory if it doesn't exist
mkdir -p data

echo ""
echo "Setup complete. Run ./run.sh to start the app."
