import sys
import os
import re
import vobject
import phonenumbers
import argparse

__version__ = "2.0.0"

MAX_FILENAME_LENGTH = 255  # Filesystem-safe limit (most common for NTFS, APFS, ext4)
GROUP_CHAT_PREFIX = "Group chat - "  # Shared prefix for renamed group chat files

# ------------------------------------------------------------
# Utility Functions
# ------------------------------------------------------------

def normalize_phone_number(raw_phone, default_region):
    """Normalize a raw phone number to E.164 format with auto region detection and a default_region for ambiguous or local numbers."""
    if not raw_phone:
        return None

    raw_phone = raw_phone.strip()
    if not raw_phone:
        return None

    try:
        # Attempt parsing without region first — works for numbers in E.164 (+...) or with known prefixes
        phone_number = phonenumbers.parse(raw_phone, None)
    except phonenumbers.NumberParseException:
        # Fallback: try parsing with provided default_region for local-style numbers (e.g., "4151234567")
        try:
            phone_number = phonenumbers.parse(raw_phone, default_region)
        except phonenumbers.NumberParseException:
            return None

    if not phonenumbers.is_valid_number(phone_number):
        return None

    try:
        # Format to E.164
        return phonenumbers.format_number(phone_number, phonenumbers.PhoneNumberFormat.E164)
    except Exception:
        return None


def load_contacts(vcf_file_path, default_region):
    """Load contacts from a VCF file and normalize phone numbers."""
    contacts = {}
    if not os.path.exists(vcf_file_path):
        print(f"Error: VCF file not found at {repr(vcf_file_path)}")
        sys.exit(1)

    with open(vcf_file_path, 'r', encoding='utf-8') as vcf_file:
        try:
            vcf_reader = vobject.readComponents(vcf_file.read())
            for vcard in vcf_reader:
                first_name = ""
                last_name = ""
                if 'n' in vcard.contents:
                    n = vcard.contents['n'][0].value
                    first_name = n.given or ""
                    last_name = n.family or ""
                elif 'fn' in vcard.contents:
                    first_name = vcard.contents['fn'][0].value
                    last_name = ""

                phone_numbers = [tel.value for tel in vcard.contents.get('tel', [])]
                for raw_phone in phone_numbers:
                    normalized_phone = normalize_phone_number(raw_phone, default_region)
                    if not normalized_phone:
                        continue

                    if normalized_phone in contacts:
                        existing = contacts[normalized_phone]
                        print(f"Warning: Duplicate number {normalized_phone} for "
                              f"'{existing}' and '{first_name} {last_name}'. Keeping first.")
                        continue

                    contacts[normalized_phone] = f"{first_name} {last_name}".strip()
        except Exception as e:
            print(f"Error reading VCF file: {e}")
            sys.exit(1)
    return contacts


def sanitize_filename(name):
    """Sanitize filenames for cross-platform compatibility."""
    return re.sub(r'[<>:"/\\|?*]', '_', name)


def truncate_filename(name, max_length):
    """Ensure filename does not exceed the max length."""
    if max_length <= 0 or len(name) <= max_length:
        return name
    return name[:max_length].rstrip() + "…"


def get_first_name(full_name):
    """Extract the first name from a full name."""
    return full_name.split()[0] if full_name else ""


def shorten_filename(path: str, max_length: int = 255) -> str:
    """Shorten a file's name (not its directory) to fit max_length, adding … if truncated."""
    directory, filename = os.path.split(path)
    name, ext = os.path.splitext(filename)
    ellipsis = "…"

    if len(filename) > max_length:
        allowed_base = max_length - len(ext) - len(ellipsis)
        name = name[:allowed_base].rstrip() + ellipsis
        filename = f"{name}{ext}"

    return os.path.join(directory, filename)


# ------------------------------------------------------------
# Processing Logic
# ------------------------------------------------------------

def process_files(imessage_export_path, contacts, phone_pattern, replace_mode):
    """Process all message files once, replacing phone numbers using a single regex pass."""
    for root, _, files in os.walk(imessage_export_path):
        for file in files:
            if not file.endswith(('.html', '.txt')):
                continue

            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                # Handle UTF-16 or legacy encodings gracefully
                try:
                    with open(file_path, 'r', encoding='utf-16') as f:
                        content = f.read()
                except Exception as e:
                    print(f"Error reading file {repr(file_path)}: {e}")
                    continue

            def replace_func(match):
                matched_number = match.group(0)
                contact_name = contacts.get(matched_number)
                if not contact_name:
                    return matched_number
                return contact_name if replace_mode else f"{contact_name} {matched_number}"

            updated_content = re.sub(phone_pattern, replace_func, content)

            if updated_content != content:
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(updated_content)
                except IOError:
                    print(f"Error writing updated content to {repr(file_path)}")


