import os
import csv
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path

from colorama import init, Fore, Style

init(autoreset=True)

print(Fore.CYAN+Style.BRIGHT + "Usage: python3 directory_scanner.py ~/<directory> [--days N] [--ext EXT ...] [--delete]")

DEFAULT_EXTENSIONS = [".tmp", ".log", ".zip", ".iso"]


def format_size(size):
    """Convert bytes into a readable size."""

    if size >= 1024 ** 3:
        return f"{size / (1024 ** 3):.2f} GB"

    elif size >= 1024 ** 2:
        return f"{size / (1024 ** 2):.2f} MB"

    elif size >= 1024:
        return f"{size / 1024:.2f} KB"

    else:
        return f"{size} B"


def scan_directory(directory, days, extensions):
    """Find files matching extension and age criteria."""

    cutoff_time = datetime.now() - timedelta(days=days)

    found_files = []
    errors = []

    def handle_error(error):
        errors.append(f"Could not open folder: {error.filename}")

    for root, dirs, files in os.walk(directory, onerror=handle_error):

        for filename in files:

            file_path = Path(root) / filename

            try:

                if file_path.is_symlink():
                    continue

                if file_path.suffix.lower() not in extensions:
                    continue

                info = file_path.stat()

                modified_time = datetime.fromtimestamp(info.st_mtime)

                if modified_time > cutoff_time:
                    continue

                age = (datetime.now() - modified_time).days

                found_files.append({
                    "path": file_path,
                    "size": info.st_size,
                    "age": age
                })

            except (PermissionError, FileNotFoundError, OSError):
                errors.append(f"Could not access: {file_path}")

    return found_files, errors


def print_report(files):
    """Print a formatted report and return the total size."""

    print(Fore.CYAN + Style.BRIGHT + "\n========== DIRECTORY SCANNER ==========\n")

    files.sort(key=lambda x: x["size"], reverse=True)

    total_size = sum(file["size"] for file in files)

    for number, file in enumerate(files, start=1):

        print(f"{number}. {Fore.WHITE}{Style.BRIGHT}{file['path']}")
        print(f"   Size: {Fore.YELLOW}{format_size(file['size'])}")
        print(f"   Age: {Fore.MAGENTA}{file['age']} days")
        print()

    print(Fore.CYAN + "---------------------------------------")
    print(f"Total files: {Fore.GREEN}{len(files)}")
    print(f"Total space: {Fore.GREEN}{Style.BRIGHT}{format_size(total_size)}")
    print(Fore.CYAN + "---------------------------------------")

    return total_size


def export_report(files, export_path):
    """Save the report as a CSV or JSON file (decided by the file name)."""

    rows = []

    for file in files:
        rows.append({
            "path": str(file["path"]),
            "size_bytes": file["size"],
            "size": format_size(file["size"]),
            "age_days": file["age"]
        })

    export_path = Path(export_path).expanduser()
    extension = export_path.suffix.lower()

    try:

        if extension == ".json":

            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(rows, f, indent=4)

        elif extension == ".csv":

            with open(export_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f, fieldnames=["path", "size_bytes", "size", "age_days"]
                )
                writer.writeheader()
                writer.writerows(rows)

        else:
            print(Fore.RED + "Error: export file must end with .csv or .json")
            return

        print(Fore.GREEN + f"\nReport exported to: {export_path}")

    except OSError as error:
        print(Fore.RED + f"Could not write export file: {error}")


def main():

    parser = argparse.ArgumentParser(
        description="Safely scan a directory for old junk files.",
        epilog="Example: python3 directory_scanner.py ~/Downloads --days 60 --ext .zip .iso --export report.csv"
    )

    parser.add_argument(
        "directory",
        help="Directory to scan"
    )

    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Find files older than this many days (default: 30)"
    )

    parser.add_argument(
        "--ext",
        nargs="+",
        default=DEFAULT_EXTENSIONS,
        help="File extensions to look for (default: .tmp .log .zip .iso)"
    )

    parser.add_argument(
        "--export",
        metavar="FILE",
        help="Save the report to a .csv or .json file"
    )

    parser.add_argument(
        "--delete",
        action="store_true",
        help="Allow deletion (still asks for confirmation first)"
    )

    args = parser.parse_args()

    directory = Path(args.directory).expanduser()

    if not directory.exists():
        print(Fore.RED + "Error: Directory does not exist.")
        return

    if not directory.is_dir():
        print(Fore.RED + "Error: Path is not a directory.")
        return

    if args.days < 0:
        print(Fore.RED + "Error: --days cannot be negative.")
        return

    extensions = set()

    for ext in args.ext:

        ext = ext.lower()

        if not ext.startswith("."):
            ext = "." + ext

        extensions.add(ext)

    print(Fore.CYAN + "Scanning...")
    print(f"Directory: {Fore.WHITE}{directory}")
    print(f"Older than: {Fore.WHITE}{args.days} days")
    print(f"Extensions: {Fore.WHITE}{', '.join(sorted(extensions))}")

    files, errors = scan_directory(
        directory,
        args.days,
        extensions
    )

    if not files:
        print(Fore.GREEN + "\nNo matching files found.")
    else:
        total_size = print_report(files)

    if errors:
        print(Fore.YELLOW + f"\n{len(errors)} problem(s) while scanning:")
        for message in errors:
            print(Fore.YELLOW + f"  - {message}")

    if not files:
        return

    if args.export:
        export_report(files, args.export)

    if not args.delete:
        print(Fore.GREEN + "\nDry-run mode: NO files were deleted.")
        print(Fore.YELLOW + "Run again with --delete if you really want to remove them.")
        return

    answer = input(
        Fore.RED + Style.BRIGHT +
        f"\nDo you want to delete these [{len(files)}] files "
        f"to free up [{format_size(total_size)}]? (yes/no): "
    )

    if answer.strip().lower() != "yes":
        print(Fore.GREEN + "\nNothing was deleted.")
        return

    deleted = 0

    for file in files:

        try:
            file["path"].unlink()
            deleted += 1
            print(Fore.GREEN + f"Deleted: {file['path']}")

        except (PermissionError, FileNotFoundError, OSError) as error:
            print(Fore.RED + f"Could not delete {file['path']}: {error}")

    print(Fore.GREEN + Style.BRIGHT + f"\nDeleted {deleted} files.")


if __name__ == "__main__":
    main()
