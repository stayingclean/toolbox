@echo off
cd /d "%~dp0"
uv run --with pytest --with openpyxl --with pypdf pytest tests -v
pause
