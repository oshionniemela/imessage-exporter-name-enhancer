@echo off
setlocal enabledelayedexpansion

:: -----------------------------------------
:: Contact Parser Launcher (Windows Version)
:: -----------------------------------------
:: Bootstraps a Python virtual environment
:: and runs contact_parser.py with provided
:: arguments.
::
:: Usage:
::   run_contact_parser.bat {contacts.vcf} {imessage_export_dir} [options]
::
:: Examples:
::   run_contact_parser.bat contacts.vcf export_dir
::   run_contact_parser.bat contacts.vcf export_dir -r
::   run_contact_parser.bat contacts.vcf export_dir -c GB -m 80
:: -----------------------------------------

:: --- Verify argument count ---
if "%~2"=="" (
    echo Usage: %~nx0 {contacts-location} {messages-location} [options]
    echo Example: %~nx0 contacts.vcf export_dir -r -c US -m 80
    exit /b 1
)

:: --- Resolve paths ---
set SCRIPT_DIR=%~dp0
set VENV_DIR=%SCRIPT_DIR%.venv

:: --- Check if Python is available ---
where python >nul 2>nul
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH.
    exit /b 1
)

:: --- Create virtual environment if missing ---
if not exist "%VENV_DIR%" (
    echo Setting up Python virtual environment...
    python -m venv "%VENV_DIR%"
    call "%VENV_DIR%\Scripts\activate.bat"

    echo Installing required packages...
    python -m pip install --quiet --upgrade pip
    python -m pip install --quiet vobject phonenumbers

    call "%VENV_DIR%\Scripts\deactivate.bat"
)

:: --- Activate environment ---
call "%VENV_DIR%\Scripts\activate.bat"

:: --- Verify that the main script exists ---
if not exist "%SCRIPT_DIR%contact_parser.py" (
    echo Error: contact_parser.py not found in %SCRIPT_DIR%
    call "%VENV_DIR%\Scripts\deactivate.bat"
    exit /b 1
)

:: --- Run Python script with all arguments ---
python "%SCRIPT_DIR%contact_parser.py" %*

:: --- Deactivate environment ---
call "%VENV_DIR%\Scripts\deactivate.bat"

endlocal
