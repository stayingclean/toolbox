@echo off
cd /d "%~dp0"
uv run --with pytest --with openpyxl pytest tests -v
pause
