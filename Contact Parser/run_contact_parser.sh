#!/bin/bash

# Check if the correct number of arguments is provided
if [ "$#" -lt 2 ] || [ "$#" -gt 3 ]; then
  echo "Usage: $0 {contacts-location} {messages-location} [country-code]"
  exit 1
fi

CONTACTS_LOCATION=$1
MESSAGES_LOCATION=$2
COUNTRY_CODE=${3:-US}  # Default to 'US' if the third argument is not provided

# Create a temporary directory for the virtual environment
TEMP_DIR=$(mktemp -d)
cd $TEMP_DIR || exit

# Function to clean up the temporary directory
cleanup() {
    deactivate 2>/dev/null
    cd - || exit
    rm -rf $TEMP_DIR
}

# Register the cleanup function to be called on script exit
trap cleanup EXIT

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install the required packages
pip install vobject phonenumbers

# Navigate back to the directory containing contact_parser.py
cd - || exit

# Run the Python script
python contact_parser.py "$CONTACTS_LOCATION" "$MESSAGES_LOCATION" "$COUNTRY_CODE"
