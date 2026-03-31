@echo off
cd /d "%~dp0"

echo Setting up EDA Agent...

:: Create virtual environment
python -m venv .venv
call .venv\Scripts\activate

:: Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

:: Create .env if it doesn't exist
if not exist .env (
    echo ANTHROPIC_API_KEY=your-api-key-here > .env
    echo.
    echo Created .env -- add your Anthropic API key to it before running the app.
    echo Get your key at: https://console.anthropic.com
) else (
    echo .env already exists, skipping.
)

:: Create data directory if it doesn't exist
if not exist data mkdir data

echo.
echo Setup complete. Run run.bat to start the app.