def rename_contact_files(imessage_export_path, contacts, phone_patterns, max_filename_length):
    """Rename exported message files to include contact or group names, preserving emails and ensuring 255-char safe filenames."""

    for filename in os.listdir(imessage_export_path):
        if not filename.endswith(('.html', '.txt')):
            continue

        file_path = os.path.join(imessage_export_path, filename)

        # Extract participants (phone numbers, emails, etc.)
        participants = [
            re.sub(r'\.html$|\.txt$', '', part.strip(), flags=re.IGNORECASE)
            for part in filename.split(',')
        ]
        is_group_chat = len(participants) > 1

        # Find phone numbers
        # Collect all phone number matches across all regex chunks
        match_numbers = []
        for pattern in phone_patterns:
            match_numbers.extend(pattern.findall(filename))

        if not match_numbers and not is_group_chat:
            continue

        new_name = filename

        # Replace phone numbers with contact names
        new_name = replace_filename_numbers(filename, contacts, phone_patterns, is_group_chat)

        # Clean up and sanitize
        new_name = re.sub(r'\s+,', ',', new_name).strip()
        new_name = re.sub(r',\s+', ', ', new_name)
        new_name = sanitize_filename(new_name)

        name_part, ext = os.path.splitext(new_name)
        prefix = GROUP_CHAT_PREFIX if is_group_chat else ""

        # --- Handle truncation ---
        buffer = 5  # buffer for potential suffixes like _2, _3
        available_length = MAX_FILENAME_LENGTH - len(prefix) - len(ext) - buffer
        if len(name_part) > available_length - 1:
            name_part = name_part[:available_length - 1].rstrip() + "…"

        new_name = f"{prefix}{name_part}{ext}"

        # Apply user-defined maxlen (if set)
        if max_filename_length > 0 and len(new_name) > max_filename_length:
            new_name = os.path.basename(shorten_filename(new_name, max_filename_length))

        # Ensure filename uniqueness
        primary_number = match_numbers[0] if match_numbers else None
        new_path = os.path.join(imessage_export_path, new_name)
        new_path = get_available_filename(
            new_path,
            original_path=file_path,
            phone_number=primary_number,
            is_group_chat=is_group_chat
        )

        # Final safety check
        if len(os.path.basename(new_path)) > MAX_FILENAME_LENGTH:
            new_path = shorten_filename(new_path, MAX_FILENAME_LENGTH)

        # Attempt rename
        try:
            os.rename(file_path, new_path)
        except OSError as e:
            print(f"Error renaming {repr(filename)}: {e}")


def replace_filename_numbers(name, contacts, phone_patterns, is_group_chat):
    def repl_func(match):
        num = match.group(0)
        contact_name = contacts.get(num)
        if not contact_name:
            return num
        return sanitize_filename(
            get_first_name(contact_name) if is_group_chat else contact_name
        )

    for pattern in phone_patterns:
        name = re.sub(pattern, repl_func, name)
    return name


def get_available_filename(path, original_path=None, phone_number=None, is_group_chat=False):
    """
    Return a unique filename by appending a phone number or numeric suffix.
    - For group chats: append _2, _3, etc.
    - For single chats: append phone number if conflict.
    Leaves existing file untouched.
    Ensures final filename <= 255 chars.
    """
    directory, filename = os.path.split(path)
    name, ext = os.path.splitext(filename)

    # Early return if file doesn't exist (or it's the original path)
    if not os.path.exists(path) or os.path.abspath(path) == os.path.abspath(original_path):
        return path

    # --- GROUP CHAT LOGIC ---
    if is_group_chat:
        return _generate_numbered_filename(directory, name, ext, MAX_FILENAME_LENGTH)

    # --- SINGLE CHAT LOGIC ---
    if phone_number:
        phone_safe = sanitize_filename(phone_number)
        candidate = os.path.join(directory, f"{name} {phone_safe}{ext}")

        # Truncate base name (keep phone number intact)
        if len(os.path.basename(candidate)) > MAX_FILENAME_LENGTH:
            allowed_base = MAX_FILENAME_LENGTH - len(f" {phone_safe}{ext}") - 1
            trimmed_name = name[:max(0, allowed_base)].rstrip() + "…"
            candidate = os.path.join(directory, f"{trimmed_name} {phone_safe}{ext}")

        # If still exists, fallback to numeric suffix (_2, _3, etc.)
        if os.path.exists(candidate):
            counter = 2
            while True:
                candidate = os.path.join(directory, f"{name}_{counter}{ext}")
                if len(os.path.basename(candidate)) <= MAX_FILENAME_LENGTH and not os.path.exists(candidate):
                    return candidate
                counter += 1

        return candidate

    # --- NO PHONE NUMBER: fallback to _2, _3 ---
    return _generate_numbered_filename(directory, name, ext, MAX_FILENAME_LENGTH)


