@echo off
setlocal enabledelayedexpansion

set "RAW_DIR=data\raw"
set "DATA_ZIP=data\data.zip"
if not defined DB_PATH set "DB_PATH=data\store"
if not defined PYTHON set "PYTHON=python"

if "%~1"=="" (
    echo Usage: %~nx0 ^<target^>
    echo Targets: setup import clean test bench
    exit /b 1
)

set "TARGET=%~1"

if /I "%TARGET%"=="setup" goto setup
if /I "%TARGET%"=="import" goto import
if /I "%TARGET%"=="clean" goto clean
if /I "%TARGET%"=="test" goto test
if /I "%TARGET%"=="bench" goto bench

goto usage

:usage
echo Unknown target: %TARGET%
echo Available targets: setup import clean test bench
exit /b 1

:setup
call :ensure_raw_dir
if errorlevel 1 exit /b %errorlevel%
call :expand_zip
exit /b %errorlevel%

:import
call :setup
if errorlevel 1 exit /b %errorlevel%
setlocal
set "PYTHONPATH=src"
"%PYTHON%" -m phone_lookup.cli import --database-path "%DB_PATH%" --npanxx-path "%RAW_DIR%\phoneplatinumwire.csv" --ocn-path "%RAW_DIR%\ocn.csv"
set "exitcode=%errorlevel%"
endlocal & exit /b %exitcode%

:clean
set "exitcode=0"
if exist "%RAW_DIR%\*.csv" del /q "%RAW_DIR%\*.csv" || set "exitcode=%errorlevel%"
if exist "%RAW_DIR%\*.pdf" del /q "%RAW_DIR%\*.pdf" || set "exitcode=%errorlevel%"
if exist "%RAW_DIR%\readme.txt" del /q "%RAW_DIR%\readme.txt" || set "exitcode=%errorlevel%"
exit /b %exitcode%

:test
setlocal
set "PYTHONPATH=src"
"%PYTHON%" -m unittest discover -s tests -t .
set "exitcode=%errorlevel%"
endlocal & exit /b %exitcode%

:bench
setlocal
set "PYTHONPATH=src"
"%PYTHON%" benchmarks/benchmark_store.py
set "exitcode=%errorlevel%"
endlocal & exit /b %exitcode%

:ensure_raw_dir
if not exist "%RAW_DIR%" mkdir "%RAW_DIR%"
exit /b %errorlevel%

:expand_zip
powershell -NoProfile -Command "Expand-Archive -LiteralPath '%DATA_ZIP%' -DestinationPath '%RAW_DIR%' -Force" >nul 2>&1
if errorlevel 1 (
    :: Fallback to tar when PowerShell Expand-Archive is unavailable
    tar -xf "%DATA_ZIP%" -C "%RAW_DIR%" >nul 2>&1
    if errorlevel 1 (
        echo Failed to unpack %DATA_ZIP% into %RAW_DIR%.
        exit /b 1
    )
)
exit /b 0

