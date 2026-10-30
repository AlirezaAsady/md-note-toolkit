@echo off
rem Number menu for the toolkit. Options 6 and 7 hand over to md_menu_tools.py.
rem Keep this file next to the .py files; %~dp0 is "the folder this .cmd is in".
rem No window opens? Python is not on PATH, or has no pythonw - swap it for python.

setlocal
set "DIR=%~dp0"
title md-note-toolkit

:menu
cls
echo  ===========================================
echo    md-note-toolkit
echo  ===========================================
echo    1   Batch        several files, one window
echo    2   Color        markers -^> HTML spans and folds
echo    3   RTL          wrap right-to-left blocks
echo    4   Color + RTL  opens both of the above
echo    5   Reverse      HTML -^> markers again
echo    6   Stylesheet   set the CSS path in md_color_gui.py
echo    7   Shortcut     put this menu on the Windows desktop
echo    0   Exit
echo  ===========================================
echo.

set "N="
set /p N=  Pick a number, then Enter:

if "%N%"=="1" start "" pythonw "%DIR%md_batch_gui.py"
if "%N%"=="2" start "" pythonw "%DIR%md_color_gui.py"
if "%N%"=="3" start "" pythonw "%DIR%md_rtl_advance_gui.py"
if "%N%"=="4" (
    start "" pythonw "%DIR%md_color_gui.py"
    start "" pythonw "%DIR%md_rtl_advance_gui.py"
)
if "%N%"=="5" start "" pythonw "%DIR%md_reverse_gui.py"

rem 6 and 7 print, so they use python, not pythonw, and wait for a key.
if "%N%"=="6" (
    python "%DIR%md_menu_tools.py" set-css
    pause
)
if "%N%"=="7" (
    python "%DIR%md_menu_tools.py" shortcut
    pause
)

if "%N%"=="0" exit /b
goto menu