def _generate_numbered_filename(directory, name, ext, max_length):
    """
    Generate a unique filename by appending _2, _3, etc.
    Ensures it doesn't exceed max_length and doesn't overwrite existing files.
    """
    counter = 2
    while True:
        candidate = os.path.join(directory, f"{name}_{counter}{ext}")
        if len(os.path.basename(candidate)) <= max_length and not os.path.exists(candidate):
            return candidate
        counter += 1


def process_imessage_export(imessage_export_path, contacts, max_filename_length, replace_mode):
    """Main pipeline to replace numbers (optimized single-pass) and rename files."""
    if not os.path.exists(imessage_export_path) or not os.path.isdir(imessage_export_path):
        print(f"Error: Invalid export path: {repr(imessage_export_path)}")
        sys.exit(1)

    detect_already_processed(imessage_export_path)

    # --- Build a single efficient regex pattern for all known phone numbers ---
    escaped_numbers = [re.escape(num) for num in contacts.keys()]
    if not escaped_numbers:
        print("No valid contacts found to process.")
        return

    # Build multiple compiled regex patterns (in chunks) matching all known phone numbers in E.164 format.
    # This avoids memory or performance issues from a single massive regex while maintaining the same matching behavior.
    phone_patterns = list(build_phone_patterns(contacts))

    total_files = sum(
        len([f for f in files if f.endswith(('.html', '.txt'))])
        for _, _, files in os.walk(imessage_export_path)
    )
    processed_files = 0

    print(f"Processing {total_files} files with {len(contacts)} contacts...")

    # --- Replace numbers with names in one pass per file ---
    for root, _, files in os.walk(imessage_export_path):
        for file in files:
            if not file.endswith(('.html', '.txt')):
                continue

            file_path = os.path.join(root, file)

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                print(f"Error reading file {repr(file_path)}: {e}")
                continue

            def replace_func(match):
                matched_number = match.group(0)
                contact_name = contacts.get(matched_number)
                if not contact_name:
                    return matched_number
                return contact_name if replace_mode else f"{contact_name} {matched_number}"

            updated_content = content
            for pattern in phone_patterns:
                updated_content = re.sub(pattern, replace_func, updated_content)

            if updated_content != content:
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(updated_content)
                except IOError:
                    print(f"Error writing file: {repr(file_path)}")

            processed_files += 1
            percent_complete = (processed_files / total_files) * 100
            sys.stdout.write(f"\rProcessed {processed_files}/{total_files} files ({percent_complete:.2f}%)")
            sys.stdout.flush()

    print("\nReplacement complete. Renaming files...")

    rename_contact_files(imessage_export_path, contacts, phone_patterns, max_filename_length)

    print("All processing complete.")


def detect_already_processed(imessage_export_path):
    """Detect if the export folder has already been processed (renamed files)."""
    for filename in os.listdir(imessage_export_path):
        # The prefix GROUP_CHAT_PREFIX is unique to this script's renaming step
        if filename.startswith(GROUP_CHAT_PREFIX):
            print(f"Error: Detected existing renamed file: '{filename}'")
            print("It looks like this export directory has already been processed.\n"
                  "Please use a *fresh* iMessage Exporter export before running this script again.")
            sys.exit(1)


def build_phone_patterns(contacts, chunk_size=500):
    """Yield compiled regex patterns for phone number chunks to avoid massive regex size."""
    escaped_numbers = [re.escape(num) for num in contacts.keys()]
    for i in range(0, len(escaped_numbers), chunk_size):
        chunk = escaped_numbers[i:i + chunk_size]
        yield re.compile(r'(' + '|'.join(chunk) + r')')


def main():
    parser = argparse.ArgumentParser(
        prog="contact_parser.py",
        description=(
            "Processes exported iMessage threads and replaces phone numbers "
            "with matching contact names from a VCF file. "
            "Also renames message files based on contacts or group members."
        ),
        epilog=(
            "Examples:\n"
            "  python contact_parser.py contacts.vcf export_dir\n"
            "  python contact_parser.py contacts.vcf export_dir -r\n"
            "  python contact_parser.py contacts.vcf export_dir -c GB -m 80\n"
        ),
        formatter_class=argparse.RawTextHelpFormatter
    )

    # --- Required positional arguments ---
    parser.add_argument("vcf", help="Path to VCF file containing contacts.")
    parser.add_argument("imessage", help="Path to exported iMessage directory.")

    # --- Optional arguments ---
    parser.add_argument("-c", "--country", default="US", help="Country code for phone normalization (default: US).")
    parser.add_argument("-m", "--maxlen", type=int, default=0, help="Maximum filename length (0 means no limit). Default: 0.")
    parser.add_argument("-r", "--replace", action="store_true", help="Replace phone numbers entirely with contact names.")

    args = parser.parse_args()

    try:
        contacts = load_contacts(args.vcf, args.country)
        process_imessage_export(args.imessage, contacts, args.maxlen, args.replace)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
