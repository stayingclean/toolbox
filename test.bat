@echo off
cd /d "%~dp0"
uv run --with pytest --with openpyxl --with pypdf --with pillow pytest tests -v
pause
