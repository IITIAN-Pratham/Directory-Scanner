# Directory-Scanner
A simple Python command-line tool that scans a folder and its subfolders for old junk files such as `.tmp`, `.log`, `.zip`, and `.iso`.

It shows the file path, size, age, and total storage occupied by the matching files. The tool is safe by default and does not delete anything unless you explicitly use the `--delete` option and confirm it.

## Features

- Scan a directory and its subdirectories
- Find files older than a specified number of days
- Search for specific file extensions
- Show file size and age
- Show total number of matching files
- Show total storage occupied
- Export reports as CSV or JSON
- Dry-run mode by default
- Optional file deletion with confirmation
- Colored terminal output

## Requirements

- Python 3
- colorama
