# imessage-exporter-name-enhancer
*** Enhances [iMessage Exporter](https://github.com/ReagentX/imessage-exporter) by adding contact names to HTML/TXT message files and renaming files to include contact names. ***

[iMessage Exporter](https://github.com/ReagentX/imessage-exporter) is incredibly useful, but I found it lacking one feature: listing the contact's name next to their number (both in the file name and within the HTML messages). To address this, I wrote a script that accomplishes this task, and I believe it could be beneficial for others. Perhaps it could even be integrated into iMessage Exporter itself at some point. I suggest iMessage Exporter could perhaps add a `--contacts {contact-vcf-location}` option. For example:

```bash
$ imessage-exporter -f html -c compatible --contacts {contact-vcf-location} --country-code US
```

For now, since this feature isn't built into iMessage Exporter, to use this script separately follow these steps:

#### Steps to Use the Contact Parser Script

1. **Export Your Contacts to a VCF File**
   - On your Mac, open the Contacts app.
   - Select all contacts.
   - Navigate to `File` -> `Export` -> `Export vCard`.

2. **Prepare the Contact Parser Script**
   - Open the terminal and navigate to the `Contact Parser` directory.
   - Make the script executable with:
     ```bash
     chmod +x run_contact_parser.sh
     ```
   - Run the script with:
     ```bash
     ./run_contact_parser.sh {contacts-vcf-location} {imessages-directory}
     ```
   - This will update every HTML message file in the directory with the contact's name (if found in the VCF file).

3. **Handling International Numbers**
   - By default, the script assumes US numbers. If you are in another country, you can pass a third parameter with your 2-letter country code:
     ```bash
     ./run_contact_parser.sh {contacts-vcf-location} {imessages-directory} {country-code}
     ```
   - For example:
     ```bash
     ./run_contact_parser.sh contacts.vcf imessages-directory UK
     ```

#### Important Notes

- **Backup Your Data**: Before running the script, please ensure you have backed up your exported HTML messages.
- **Tested on Mac**: This script has only been tested on a Mac environment.
