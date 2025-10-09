#!/bin/bash
set -euo pipefail

# -------------------------------
# Contact Parser Launcher Script
# -------------------------------
# Purpose:
#   Bootstraps a Python environment and runs contact_parser.py
#   with all provided arguments.
#
# Usage:
#   ./run_contact_parser.sh {contacts.vcf} {imessage_export_dir} [options]
#
# Examples:
#   ./run_contact_parser.sh contacts.vcf export_dir
#   ./run_contact_parser.sh contacts.vcf export_dir -r
#   ./run_contact_parser.sh contacts.vcf export_dir -c GB -m 80
# -------------------------------

# --- Ensure at least 2 required arguments ---
if [ "$#" -lt 2 ]; then
  echo "Usage: $0 {contacts-location} {messages-location} [options]"
  echo "Example: $0 contacts.vcf export_dir -r -c US -m 80"
  exit 1
fi

# --- Determine script directory ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/.venv"

# --- Create and activate virtual environment if needed ---
if [ ! -d "$VENV_DIR" ]; then
  echo "Setting up virtual environment at: $VENV_DIR"
  python3 -m venv "$VENV_DIR"
  source "$VENV_DIR/bin/activate"

  echo "Installing required dependencies..."
  pip install --quiet --upgrade pip
  pip install --quiet vobject phonenumbers
else
  source "$VENV_DIR/bin/activate"
fi

# --- Verify that contact_parser.py exists ---
if [ ! -f "${SCRIPT_DIR}/contact_parser.py" ]; then
  echo "Error: contact_parser.py not found in ${SCRIPT_DIR}"
  exit 1
fi

# --- Execute the Python script, forwarding all arguments ---
python3 "${SCRIPT_DIR}/contact_parser.py" "$@"

# --- Deactivate environment cleanly ---
deactivate 2>/dev/null || true
