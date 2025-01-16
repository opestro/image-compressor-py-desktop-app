@echo off
echo Cleaning previous builds...
rmdir /s /q build
rmdir /s /q dist

echo Installing requirements...
pip install -r requirements.txt

echo Building executable...
pyinstaller image_compressor.spec

echo Build complete!
pause 