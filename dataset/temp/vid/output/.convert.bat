@echo off
setlocal enabledelayedexpansion

:: --- CONFIGURATION ---
set "PREFIX=phone_camera"
set "START_NUM=1"
:: ---------------------

set /a count=%START_NUM%

echo Renaming all images sequentially...
echo Pattern: %PREFIX%_00001.ext

:: Loop through all common image files
for %%f in (*.jpg *.jpeg *.png *.heic *.bmp *.tif) do (
    
    :: 1. Generate the 5-digit zero-padded number
    set /a num=100000+count
    set "suffix=!num:~-5!"
    
    :: 2. Build the new filename (Preserving original extension)
    set "newname=%PREFIX%_!suffix!%%~xf"
    
    :: 3. Rename the file
    ren "%%f" "!newname!"
    echo [!suffix!] %%f -^> !newname!

    :: 4. Increment counter
    set /a count+=1
)

echo.
echo All done.
pause