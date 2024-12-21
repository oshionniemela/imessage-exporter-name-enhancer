# imessage-exporter-name-enhancer
*** Enhances [iMessage Exporter](https://github.com/ReagentX/imessage-exporter) by adding contact names to HTML/TXT message files and renaming files to include contact names. ***

[iMessage Exporter](https://github.com/ReagentX/imessage-exporter) is incredibly useful, but I found it lacking one feature: listing the contact's name next to their number (both in the file name and within the HTML messages). To address this, I wrote a script that accomplishes this task, and I believe it could be beneficial for others. Perhaps it could even be integrated into iMessage Exporter itself at some point. I suggest iMessage Exporter could perhaps add a `--contacts {contact-vcf-location}` option. For example:

```bash
$ imessage-exporter -f html -c compatible --contacts {contact-vcf-location} --country-code US
```

For now, since this feature isn't built into iMessage Exporter, to use this script separately follow these steps:

### Steps to Use the Contact Parser Script

#### 1. Export Your Contacts to a vCard (VCF File)

Follow one of the methods below to export your contacts as a vCard ('.vcf' file):

- **Using iCloud.com**:
  1. Sync your iPhone contacts to iCloud.  
  2. Log in to [iCloud Contacts](https://www.icloud.com/contacts).
  3. Select all contacts by pressing `Cmd+A` (Mac) or `Ctrl+A` (Windows).  
  4. Click the **share icon** (top-right corner).
  5. Choose "Export vCard" to download the file to your computer.

- **Using iCloud on a Mac**:  
  1. Sync your iPhone contacts to iCloud.  
  2. Open the **Contacts** app on your Mac.  
  3. Select all contacts by pressing `Cmd+A`.  
  4. Go to `File` -> `Export` -> `Export vCard`.

 - **From the iOS Contacts app**:
  1. Open the Contacts app.
  2. Navigate to Lists (top-left) and tap and hold a specific list.
  3. Choose Export from the options.
  4. Confirm which details you want to include and tap Done.
  5. Select your preferred sharing method such as emailing yourself the vcf file.
  6. Open that email from your computer and you can then download it.

After exporting, you’ll have a `.vcf` file that you can use with this script to enhance your exported iMessage files.

3. **Prepare the Contact Parser Script**
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

4. **Handling International Numbers**
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

---

### Example Without Contact Parser

![Without Contact Parser](images/without-contact-parser.png "HTML Output Without Contact Parser")

---

### Example With Contact Parser

![With Contact Parser](images/with-contact-parser.png "HTML Output With Contact Parser")
