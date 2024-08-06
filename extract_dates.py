import os
import re
from datetime import datetime
import shutil
import subprocess
import logging
import sys

# Setup logging
log_file = os.path.expanduser('~/takeout-put/extract-error.log')
logging.basicConfig(filename=log_file, level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

# Define patterns to match dates in filenames
patterns = [
    r'Screenshot_(\d{4})(\d{2})(\d{2})-(\d{2})-(\d{2})-(\d{2})',        # Pattern for `Screenshot_YYYYMMDD-HHMMSS`
    r'Screenshot_(\d{4})-(\d{2})-(\d{2})-(\d{2})-(\d{2})-(\d{2})',      # Pattern for `Screenshot_YYYY-MM-DD-HH-MM-SS`
    r'IMG_(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})',                # Pattern for `IMG_YYYYMMDD_HHMMSS`
    r'_(\d{4})(\d{2})(\d{2})_',                                          # Pattern for `_YYYYMMDD_`
    r'-(\d{4})(\d{2})(\d{2})-',                                          # Pattern for `-YYYYMMDD-`
    r'IMG-(\d{4})(\d{2})(\d{2})-WA.*',                                  # Pattern for `IMG-YYYYMMDD-WA*`
]

def extract_date_from_filename(filename):
    for pattern in patterns:
        match = re.search(pattern, filename)
        if match:
            try:
                if len(match.groups()) == 6:
                    date_str = f"{match.group(1)}-{match.group(2)}-{match.group(3)} {match.group(4)}:{match.group(5)}:{match.group(6)}"
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                elif len(match.groups()) == 4:
                    date_str = f"{match.group(1)}-{match.group(2)}-{match.group(3)} {match.group(4)}:00:00"
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                else:
                    continue
                return date_obj
            except ValueError:
                continue
    return None

def update_file_dates(file_path, new_date):
    timestamp = new_date.timestamp()
    try:
        if file_path.lower().endswith('.png'):
            # Change modified date for PNG files
            os.utime(file_path, (timestamp, timestamp))
        else:
            # Change modification date for non-PNG files
            os.utime(file_path, (timestamp, timestamp))
        
        # Update EXIF Date/Time Original using exiftool
        exif_date_str = new_date.strftime('%Y:%m:%d %H:%M:%S')
        subprocess.run([
            'exiftool', 
            f'-DateTimeOriginal={exif_date_str}', 
            file_path
        ], check=True)

    except Exception as e:
        logging.error(f"Error updating file dates for {file_path}: {e}")

def process_files(source_dir, output_dir):
    files = os.listdir(source_dir)
    total_files = len(files)
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    for index, file_name in enumerate(files):
        file_path = os.path.join(source_dir, file_name)
        date_obj = extract_date_from_filename(file_name)
        if date_obj:
            # Create corresponding path in output directory
            output_path = os.path.join(output_dir, file_name)
            if os.path.isfile(file_path):
                # Move file to output directory
                shutil.move(file_path, output_path)
                # Update file dates
                update_file_dates(output_path, date_obj)
        
        # Print progress
        progress = (index + 1) / total_files * 100
        progress_bar_length = 50
        filled_length = int(progress_bar_length * (index + 1) // total_files)
        progress_bar = '█' * filled_length + '-' * (progress_bar_length - filled_length)
        sys.stdout.write(f"\rProgress |{progress_bar}| {progress:.1f}% Complete")
        sys.stdout.flush()

    sys.stdout.write('\n')  # Move to next line after completion

# Define source and output directories
source_dir = os.path.expanduser('~/takeout-put/noexifdata')  # Adjust path as needed
output_dir = os.path.expanduser('~/takeout-put/proc')        # Adjust path as needed

# Process files
process_files(source_dir, output_dir)
