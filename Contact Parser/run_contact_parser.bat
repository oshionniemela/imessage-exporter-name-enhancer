@echo off
:: Check if the correct number of arguments is provided
if "%~2"=="" (
    echo Usage: %~nx0 {contacts-location} {messages-location} [country-code]
    exit /b 1
)

set CONTACTS_LOCATION=%1
set MESSAGES_LOCATION=%2
set COUNTRY_CODE=%3

:: Default country code to US if not provided
if "%COUNTRY_CODE%"=="" (
    set COUNTRY_CODE=US
)

:: Create a temporary directory for the virtual environment
set TEMP_DIR=%TEMP%\contact_parser_venv
if exist "%TEMP_DIR%" rmdir /s /q "%TEMP_DIR%"
mkdir "%TEMP_DIR%"
cd /d "%TEMP_DIR%"

:: Create the virtual environment
python -m venv venv

:: Activate the virtual environment
call venv\Scripts\activate.bat

:: Install the required packages
pip install vobject phonenumbers

:: Navigate back to the directory containing contact_parser.py
cd /d "%~dp0"

:: Run the Python script
python contact_parser.py "%CONTACTS_LOCATION%" "%MESSAGES_LOCATION%" "%COUNTRY_CODE%"

:: Deactivate and clean up
call venv\Scripts\deactivate.bat
rmdir /s /q "%TEMP_DIR%"
