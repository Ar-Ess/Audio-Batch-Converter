 @echo off
setlocal
title Build Audio Batch Converter

cd /d "%~dp0"

set "DEV=%~dp0Development"
set "RELEASE=%~dp0Release"
set "OUTPUT=%~dp0Release\Internal"
set "BUILD=%~dp0build"
set "DIST=%~dp0dist"
set "SPEC=%~dp0AudioBatchConverter.spec"

echo ==========================================
echo       Building Audio Batch Converter
echo ==========================================
echo.

if not exist "%DEV%\main.py" (
    echo ERROR: Development\main.py was not found.
    pause
    exit /b 1
)

echo [1/5] Removing previous release...
if exist "%OUTPUT%" rmdir /s /q "%OUTPUT%"
if exist "%OUTPUT%" (
    echo ERROR: Could not remove Release\Internal.
    pause
    exit /b 1
)

echo [2/5] Cleaning previous build artifacts...
if exist "%BUILD%" rmdir /s /q "%BUILD%"
if exist "%DIST%" rmdir /s /q "%DIST%"
if exist "%SPEC%" del /q "%SPEC%"

echo [3/5] Building executable with PyInstaller...
py -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --windowed ^
    --onedir ^
    --name "AudioBatchConverter" ^
    --contents-directory "_internal" ^
    "%DEV%\main.py"

if errorlevel 1 (
    echo.
    echo ERROR: PyInstaller build failed.
    call :cleanup
    pause
    exit /b 1
)

if not exist "%DIST%\AudioBatchConverter\AudioBatchConverter.exe" (
    echo.
    echo ERROR: The generated executable was not found.
    call :cleanup
    pause
    exit /b 1
)

if not exist "%DIST%\AudioBatchConverter\_internal" (
    echo.
    echo ERROR: The generated _internal folder was not found.
    call :cleanup
    pause
    exit /b 1
)

echo [4/5] Creating release folder...
mkdir "%OUTPUT%" 2>nul

if not exist "%OUTPUT%" (
    echo ERROR: Could not create Release\Internal.
    call :cleanup
    pause
    exit /b 1
)

echo Copying executable...
copy /y "%DIST%\AudioBatchConverter\AudioBatchConverter.exe" "%OUTPUT%\AudioBatchConverter.exe" >nul

if errorlevel 1 (
    echo ERROR: Could not copy the executable.
    call :cleanup
    pause
    exit /b 1
)

echo Copying _internal folder...
xcopy "%DIST%\AudioBatchConverter\_internal" "%OUTPUT%\_internal\" /E /I /H /K /Y >nul

if errorlevel 1 (
    echo ERROR: Could not copy the _internal folder.
    call :cleanup
    pause
    exit /b 1
)

if not exist "%OUTPUT%\AudioBatchConverter.exe" (
    echo ERROR: The release executable is missing.
    call :cleanup
    pause
    exit /b 1
)

if not exist "%OUTPUT%\_internal" (
    echo ERROR: The release _internal folder is missing.
    call :cleanup
    pause
    exit /b 1
)

echo [5/5] Removing temporary build artifacts...
call :cleanup

echo.
echo ==========================================
echo       BUILD COMPLETED SUCCESSFULLY
echo ==========================================
echo.
echo Release contents:
echo   Release\Internal\AudioBatchConverter.exe
echo   Release\Internal\_internal
echo.
echo Run Release\StartAudioConverter.bat to test.
echo.
pause
exit /b 0

:cleanup
if exist "%BUILD%" rmdir /s /q "%BUILD%"
if exist "%DIST%" rmdir /s /q "%DIST%"
if exist "%SPEC%" del /q "%SPEC%"
exit /b 0