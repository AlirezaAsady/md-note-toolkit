@echo off
rem =====================================================================
rem  md_menu.cmd - a number menu that opens the toolkit windows.
rem
rem  WHAT THIS FILE DOES, and all it does:
rem    1. prints a menu
rem    2. reads one number from you
rem    3. runs "start pythonw <one of the four .py files next to it>"
rem    4. goes back to step 1
rem
rem  It never creates, edits, copies, moves or deletes a file. It never
rem  touches the network, the registry or any other program. The only
rem  thing it can launch is a Python file sitting in its own folder.
rem  The whole file is below - read it, it is short and nothing is hidden.
rem
rem  SETUP: keep this file in the same folder as the .py files and
rem  double-click it. %~dp0 means "the folder this .cmd is in", so there
rem  is no path of mine baked into it and it works from any drive.
rem
rem  If a window does not open, Python is not on your PATH, or it is
rem  installed without the "pythonw" launcher. Change pythonw to python
rem  on the five lines below to see the error message instead.
rem =====================================================================

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
echo    0   Exit
echo  ===========================================
echo.

rem SET /P only stores the line you type into a variable. It cannot run
rem anything, and an empty answer simply matches none of the checks below.
set "N="
set /p N=  Pick a number, then Enter:

rem "start" launches a program and returns immediately, so the menu stays
rem usable while the window is open. The empty "" is the window title.
if "%N%"=="1" start "" pythonw "%DIR%md_batch_gui.py"
if "%N%"=="2" start "" pythonw "%DIR%md_color_gui.py"
if "%N%"=="3" start "" pythonw "%DIR%md_rtl_advance_gui.py"
if "%N%"=="4" (
    start "" pythonw "%DIR%md_color_gui.py"
    start "" pythonw "%DIR%md_rtl_advance_gui.py"
)
if "%N%"=="5" start "" pythonw "%DIR%md_reverse_gui.py"

rem 0 leaves. Anything else - a letter, a wrong number, just Enter - falls
rem through to here and the menu is drawn again. Nothing is lost.
if "%N%"=="0" exit /b
goto menu
