
@echo off
setlocal

title Audio Batch Converter

set "CONFIG=%~dp0Config"
set "AUDACITY_FILE=%~dp0Config\audacity_path.txt"
set "APP=%~dp0Internal\AudioBatchConverter.exe"

set "AUDACITY="

echo ========================================
echo       Audio Batch Converter
echo ========================================
echo.

if not exist "%CONFIG%" mkdir "%CONFIG%"

if exist "%AUDACITY_FILE%" (
    set /p "AUDACITY="<"%AUDACITY_FILE%"
)

if not defined AUDACITY (
    echo Please select your Audacity 3.7.9 executable.
    echo.

    for /f "usebackq delims=" %%A in (`powershell -NoProfile -STA -Command ^
        "Add-Type -AssemblyName System.Windows.Forms; $d = New-Object System.Windows.Forms.OpenFileDialog; $d.Title = 'Select Audacity 3.7.9'; $d.Filter = 'Audacity executable (Audacity.exe)|Audacity.exe'; if ($d.ShowDialog() -eq 'OK') { $p = $d.FileName; [System.IO.File]::WriteAllText($env:AUDACITY_FILE, $p); Write-Output $p }"`) do (
        set "AUDACITY=%%A"
    )

    if not defined AUDACITY (
        echo No Audacity executable was selected, or its path could not be retrieved.
        echo.
        pause
        exit /b 1
    )
)

if not exist "%AUDACITY%" (
    echo ERROR: The saved Audacity path is invalid:
    echo "%AUDACITY%"
    echo Delete Config\audacity_path.txt and run again to select it.
    echo.
    pause
    exit /b 1
)

if not exist "%APP%" (
    echo ERROR: AudioBatchConverter.exe was not found:
    echo "%APP%"
    echo.
    echo Make sure the PyInstaller dist folder is included.
    echo.
    pause
    exit /b 1
)

echo Checking whether Audacity is already running...

tasklist /FI "IMAGENAME eq Audacity.exe" 2>NUL | find /I "Audacity.exe" >NUL

if not errorlevel 1 (
    powershell -NoProfile -Command "Add-Type -AssemblyName PresentationFramework; [System.Windows.MessageBox]::Show('Please close Audacity before running the Audio Batch Converter.', 'Audio Batch Converter', 'OK', 'Warning') | Out-Null"
    exit /b 1
)

echo.
echo Starting Audacity...
start "" "%AUDACITY%"

echo.
echo Waiting for Audacity scripting pipes...

set "WAITED=0"

:wait_for_audacity_pipes
powershell -NoProfile -Command "$p = Get-ChildItem '\\.\pipe\' -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Name; if (($p -contains 'ToSrvPipe') -and ($p -contains 'FromSrvPipe')) { exit 0 } else { exit 1 }"

if not errorlevel 1 goto audacity_pipes_ready

if %WAITED% GEQ 30 goto audacity_pipe_timeout

timeout /t 1 /nobreak >NUL
set /a WAITED+=1
goto wait_for_audacity_pipes

:audacity_pipe_timeout
echo.
echo ERROR: Audacity scripting pipes did not become available.
echo Check that mod-script-pipe is enabled in Audacity.
echo Restart Audacity and try again.
echo.
pause
exit /b 1

:audacity_pipes_ready
echo Audacity scripting pipes are ready.

echo Waiting for Audacity window...

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$deadline = (Get-Date).AddSeconds(15); " ^
  "$p = $null; " ^
  "while ((Get-Date) -lt $deadline) { " ^
  "  $p = Get-Process Audacity -ErrorAction SilentlyContinue | " ^
  "    Where-Object { $_.MainWindowHandle -ne 0 } | " ^
  "    Select-Object -First 1; " ^
  "  if ($p) { break }; " ^
  "  Start-Sleep -Milliseconds 250 " ^
  "}; " ^
  "if ($p) { " ^
  "  Add-Type -Name Win -Namespace Native -MemberDefinition " ^
  "    '[System.Runtime.InteropServices.DllImport(\"user32.dll\")] public static extern bool ShowWindowAsync(System.IntPtr hWnd, int nCmdShow);'; " ^
  "  [Native.Win]::ShowWindowAsync($p.MainWindowHandle, 6) | Out-Null; " ^
  "  Start-Sleep -Milliseconds 500 " ^
  "} else { Write-Host 'Audacity window was not detected.' }"

echo.
echo Starting Audio Batch Converter...
echo.

start "" "%APP%"

exit /b
