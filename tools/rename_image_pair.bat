@echo off
setlocal enabledelayedexpansion

:: --- SETTINGS ---
set "namespace=mydata"
set /a count=0
:: ----------------

echo Renaming files to %namespace%_XXXXX...

:: Loop through image files (add/remove extensions as needed)
for %%F in (*.jpg *.jpeg *.png) do (
    
    :: Format the number to 5 digits
    set "padded=00000!count!"
    set "final_num=!padded:~-5!"
    
    :: Define the base old name and new name
    set "oldname=%%~nF"
    set "newname=%namespace%_!final_num!"

    :: Rename the image
    echo Processing: !oldname! -^> !newname!
    ren "%%F" "!newname!%%~xF"

    :: Rename the matching .txt file if it exists
    if exist "!oldname!.txt" (
        ren "!oldname!.txt" "!newname!.txt"
    )

    set /a count+=1
)

echo Done! Processed %count% pairs.
pause