import sys
import os
import re
import vobject
import phonenumbers

def normalize_phone_number(raw_phone, region):
    try:
        # Parse phone number with the given region
        phone_number = phonenumbers.parse(raw_phone, region)
        return phonenumbers.format_number(phone_number, phonenumbers.PhoneNumberFormat.E164)
    except phonenumbers.NumberParseException:
        return None

def load_contacts(vcf_file_path, region):
    contacts = {}
    with open(vcf_file_path, 'r') as vcf_file:
        vcf_reader = vobject.readComponents(vcf_file.read())

        for vcard in vcf_reader:
            first_name = vcard.contents.get('n', [None])[0].value.given if 'n' in vcard.contents else ""
            last_name = vcard.contents.get('n', [None])[0].value.family if 'n' in vcard.contents else ""
            phone_numbers = [tel.value for tel in vcard.contents.get('tel', [])]

            for raw_phone in phone_numbers:
                normalized_phone = normalize_phone_number(raw_phone, region)
                if normalized_phone:
                    contacts[normalized_phone] = f"{first_name} {last_name}".strip()
    return contacts

def process_files(imessage_export_path, phone_number, name, phone_pattern):
    for root, dirs, files in os.walk(imessage_export_path):
        for file in files:
            if file.endswith(('.html', '.txt')):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    updated_content = re.sub(phone_pattern, lambda m: f"{name} {m.group()}" if m.group() == phone_number else m.group(), content)
                    if updated_content != content:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(updated_content)
                except IOError:
                    print(f"Error processing file: {file_path}")

def sanitize_filename(name):
    return re.sub(r'[<>:"/\\|?*]', '_', name)

def rename_single_contact_files(imessage_export_path, contacts, phone_pattern):
    for filename in os.listdir(imessage_export_path):
        if filename.endswith(('.html', '.txt')):
            pattern = phone_pattern.pattern + r'\.(html|txt)'
            if re.fullmatch(pattern, filename):
                match = re.search(phone_pattern, filename)
                if match and match.group() in contacts:
                    sanitized_name = sanitize_filename(contacts[match.group()])
                    new_filename = f"{sanitized_name} {match.group()}{os.path.splitext(filename)[1]}"
                    old_filepath = os.path.join(imessage_export_path, filename)
                    new_filepath = os.path.join(imessage_export_path, new_filename)
                    if os.path.exists(old_filepath):
                        os.rename(old_filepath, new_filepath)
                    else:
                        print(f"File not found: {old_filepath}")

def process_imessage_export(imessage_export_path, contacts):
    phone_pattern = re.compile(r'\+\d{1,3}\d{4,14}')  # Updated regex to match international phone numbers
    total_contacts = len(contacts)
    processed = 0

    for phone_number, name in contacts.items():
        process_files(imessage_export_path, phone_number, name, phone_pattern)
        processed += 1
        percent_complete = (processed / total_contacts) * 100
        sys.stdout.write(f"\rProcessed {processed} of {total_contacts} contacts ({percent_complete:.2f}%)")
        sys.stdout.flush()

    rename_single_contact_files(imessage_export_path, contacts, phone_pattern)
    print("\nProcessing complete.")

def main():
    if len(sys.argv) < 3:
        print("Usage: python script.py [path_to_vcf_file] [path_to_imessage_export_directory] [country_code]")
        sys.exit(1)

    vcf_file_path = sys.argv[1]
    imessage_export_path = sys.argv[2]
    region = sys.argv[3] if len(sys.argv) > 3 else 'US'

    contacts = load_contacts(vcf_file_path, region)
    process_imessage_export(imessage_export_path, contacts)

if __name__ == "__main__":
    main()
