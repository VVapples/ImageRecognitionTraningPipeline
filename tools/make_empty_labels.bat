@echo off
echo Generating empty .txt files for YOLO backgrounds...

REM Loop through common image formats
for %%i in (*.jpg *.jpeg *.png) do (
    REM Create an empty text file with the same base name
    type NUL > "%%~ni.txt"
)

echo Done!
pause